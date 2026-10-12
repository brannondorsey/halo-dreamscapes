# Pending: more maps

Status: **unblocked.** Halo Custom Edition 1.0.10 runs under Wine with Chimera
and the rig, and has all 19 official multiplayer maps. No shot lists for them yet.

### How Custom Edition was installed (no installer run)

1. Download `halocesetup_en_1.00.exe` from halomaps (fid=410, sha256 below).
2. Run `7z x -o$HALO_DIR/game halocesetup_en_1.00.exe`. The installer is a plain
   archive, so the unverified setup program never runs. The maps are in `maps/`.
3. Put the game at `C:\Program Files\Microsoft Games\Halo Custom Edition` in a
   win32 prefix and symlink `$HALO_DIR/game` to it.
4. Patch it to 1.0.10, which Chimera needs. The official patch
   (`haloce-patch-1.0.10.zip`, halomaps fid=6798) is Authenticode-signed by
   Bungie Inc. Its wrapper refused to run, so `patch.rtp` from inside it was
   applied directly through `patchw32.dll`'s `RTPatchApply32NoCall("\"<game dir>\" C:\patch.rtp")`.
   `haloce.exe` then reports 01.00.10.0621.
5. Install Chimera (rename `strings.dll` to `strings-old.dll`) and copy `rig.lua` into
   `My Games/Halo CE/chimera/lua/scripts/global/`. `run.sh` and `shot.sh` detect
   `haloce.exe` and use the `Halo CE` folder automatically.

The product key wasn't needed to load maps locally. Don't store it anywhere.

Trial and Custom Edition render the same shot identically (Blood Gulch,
`bg_blue_roof`), so new cuts will match the existing ones.

## Goal

Make more one-hour cuts like the Silent Cartographer and Blood Gulch ones,
following the same rules: only landscapes and interiors, no people or action,
no HUD, no first-person view, and classic, identifiable angles. Use the same
pipeline (`setup.sh` → shot list → `shotlist.py run` → `glitch.py --calm
--minutes 60`).

**Official maps only.** Use only the Bungie/Gearbox maps that shipped with Halo PC
or Custom Edition. No community or custom maps from halomaps or anywhere else.

## Background: why it was blocked

The Halo PC Trial ships only `bloodgulch.map` and `b30.map`. Every other map
needs the full **Halo PC (2003)** game or **Halo Custom Edition**. The Chimera
camera rig only works with those, not with the Master Chief Collection.

- **Halo PC is out of print.** The owner has a retail disc with a product key,
  but the key isn't in this repo. Ask them for it; don't commit it.
- **Halo Custom Edition** is the official free multiplayer-only release (all 19
  multiplayer maps, no campaign). It needs a Halo PC key. Its installer was
  downloaded from halomaps.org
  (`https://www.halomaps.org/hce/detail.cfm?fid=410`: POST the page's form
  with `fid=410&action=dl&hash=…&submit=download`):
  - file `halocesetup_en_1.00.exe`, 178,262,016 bytes
  - sha256 `011b03b61634561d7c1b6090e7229fe0a2df40de2c2a14b45ac8f0455d5d990f`
  - md5 `d3894ce0426a80c93392c851e3403fdb`
  - Unsigned, PE build date 2009-12-04, version info "© 2004 Microsoft Corp."
  - VirusTotal: **3/69** detections (QuickHeal W32.Virut.G, Varist
    W32/Virut.BU.gen, Zoner Heur.ExeHeader). The major engines report it
    clean. First submitted to VirusTotal in 2017, under many
    `halocesetup_en_1.00.exe` names. This is probably a false positive, but it
    isn't proven.
- The cloud session's automatic safety check refused to run or even unpack
  this unverified installer, and `/permissions` wasn't available there to add
  an allow rule. An isolated Wine prefix was prepared for it (`WINEPREFIX` of
  its own, `Xvfb :98`), but the installer was never run.

## Ways to unblock (pick one)

1. **Files from the owner's disc (preferred).** Make an ISO of the Halo PC
   disc, or copy the `maps/` folder of an installed copy, and fetch it via a
   link. That gives the trusted original files and the campaign levels too.
   Install the game under Wine the same way as the trial, then add Chimera and
   `rig.lua`.
2. **Custom Edition from halomaps.** Run it in an environment where the owner
   can approve running the installer, in its own Wine prefix and display. Enter
   the owner's key. Check the installed files (`maps/*.map`) before going
   further. Multiplayer maps only.

