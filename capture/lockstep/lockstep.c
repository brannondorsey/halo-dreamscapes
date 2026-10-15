/*
 * lockstep.c - LD_PRELOAD shim that films a slow-rendering game at a perfectly even frame rate.
 *
 * Halo runs on software GL at ~6-13 fps, so a real-time x11grab at 30 fps holds each rendered frame
 * for 2-7 frames, unevenly: judder. While a capture is armed this shim fakes the game's clock so it
 * advances exactly 1/FPS per presented frame, and writes each presented frame (raw rgb24, top-down)
 * to a pipe. Every frame of the capture is then a real render at exactly t0 + k/FPS, however slowly
 * the game draws. Between captures the clock runs free (real time minus the time lost while locked),
 * so console typing, map loads and sleeps in the shell scripts behave as before.
 *
 * Arm a capture by writing "<frames> <output path>" to $LOCKSTEP_CTL (default /dev/shm/lockstep.ctl),
 * via a temp file + rename. On the next present the shim renames it to <ctl>.busy, opens the output
 * (open a fifo's reader first), locks the clock and captures the next <frames> presents; then it
 * closes the output, unlocks and renames <ctl>.busy to <ctl>.done.
 *
 * Faked: clock_gettime (monotonic and realtime families), gettimeofday, time, timespec_get, plus the
 * __*64 time64 entry points that Ubuntu's i386 Wine ntdll.so actually calls. Wine's
 * QueryPerformanceCounter and timeGetTime read these, in the game process. While locked, sleeps
 * (nanosleep, clock_nanosleep, usleep, fd-less select = Wine's Sleep) return at once.
 * Not faked: rdtsc, GetTickCount (written by wineserver), timeouts in poll/futex/epoll.
 * Wine's CSMT must be off (HKCU\Software\Wine\Direct3D csmt=0): with it the real swap runs on
 * another thread and the game can read the clock before the frame counter moves.
 *
 * Env: LOCKSTEP_FPS (30), LOCKSTEP_CTL, LOCKSTEP_PROC (comma list of cmdline substrings; only those
 * processes are faked, e.g. "halo.exe"), LOCKSTEP_EPS_NS (fake ns per clock read within a frame,
 * default 1000, capped at half a frame so spin-waits progress), LOCKSTEP_VERBOSE.
 * Build: capture/lockstep/build.sh.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#include <GL/gl.h>
#include <GL/glx.h>

#define GL_PIXEL_PACK_BUFFER_ 0x88EB
#define GL_PIXEL_PACK_BUFFER_BINDING_ 0x88ED
#define GL_READ_FRAMEBUFFER_ 0x8CA8
#define GL_READ_FRAMEBUFFER_BINDING_ 0x8CAA
#define EXPORT __attribute__((visibility("default")))

static int64_t period_ns = 1000000000LL / 30, eps_ns = 1000, rm_delta;
static int active = 1, verbose;
static char ctl[512] = "/dev/shm/lockstep.ctl";

/* clock state: free = real - lag; locked = base + frame*period + intra */
static _Atomic int locked;
static _Atomic int64_t lag, base, frame, seen_frame = -1, calls_in_frame;
static long want, got;        /* frames to capture / captured, render thread only */
static int out_fd = -1;
static unsigned char *buf, *row;
static int cap_w, cap_h;
static pthread_once_t once = PTHREAD_ONCE_INIT;
static volatile int inited;

static int64_t real_ns(clockid_t c) {   /* raw syscall: never recurses into the hooks */
#if defined(__i386__) && defined(SYS_clock_gettime64)
    struct { int64_t s, ns; } t;
    syscall(SYS_clock_gettime64, c, &t);
    return t.s * 1000000000LL + t.ns;
#else
    struct timespec t;
    syscall(SYS_clock_gettime, c, &t);
    return (int64_t)t.tv_sec * 1000000000LL + t.tv_nsec;
#endif
}

