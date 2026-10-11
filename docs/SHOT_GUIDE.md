# Shot guide

These are the owner's rules for every cut. The shot-type mix (percentages) is in
[NEW_MAPS.md](NEW_MAPS.md#per-map-checklist).

## What to film

- **A nature documentary shot inside Halo.** Use *Survivorman* as inspiration
  for the vibe, not as a rulebook: a lone camera quietly observing the world,
  with the environment as the subject. Aim for **majestic and mundane:
  beautiful and quiet.** Grand vistas sit next to ordinary, still corners.
  Prioritise scenic shots with ambient, natural motion: drifting clouds, waves
  and water, swaying foliage, fog, waterfalls, light. Point still shots at
  something that moves.
- **Beautiful scenes and vistas.** Scout for interesting compositions:
  foreground framing, leading lines, depth, silhouettes and classic,
  identifiable angles. Don't just place the camera at the first spot that works.
- **Vary the camera.** Use different angles, heights, distances, lenses (FOV)
  and positions across the list. Avoid near-duplicates.
- **Interiors and exteriors.** Follow the mix in NEW_MAPS.md: about 15%
  interiors where the map has them, the rest exteriors.
- **Omit anything "behind the curtain":** out-of-map void, map edges and seams,
  skybox edges, the underside of terrain or geometry, missing backfaces,
  clipping, floating or unfinished objects, and dev or spawn markers. Also omit
  the earlier exclusions: no people, AI, players, action, HUD or first-person
  view.

## Output

- Every rendered video is **1 hour**: `glitch.py --calm --minutes 60`.

## Approval before filming

1. Scout the shot list and produce **numbered contact sheets** (`shotlist.py
   scout` + `scout.py`). Show first and last frames, and sample moving shots
   too, so the motion is visible.
2. **Always ask the owner for approval** with the sheets before filming. They
   may ask for specific numbered shots to be replaced. Re-scout the replacements
   and ask again.
3. Film and render the hour only after approval.