After either one, check that the existing scripts work against the full game:
- Paths: the user folder is `Halo` instead of `Halo Trial`, and Custom Edition
  uses `Halo CE`. Fix the rig paths in `shot.sh` and the README.
- Chimera supports Halo PC retail and Custom Edition with the same
  `strings.dll`.

## Candidate maps (Halopedia)

Prioritised for bar scenery. The map-file name, where known, is in brackets.

**Campaign** (full Halo PC only):
- [Halo](https://www.halopedia.org/Halo_(Halo:_Combat_Evolved_level)) [a30]: the
  iconic first ring vistas. **Top pick.**
- [Assault on the Control Room](https://www.halopedia.org/Assault_on_the_Control_Room) [b40]:
  snow, bridges, giant Forerunner structures. **Top pick.**
- [343 Guilty Spark](https://www.halopedia.org/343_Guilty_Spark_(level)) [c10]: foggy swamp at night.
- [The Pillar of Autumn](https://www.halopedia.org/The_Pillar_of_Autumn_(level)) [a10]: ship interiors.
- [The Truth and Reconciliation](https://www.halopedia.org/The_Truth_and_Reconciliation_(level)) [a50]: night canyon, Covenant ship.
- [The Library](https://www.halopedia.org/The_Library) [c20]: endless corridors (interiors).
- [Two Betrayals](https://www.halopedia.org/Two_Betrayals) [c40], [Keyes](https://www.halopedia.org/Keyes_(level)) [d20], [The Maw](https://www.halopedia.org/The_Maw_(level)) [d40].

Campaign maps start full of AI and scripted events. Plan on `ai_erase_all`,
`garbage_collect_now`, and possibly `switch_bsp` to reach different areas (see
the b30 interior dead end in SETUP.md).

**Multiplayer** (Halo PC or Custom Edition):
- PC-only and very scenic: [Death Island](https://www.halopedia.org/Death_Island),
  [Timberland](https://www.halopedia.org/Timberland), [Ice Fields](https://www.halopedia.org/Ice_Fields),
  [Danger Canyon](https://www.halopedia.org/Danger_Canyon), [Infinity](https://www.halopedia.org/Infinity_(Halo:_Combat_Evolved_map)),
  [Gephyrophobia](https://www.halopedia.org/Gephyrophobia)
- Classics: [Sidewinder](https://www.halopedia.org/Sidewinder), [Hang 'Em High](https://www.halopedia.org/Hang_%27Em_High),
  [Battle Creek](https://www.halopedia.org/Battle_Creek), [Damnation](https://www.halopedia.org/Damnation),
  [Chill Out](https://www.halopedia.org/Chill_Out), [Derelict](https://www.halopedia.org/Derelict),
  [Boarding Action](https://www.halopedia.org/Boarding_Action), [Rat Race](https://www.halopedia.org/Rat_Race),
  [Prisoner](https://www.halopedia.org/Prisoner), [Chiron TL-34](https://www.halopedia.org/Chiron_TL-34),
  [Longest](https://www.halopedia.org/Longest), [Wizard](https://www.halopedia.org/Wizard)

Multiplayer maps have no AI, so on those `setup.sh` only needs the HUD, gun
and player-body steps.

## Per-map checklist

1. `capture/setup.sh <map>`. Confirm there's no HUD, gun, player or AI in
   `now.png`.
2. Write `capture/lists/<map>.py` with about 30–40 shots following
   [SHOT_GUIDE.md](SHOT_GUIDE.md): scenic compositions with natural motion and
   varied angles and positions.
   Mix: about 40% static or drift wides, 25% close-ups, 20% slow fly-throughs
   and orbits, and about 15% interiors where the map has them. Point still shots
   at something moving (water, fog, sky) where possible.
3. `scout` the list and fix anything behind the curtain (void, seams, clipping,
   visible objects). Send the numbered contact sheets to the owner and **wait
   for approval**. Replace any shots they reject, re-scout and ask again.
4. `run`. It QCs every capture as soon as it's filmed (`qc.py`: splices, black,
   void, short or missing) and refilms flagged shots up to twice. Then check
   frames from several timestamps of every capture.
5. Render it:
   `./glitch.py <caps> --calm --minutes 60 --seed <new> -o cuts/<map>_1h.mp4`.
   Contact-sheet one frame a minute and send a preview of 30 MB or less.
6. Add the map to `hour.sh`.
