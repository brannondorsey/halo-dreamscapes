/* bar.c - slow, clock-driven GL test app for the lockstep shim: a white bar moves SPEED px/s
 * (position from clock_gettime) and each frame burns a random amount of CPU, so it renders at an
 * irregular few fps like Halo on software GL. */
#define _GNU_SOURCE
#include <GL/gl.h>
#include <GL/glx.h>
#include <X11/Xlib.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define W 320
#define H 120
#define BARW 24
#define SPEED 60.0
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char**argv){
  long burn = argc>1? atol(argv[1]) : 60000000; /* base iterations */
  Display*d=XOpenDisplay(NULL); if(!d){fprintf(stderr,"no display\n");return 1;}
  int att[]={GLX_RGBA,GLX_DOUBLEBUFFER,GLX_RED_SIZE,8,GLX_GREEN_SIZE,8,GLX_BLUE_SIZE,8,None};
  XVisualInfo*vi=glXChooseVisual(d,DefaultScreen(d),att);
  XSetWindowAttributes swa={0}; swa.colormap=XCreateColormap(d,RootWindow(d,vi->screen),vi->visual,AllocNone);
  Window win=XCreateWindow(d,RootWindow(d,vi->screen),0,0,W,H,0,vi->depth,InputOutput,vi->visual,CWColormap,&swa);
  XMapWindow(d,win); XSync(d,False);
  GLXContext ctx=glXCreateContext(d,vi,NULL,True); glXMakeCurrent(d,win,ctx);
  glViewport(0,0,W,H); glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0,W,H,0,-1,1);
  double t0=now(); srand(1);
  for(;;){
    double t=now()-t0;
    double x=fmod(t*SPEED,(double)(W-BARW));
    glClearColor(0.08,0.08,0.12,1); glClear(GL_COLOR_BUFFER_BIT);
    glColor3f(1,1,1); glBegin(GL_QUADS);
    glVertex2f(x,0);glVertex2f(x+BARW,0);glVertex2f(x+BARW,H);glVertex2f(x,H);glEnd();
    /* burn CPU: 0.5x..1.5x base, irregular */
    volatile double acc=0; long n=burn/2+(long)((double)rand()/RAND_MAX*burn);
    for(long i=0;i<n;i++) acc+=i*1e-9;
    glXSwapBuffers(d,win);
  }
}