static int cmdline_matches(const char *list) {
    char cmd[4096], tmp[1024];
    int fd = open("/proc/self/cmdline", O_RDONLY | O_CLOEXEC);
    if (fd < 0) return 1;
    ssize_t n = read(fd, cmd, sizeof cmd - 1);
    close(fd);
    if (n <= 0) return 1;
    for (ssize_t i = 0; i < n; i++) if (!cmd[i]) cmd[i] = ' ';
    cmd[n] = 0;
    snprintf(tmp, sizeof tmp, "%s", list);
    for (char *save, *tok = strtok_r(tmp, ",", &save); tok; tok = strtok_r(NULL, ",", &save))
        if (*tok && strcasestr(cmd, tok)) return 1;
    return 0;
}

static void init_impl(void) {
    const char *s;
    double fps = (s = getenv("LOCKSTEP_FPS")) ? atof(s) : 30.0;
    if (fps <= 0) fps = 30.0;
    period_ns = (int64_t)(1e9 / fps + 0.5);
    if ((s = getenv("LOCKSTEP_EPS_NS"))) eps_ns = atoll(s);
    if ((s = getenv("LOCKSTEP_VERBOSE"))) verbose = atoi(s);
    if ((s = getenv("LOCKSTEP_CTL")) && *s) snprintf(ctl, sizeof ctl, "%s", s);
    if ((s = getenv("LOCKSTEP_PROC")) && *s) active = cmdline_matches(s);
    rm_delta = real_ns(CLOCK_REALTIME) - real_ns(CLOCK_MONOTONIC);
    inited = 1;
    if (verbose) fprintf(stderr, "lockstep[%d]: active=%d fps=%.3f ctl=%s\n", getpid(), active, fps, ctl);
}
static inline void init(void) { if (!inited) pthread_once(&once, init_impl); }
__attribute__((constructor)) static void ctor(void) { init(); }

/* fake monotonic ns. Within a locked frame each read adds eps (capped at half a frame) so loops
 * that wait on the clock still progress; only a present moves time across a frame boundary. */
static int64_t fake_mono(void) {
    if (!atomic_load(&locked)) return real_ns(CLOCK_MONOTONIC) - atomic_load(&lag);
    int64_t f = atomic_load(&frame), sf = atomic_load(&seen_frame);
    if (sf != f && atomic_compare_exchange_strong(&seen_frame, &sf, f)) atomic_store(&calls_in_frame, 0);
    int64_t intra = atomic_fetch_add(&calls_in_frame, 1) * eps_ns;
    if (intra > period_ns / 2) intra = period_ns / 2;
    return atomic_load(&base) + f * period_ns + intra;
}

static int fake_ns(clockid_t c, int64_t *ns) {
    init();
    if (!active) return 0;
    switch (c) {
    case CLOCK_MONOTONIC: case CLOCK_MONOTONIC_RAW: case CLOCK_MONOTONIC_COARSE: case CLOCK_BOOTTIME:
        *ns = fake_mono(); return 1;
    case CLOCK_REALTIME: case CLOCK_REALTIME_COARSE: case CLOCK_TAI:
        *ns = fake_mono() + rm_delta; return 1;
    default: return 0;
    }
}
static int64_t now_ns(clockid_t c) { int64_t ns; return fake_ns(c, &ns) ? ns : real_ns(c); }
static int sleeps_skipped(void) { init(); return active && atomic_load(&locked); }

