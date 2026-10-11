# Shot guide

These are the owner's rules for every cut. They override any older shot-mix
numbers elsewhere in the docs.

## What to film

- **A nature documentary shot inside Halo. Think *Survivorman*.** It should
  look as if a lone filmmaker carried a camera into this world and left it
  running: raw and grounded, with tripod-height and ground-level positions,
  long unhurried takes and slow pans, and the environment as the subject.
  Prioritise scenic shots with ambient, natural motion: drifting clouds, waves
  and water, swaying foliage, fog, waterfalls, light. Point still shots at
  something that moves.
- **Beautiful scenes and vistas.** Scout for interesting compositions:
  foreground framing, leading lines, depth, silhouettes and classic,
  identifiable angles. Don't just place the camera at the first spot that works.
- **Vary the camera.** Use different angles, heights, distances, lenses (FOV)
  and positions across the list. Avoid near-duplicates.
- **Mostly interiors.** Each cut mixes interior shots (the majority) with
  exterior shots (the minority). When a map has few interiors, use every good
  one it has and state the actual split when asking for approval.
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
