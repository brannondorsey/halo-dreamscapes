# How the halo-crt setup works

This covers everything behind the two one-hour cuts (Silent Cartographer and
Blood Gulch): the environment, how the game is driven, how shots are designed,
how the glitch engine and score work, and the problems hit along the way. The
README has the short version.

## Overview

```
Xvfb :99 ─ Wine (win32) ─ halo.exe (Halo PC Trial, 2003) ─ Chimera (strings.dll)
                                                      └─ rig.lua  ◄── shot.lua (written by shot.sh)
ffmpeg x11grab ─► $HALO_DIR/caps/<shot>.mp4 ─► glitch.py --calm ─► cuts/<map>_1h.mp4 ─► play.sh on a CRT
```

- The footage is real Halo, from Microsoft's free **Halo PC Trial**. It ships
  `bloodgulch.map` and `b30.map` (Silent Cartographer) only. No game files are
  in the repo; `clips/`, `*.mp4` and `*.wav` are gitignored.
- There's no HUD, no first-person gun and no player or AI on screen. A Chimera
  Lua script drives the free camera along keyframed paths.
- `glitch.py` cuts the shots together at the MPEG-4 bitstream level (datamosh,
  P-frame bloom), adds scanline tears and slips, and muxes a generated score
  from `soundtrack.py`.

## 1. Environment

The two cuts were made in an Ubuntu 24.04 container with no GPU.

| piece | version / setting |
|---|---|
| Wine | 9.0 (Ubuntu package), `WINEARCH=win32`, prefix at `$HALO_DIR/prefix` |
| Display | `Xvfb :99 -screen 0 800x600x24 +extension GLX` (software GL via Mesa) |
| Game | `halo.exe -novideo -window -vidmode 800,600,60 -console` |
| Game window | 640x480, at offset +80,60 inside the 800x600 screen |
| Capture | `ffmpeg -f x11grab -framerate 30 -video_size 640x480 -i :99+80,60`, x264 crf 12 |
| Input | `xdotool keydown/keyup` (real XTest events; `--window`/XSendEvent is ignored by the game) |

Packages: `wine wine32:i386 xvfb xdotool p7zip-full mingw-w64 cmake ffmpeg python3-numpy python3-scipy fonts-dejavu-core`.

**HALO_DIR.** Every script uses `HALO_DIR=${HALO_DIR:-$HOME/halo-trial}`. In the
cloud container `$HOME` was `/root`, so export `HALO_DIR=/home/user/halo-trial`
or similar explicitly. The layout is:

```
$HALO_DIR/game/     extracted trial (halo.exe, maps/, strings.dll = Chimera)
$HALO_DIR/prefix/   wine prefix
$HALO_DIR/caps/     captured shots, one mp4 per shot name
$HALO_DIR/now.png   last screenshot from con.sh / shot.sh
```

### Installing the trial

1. Get `HaloTrialSetup.exe` (archive.org: `halo-trial-setup`).
2. Run `7z x -o$HALO_DIR/game HaloTrialSetup.exe`. Nothing runs; it's an archive.
3. Run `capture/run.sh -console` once and accept the EULA dialog. That's a
   manual step; whoever owns the setup has to accept it.

### Building Chimera (free camera, Lua, dev commands)