/* ---------------- clock hooks ---------------- */
EXPORT int clock_gettime(clockid_t c, struct timespec *ts) {
    int64_t ns;
    if (!fake_ns(c, &ns)) return syscall(SYS_clock_gettime, c, ts);
    ts->tv_sec = ns / 1000000000LL; ts->tv_nsec = ns % 1000000000LL;
    return 0;
}
EXPORT int gettimeofday(struct timeval *tv, void *tz) {
    (void)tz;
    int64_t ns = now_ns(CLOCK_REALTIME);
    tv->tv_sec = ns / 1000000000LL; tv->tv_usec = (ns % 1000000000LL) / 1000;
    return 0;
}
EXPORT time_t time(time_t *t) {
    time_t s = now_ns(CLOCK_REALTIME) / 1000000000LL;
    if (t) *t = s;
    return s;
}
EXPORT int timespec_get(struct timespec *ts, int b) {
    if (b != TIME_UTC) return 0;
    clock_gettime(CLOCK_REALTIME, ts);
    return b;
}
#if defined(__i386__)
struct ts64 { int64_t tv_sec, tv_nsec; };
struct tv64 { int64_t tv_sec, tv_usec; };
EXPORT int __clock_gettime64(clockid_t c, struct ts64 *ts) {
    int64_t ns;
    if (!fake_ns(c, &ns)) ns = real_ns(c);
    ts->tv_sec = ns / 1000000000LL; ts->tv_nsec = ns % 1000000000LL;
    return 0;
}
EXPORT int __gettimeofday64(struct tv64 *tv, void *tz) {
    (void)tz;
    int64_t ns = now_ns(CLOCK_REALTIME);
    tv->tv_sec = ns / 1000000000LL; tv->tv_usec = (ns % 1000000000LL) / 1000;
    return 0;
}
EXPORT int64_t __time64(int64_t *t) {
    int64_t s = now_ns(CLOCK_REALTIME) / 1000000000LL;
    if (t) *t = s;
    return s;
}
#endif

/* ---------------- sleep hooks (skipped only while locked) ---------------- */
static void *next(const char *name, const char *v1, const char *v2) {
    void *p = dlvsym(RTLD_NEXT, name, v1);
    return p ? p : dlvsym(RTLD_NEXT, name, v2);
}
EXPORT int nanosleep(const struct timespec *req, struct timespec *rem) {
    if (sleeps_skipped()) { if (rem) rem->tv_sec = rem->tv_nsec = 0; sched_yield(); return 0; }
    static int (*real)(const struct timespec *, struct timespec *);
    if (!real) real = next("nanosleep", "GLIBC_2.2.5", "GLIBC_2.0");
    return real(req, rem);
}
EXPORT int clock_nanosleep(clockid_t c, int fl, const struct timespec *req, struct timespec *rem) {
    if (sleeps_skipped()) { if (rem) rem->tv_sec = rem->tv_nsec = 0; sched_yield(); return 0; }
    static int (*real)(clockid_t, int, const struct timespec *, struct timespec *);
    if (!real) real = next("clock_nanosleep", "GLIBC_2.17", "GLIBC_2.0");
    if (fl & TIMER_ABSTIME) {   /* the deadline is in fake time: wait the fake difference in real time */
        int64_t d = (int64_t)req->tv_sec * 1000000000LL + req->tv_nsec - now_ns(c);
        struct timespec r = { d > 0 ? d / 1000000000LL : 0, d > 0 ? d % 1000000000LL : 0 };
        return real(c, 0, &r, NULL);
    }
    return real(c, fl, req, rem);
}
EXPORT int usleep(useconds_t us) {
    struct timespec ts = { us / 1000000, (long)(us % 1000000) * 1000 };
    return nanosleep(&ts, NULL);
}
EXPORT int select(int nfds, fd_set *r, fd_set *w, fd_set *e, struct timeval *tv) {
    if (nfds == 0 && tv && sleeps_skipped()) { tv->tv_sec = tv->tv_usec = 0; sched_yield(); return 0; }
    static int (*real)(int, fd_set *, fd_set *, fd_set *, struct timeval *);
    if (!real) real = next("select", "GLIBC_2.2.5", "GLIBC_2.0");
    return real(nfds, r, w, e, tv);
}
#if defined(__i386__)
EXPORT int __nanosleep64(const struct ts64 *req, struct ts64 *rem) {
    struct timespec r = { (time_t)req->tv_sec, req->tv_nsec };
    if (rem) rem->tv_sec = rem->tv_nsec = 0;
    return nanosleep(&r, NULL);
}
EXPORT int __clock_nanosleep_time64(clockid_t c, int fl, const struct ts64 *req, struct ts64 *rem) {
    struct timespec r = { (time_t)req->tv_sec, req->tv_nsec };
    if (rem) rem->tv_sec = rem->tv_nsec = 0;
    return clock_nanosleep(c, fl, &r, NULL);
}
EXPORT int __select64(int nfds, fd_set *r, fd_set *w, fd_set *e, struct tv64 *tv) {
    if (nfds == 0 && tv && sleeps_skipped()) { tv->tv_sec = tv->tv_usec = 0; sched_yield(); return 0; }
    static int (*real)(int, fd_set *, fd_set *, fd_set *, struct tv64 *);
    if (!real) real = dlvsym(RTLD_NEXT, "__select64", "GLIBC_2.34");
    return real(nfds, r, w, e, tv);
}
#endif

/* ---------------- GL plumbing (Wine's winex11 finds GLX through dlsym) ---------------- */
typedef void *(*dlsym_fn)(void *, const char *);
static void *real_dlsym(void *h, const char *n) {
    static dlsym_fn p;
    if (!p) p = (dlsym_fn)dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.34");
    if (!p) p = (dlsym_fn)dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.2.5");
    if (!p) p = (dlsym_fn)dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.0");
    return p(h, n);
}
typedef void (*swap_fn)(Display *, GLXDrawable);
typedef void *(*gpa_fn)(const GLubyte *);
static swap_fn real_swap;
static gpa_fn real_gpa;
static void *libgl;

static void *gl_lookup(const char *name) {
    if (!real_gpa) {
        if (!libgl) libgl = dlopen("libGL.so.1", RTLD_LAZY | RTLD_NOLOAD);
        if (libgl) real_gpa = (gpa_fn)real_dlsym(libgl, "glXGetProcAddressARB");
        if (!real_gpa) real_gpa = (gpa_fn)real_dlsym(RTLD_NEXT, "glXGetProcAddressARB");
    }
    return real_gpa ? real_gpa((const GLubyte *)name) : NULL;
}
static struct {
    void (*GetIntegerv)(GLenum, GLint *);
    GLenum (*GetError)(void);
    void (*PixelStorei)(GLenum, GLint);
    void (*ReadBuffer)(GLenum);
    void (*ReadPixels)(GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, void *);
    void (*BindBuffer)(GLenum, GLuint);
    void (*BindFramebuffer)(GLenum, GLuint);
    int (*QueryDrawable)(Display *, GLXDrawable, int, unsigned int *);
} gl;
static void load_gl(void) {
    if (gl.ReadPixels) return;
    gl.GetIntegerv = gl_lookup("glGetIntegerv");
    gl.GetError = gl_lookup("glGetError");
    gl.PixelStorei = gl_lookup("glPixelStorei");
    gl.ReadBuffer = gl_lookup("glReadBuffer");
    gl.BindBuffer = gl_lookup("glBindBuffer");
    gl.BindFramebuffer = gl_lookup("glBindFramebuffer");
    gl.QueryDrawable = gl_lookup("glXQueryDrawable");
    gl.ReadPixels = gl_lookup("glReadPixels");
}

/* ---------------- capture ---------------- */
/* a reader that went away (cap.sh killed) must end the capture, not SIGPIPE the game */
static void write_all(const void *p, size_t n) {
    const char *c = p;
    sigset_t pipe, old;
    sigemptyset(&pipe); sigaddset(&pipe, SIGPIPE);
    pthread_sigmask(SIG_BLOCK, &pipe, &old);
    while (n && out_fd >= 0) {
        ssize_t w = write(out_fd, c, n);
        if (w < 0) { if (errno == EINTR) continue; perror("lockstep: write"); close(out_fd); out_fd = -1; return; }
        c += w; n -= (size_t)w;
    }
    struct timespec zero = { 0, 0 };
    while (sigtimedwait(&pipe, NULL, &zero) > 0) {}   /* drop the pending SIGPIPE, if any */
    pthread_sigmask(SIG_SETMASK, &old, NULL);
}