Chimera ([SnowyMouse/chimera](https://github.com/SnowyMouse/chimera)) is an open
source Halo PC mod. GitHub release downloads were blocked by the proxy, so it was
built from source at tag `1.0.0r995` with the mingw toolchain file in
`capture/chimera/mingw32.cmake` (i686, **posix** threads):

```sh
git clone --branch 1.0.0r995 https://github.com/SnowyMouse/chimera
cmake -S chimera -B build -G "Unix Makefiles" \
      -DCMAKE_TOOLCHAIN_FILE=capture/chimera/mingw32.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
mv $HALO_DIR/game/strings.dll $HALO_DIR/game/strings-old.dll
cp build/strings.dll chimera/chimera.ini $HALO_DIR/game/
cp -r chimera/fonts $HALO_DIR/game/
```

- Use **Unix Makefiles**. The Ninja generator hits a glob bug in Chimera's
  build.
- Keep `load_embedded_lua=1` in `chimera.ini` (the default).

### Installing the camera rig

Copy `capture/rig.lua` to:

```
$HALO_DIR/prefix/drive_c/users/$USER/Documents/My Games/Halo Trial/chimera/lua/scripts/global/rig.lua   (`Halo CE` instead of `Halo Trial` for Custom Edition)
```

The rig polls `.../chimera/lua/data/global/rig/shot.lua` every 10 ticks.
`shot.sh` writes that file. On the `precamera` callback the rig overrides the
camera position, FOV and orientation every frame. `ticks()` gives fractional
ticks for smooth motion.

## 2. Driving the game

| script | does |
|---|---|
| `capture/run.sh [args]` | starts Xvfb :99 and the game |
| `capture/con.sh "cmd" ... "sleep:N"` | opens the console (grave key), types each command, screenshots to `now.png`, closes it with grave. `NOOPEN=1` skips opening. |
| `capture/k.sh Key s1 Key2` | key presses; `sN` sleeps N seconds |
| `capture/shot.sh '<lua table>' [sleep]` | sets the rig's shot and screenshots it; `shot.sh ''` releases the camera |
| `capture/cap.sh name secs '<table>'` | sets the shot and records `secs` to `$HALO_DIR/caps/name.mp4` |
| `capture/setup.sh bloodgulch\|b30` | loads a map and strips it for filming (below) |

Don't close the console with Escape: it opens the quit dialog.

### Console commands that make it scenery-only

```
chimera_devmode true                   # unlocks dev commands
chimera_lua_reload_scripts             # (re)loads rig.lua
map_name bloodgulch | map_name b30
show_hud 0
camera_control 1                       # removes the first-person gun (Backspace free cam alone didn't)
cheat_deathless_player 1
ai_erase_all                           # removes Covenant (b30)
garbage_collect_now                    # removes bodies and dropped weapons
object_set_scale (list_get (players) 0) 0.01 0   # hides the player body (it shows on Blood Gulch roofs)
debug_camera_save                      # writes game/camera.txt (pos, forward, up, fov in radians)
switch_bsp N                           # b30's interiors are BSP 1; see "Dead ends"
```

b30 opens with a ~2 min cutscene. Let it play before you run the rest.

## 3. Shot design

Shot lists are Python modules in `capture/lists/` (`b30.py`, `bloodgulch.py`)
built with helpers from `capture/shotlist.py`:

- `static(name, cam, look, fov=70, secs=75)`: a locked-off shot.
- `move(name, secs, [(cam, look), ...], fov, ease)`: a path spread evenly over `secs`.
- `arc(name, secs, r, a0, a1, z, look, fov, steps, cx, cy)`: an orbit around (cx, cy).
- `P(r, deg, z, cx, cy)`: a polar position (b30's island is centred at 0,0 with the beach at r ≈ 95).
- `drift()` (in `bloodgulch.py`): a near-static shot creeping about 0.1 m/s.
  Blood Gulch has nothing that moves on its own, so a fully locked shot looks
  like a freeze.

```sh
cd capture
./shotlist.py lists/X.py names           # shot names, in order
./shotlist.py lists/X.py scout > s.txt   # first/last frame of each shot as 'x y z tx ty tz fov'
./scout.py s.txt sheet.png               # numbered contact sheet of those frames
./shotlist.py lists/X.py run [names...]  # film each shot (secs + 2) unless caps/<name>.mp4 exists
```

The rig's Lua table is `{ ease = bool, keys = { {t, x,y,z, tx,ty,tz, fov_deg}, ... } }`
with Catmull-Rom interpolation. `ease` smooths the ends, and the up vector is
world z, orthogonalised.

**Rules for the footage:** see [SHOT_GUIDE.md](SHOT_GUIDE.md). In short: a nature
documentary in Halo (majestic and mundane, beautiful and quiet), with scenic
shots and natural motion; about 15% interiors; numbered contact sheets
approved by the owner before filming; nothing behind the curtain.

### Workflow for a new shot

1. Find a position: fly the free cam and run `debug_camera_save`, or guess
   coordinates from the map's layout.
2. Run `shot.sh '{ keys = { {0, x,y,z, tx,ty,tz, 70} } }' 1.5` and look at `now.png`.
3. Add it to the list, `scout` the whole list, and look at the sheet for void,
   clipping and the player body.
4. `run`, then check frames from each capture (several timestamps per shot).
   Paths can dip under terrain mid-shot.

## 4. Glitch engine (`glitch.py`)

1. **Plan.** Pick shots (`--calm` uses a shuffle bag) and segment lengths, and
   choose each transition: `cut`, `mosh` or `tear`. Each segment can also get a
   bloom (P-frame repeat) and scan events.
2. **Encode** each segment to raw MPEG-4 Part 2 (`.m4v`) with no B-frames,
   `-g 100000` and `-sc_threshold 1e9`, so there's a single I-frame at the
   start plus forced keyframes where a mosh should heal.
3. **Splice** at VOP start codes (`00 00 01 B6`, GOV `B3` stripped). The VOP
   type is the top 2 bits of the next byte.
   - mosh: drop the segment's first I-VOP. The new shot's motion vectors drag
     the previous picture until the forced keyframe `heal` seconds later.
   - bloom: repeat one P-VOP N times, so motion smears outward.
4. **Decode** the joined stream with `-err_detect ignore_err` and
   `setpts=N/(30*TB)`.
5. **Scan faults** per frame in numpy, through the `Scan` class: `tear`
   (vsync tear, lagging lower field), `slip` (h-sync band slips with RGB
   split), `roll` (vertical hold loss with a black bar), `softtear` (one gentle
   8–24 px slip of the lower field, 0.4–1.0 s).
6. **Encode** with x264 plus the score WAV. Output is 640x480 4:3, with no fake
   scanlines.

`--calm` (used for the hour cuts): 45–90 s segments, mosh weight 2.5, bloom
0.3; transitions are mosh or cut only, heal 3–7 s, bloom repeats 10–24, and the
only scan event is the soft tear. The rule was "every glitch that isn't jarring;
don't cut too often." The owner approved all of the calm effects and wants
exactly **6 soft tears per hour** (`--soft-tears`, placed on random shots); an
hour also averages about 39 moshes and 16 blooms.

Hour cuts: `./hour.sh`, or by hand:

```sh
./glitch.py $(cd capture && ./shotlist.py lists/b30.py names | sed "s#.*#$HALO_DIR/caps/&.mp4#") \
    --calm --minutes 60 --seed 30 -o cuts/silent_cartographer_1h.mp4    # 61.0 min, 272 events, ~510 MB
./glitch.py $(... lists/bloodgulch.py ...) --calm --minutes 60 --seed 31 -o cuts/blood_gulch_1h.mp4   # 61.3 min, 281 events, ~540 MB
```

The render takes about 30–40 minutes per hour of output. Don't film while it
runs: CPU contention drops capture frames.

`sampler.py` renders a numbered, labeled reel with one demo of every effect,
marked [CALM] or [FULL] by which preset uses it. Give it three locked-off clips
and two moving ones (fly-through, then orbit), each at least 12 s:
`./sampler.py --still a.mp4 b.mp4 c.mp4 --moving fly.mp4 orbit.mp4 -o sampler.mp4`.
`--only 4 6` renders just those demos.

## 5. Score (`soundtrack.py`)

The score is original and generated with numpy/scipy. It's inspired by the
Halo soundtrack's monk choir and synth atmosphere, but copies nothing from it.

- Saw voices through formant resonators (choir and chant), detuned saw pads,
  sub bass, square arpeggios, wind noise and booms.
- FFT-convolution hall reverb.
- Glitch sync: every visual event has an audio counterpart. mosh → frozen grain
  sinking in pitch, bloom → stutter, tear/slip → bitcrush, roll → tape stop,
  softtear → light crush.
- `render(seconds, events, seed, chunk=300, overlap=8)` composes in 5-minute
  chunks crossfaded over 8 s (each normalised to 0.8), then applies glitches,
  end fades and a tanh limiter. Hour-long scores never loop.

## 6. Playing it

`play.sh file.mp4...` loops fullscreen with mpv, falling back to vlc or ffplay,
and restarts if the player dies. The suggested box is a Raspberry Pi with
composite out (`enable_tvout=1`, `sdtv_mode=0` NTSC / `2` PAL).

## 7. Gotchas and dead ends

- **Out-of-map void.** Blood Gulch renders a flat peach colour above z ≈ 17–30
  and past the map edges. Keep cameras low and keep orbits inside the canyon.
  b30's void (inside BSP 1) is flat purple, about RGB (51, 45, 85).
- **b30 interiors.** They're in a separate BSP that the free cam couldn't find,
  even with `switch_bsp 1` plus a grid search (the old `probe.py`). Gave up and
  used `switch_bsp 0`. b30 is all exterior.
- **Vehicles, weapons and other bipeds** (multiplayer maps place dozens). The
  rig's strip mode deletes them continuously, so respawns are removed too.
  `setup.sh` turns it on for every map except the two trial cuts by creating
  `chimera/lua/data/global/rig/strip`. It walks the object table at
  `0x400506B4` and deletes object types 0–5 (biped, vehicle, weapon,
  equipment, garbage, projectile) except the player's biped. Scenery, light
  fixtures and machines stay, and so does the level geometry (buildings,
  terrain), so some fixed turrets that are placed as scenery remain.
- **The free cam showed the gun** on both maps; `camera_control 1` fixes that.
- **Covenant and corpses on b30.** `ai_erase_all` and `garbage_collect_now`. An
  empty Ghost and the parked Pelicans stay; they're vehicles, not people.
- **Recording** fails silently if the output dir doesn't exist.
- **`pgrep -f` waits** match their own command line, so use a distinctive
  pattern.
- **Delivery.** Chat attachments are capped at 30 MB. Full cuts went out via
  Litterbox (catbox.moe), with 72 h links.