/* read the back buffer (the frame about to be presented) and write it top-down */
static void capture(Display *dpy, GLXDrawable d) {
    load_gl();
    if (out_fd < 0 || !gl.ReadPixels || !gl.GetIntegerv) return;
    unsigned int dw = 0, dh = 0;
    if (gl.QueryDrawable) { gl.QueryDrawable(dpy, d, GLX_WIDTH, &dw); gl.QueryDrawable(dpy, d, GLX_HEIGHT, &dh); }
    if (!dw || !dh) { GLint vp[4]; gl.GetIntegerv(GL_VIEWPORT, vp); dw = vp[2]; dh = vp[3]; }
    if (!buf) {   /* size fixed by the first captured frame */
        cap_w = dw; cap_h = dh;
        buf = calloc((size_t)cap_w * cap_h, 3);
        row = malloc((size_t)cap_w * 3);
        if (verbose) fprintf(stderr, "lockstep[%d]: capturing %dx%d rgb24\n", getpid(), cap_w, cap_h);
    }
    while (gl.GetError() != GL_NO_ERROR) {}
    GLint align, rowlen, skip_r, skip_p, rbuf, pack = 0, rfbo = 0;
    gl.GetIntegerv(GL_PACK_ALIGNMENT, &align);
    gl.GetIntegerv(GL_PACK_ROW_LENGTH, &rowlen);
    gl.GetIntegerv(GL_PACK_SKIP_ROWS, &skip_r);
    gl.GetIntegerv(GL_PACK_SKIP_PIXELS, &skip_p);
    gl.GetIntegerv(GL_PIXEL_PACK_BUFFER_BINDING_, &pack);
    gl.GetIntegerv(GL_READ_FRAMEBUFFER_BINDING_, &rfbo);
    while (gl.GetError() != GL_NO_ERROR) {}
    if (rfbo && gl.BindFramebuffer) gl.BindFramebuffer(GL_READ_FRAMEBUFFER_, 0);
    gl.GetIntegerv(GL_READ_BUFFER, &rbuf);
    if (pack && gl.BindBuffer) gl.BindBuffer(GL_PIXEL_PACK_BUFFER_, 0);
    gl.PixelStorei(GL_PACK_ALIGNMENT, 1);
    gl.PixelStorei(GL_PACK_ROW_LENGTH, cap_w);
    gl.PixelStorei(GL_PACK_SKIP_ROWS, 0);
    gl.PixelStorei(GL_PACK_SKIP_PIXELS, 0);
    gl.ReadBuffer(GL_BACK);
    memset(buf, 0, (size_t)cap_w * cap_h * 3);
    int w = cap_w < (int)dw ? cap_w : (int)dw, h = cap_h < (int)dh ? cap_h : (int)dh;
    gl.ReadPixels(0, (int)dh - h, w, h, GL_RGB, GL_UNSIGNED_BYTE, buf + (size_t)(cap_h - h) * cap_w * 3);
    GLenum err = gl.GetError();
    if (err && verbose) fprintf(stderr, "lockstep: glReadPixels error 0x%x\n", err);
    gl.PixelStorei(GL_PACK_ALIGNMENT, align);
    gl.PixelStorei(GL_PACK_ROW_LENGTH, rowlen);
    gl.PixelStorei(GL_PACK_SKIP_ROWS, skip_r);
    gl.PixelStorei(GL_PACK_SKIP_PIXELS, skip_p);
    gl.ReadBuffer(rbuf);
    if (pack && gl.BindBuffer) gl.BindBuffer(GL_PIXEL_PACK_BUFFER_, pack);
    if (rfbo && gl.BindFramebuffer) gl.BindFramebuffer(GL_READ_FRAMEBUFFER_, rfbo);
    for (int y = 0; y < cap_h / 2; y++) {   /* GL is bottom-up */
        unsigned char *a = buf + (size_t)y * cap_w * 3, *b = buf + (size_t)(cap_h - 1 - y) * cap_w * 3;
        memcpy(row, a, cap_w * 3); memcpy(a, b, cap_w * 3); memcpy(b, row, cap_w * 3);
    }
    write_all(buf, (size_t)cap_w * cap_h * 3);
}

static void suffix(char *dst, size_t n, const char *s) { snprintf(dst, n, "%s%s", ctl, s); }

/* an armed ctl file starts a capture: lock the clock at the current fake time */
static void maybe_arm(void) {
    char busy[600], path[512];
    FILE *f = fopen(ctl, "r");
    if (!f) return;
    long n = 0;
    int ok = fscanf(f, "%ld %511s", &n, path) == 2 && n > 0;
    fclose(f);
    suffix(busy, sizeof busy, ".busy");
    rename(ctl, busy);
    if (!ok) { fprintf(stderr, "lockstep: bad ctl file\n"); return; }
    out_fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);   /* blocks until a fifo reader */
    if (out_fd < 0) { perror("lockstep: open output"); return; }
    want = n; got = 0;
    atomic_store(&base, fake_mono());
    atomic_store(&frame, 0);
    atomic_store(&locked, 1);
    if (verbose) fprintf(stderr, "lockstep[%d]: locked, %ld frames -> %s\n", getpid(), n, path);
}

static void finish(void) {
    char busy[600], done[600];
    close(out_fd); out_fd = -1;
    /* resume real time one frame after the last captured one: the clock never steps backwards */
    atomic_store(&lag, real_ns(CLOCK_MONOTONIC) - (atomic_load(&base) + (atomic_load(&frame) + 1) * period_ns));
    atomic_store(&locked, 0);
    suffix(busy, sizeof busy, ".busy"); suffix(done, sizeof done, ".done");
    rename(busy, done);
    if (verbose) fprintf(stderr, "lockstep[%d]: captured %ld frames, unlocked\n", getpid(), got);
}

EXPORT void glXSwapBuffers(Display *dpy, GLXDrawable d) {
    init();
    if (!real_swap) {
        real_swap = (swap_fn)real_dlsym(RTLD_NEXT, "glXSwapBuffers");
        if (!real_swap) real_swap = (swap_fn)gl_lookup("glXSwapBuffers");
    }
    if (!active) { real_swap(dpy, d); return; }
    if (atomic_load(&locked)) {
        capture(dpy, d);
        real_swap(dpy, d);
        atomic_fetch_add(&frame, 1);
        if (++got >= want || out_fd < 0) finish();
    } else {
        real_swap(dpy, d);
        maybe_arm();
    }
}

static void *hook_gpa(const GLubyte *name) {
    if (!strcmp((const char *)name, "glXSwapBuffers")) return (void *)glXSwapBuffers;
    return gl_lookup((const char *)name);
}
EXPORT void (*glXGetProcAddress(const GLubyte *n))(void) { return (void (*)(void))hook_gpa(n); }
EXPORT void (*glXGetProcAddressARB(const GLubyte *n))(void) { return (void (*)(void))hook_gpa(n); }

EXPORT void *dlsym(void *h, const char *name) {
    if (name && name[0] == 'g' && name[1] == 'l' && name[2] == 'X') {
        if (!strcmp(name, "glXSwapBuffers")) {
            if (!real_swap && h != RTLD_NEXT && h != RTLD_DEFAULT) real_swap = (swap_fn)real_dlsym(h, name);
            return (void *)glXSwapBuffers;
        }
        if (!strcmp(name, "glXGetProcAddressARB") || !strcmp(name, "glXGetProcAddress")) {
            if (h != RTLD_NEXT && h != RTLD_DEFAULT) {
                if (!real_gpa) real_gpa = (gpa_fn)real_dlsym(h, "glXGetProcAddressARB");
                if (!libgl) libgl = h;
            }
            return (void *)glXGetProcAddressARB;
        }
    }
    return real_dlsym(h, name);
}
