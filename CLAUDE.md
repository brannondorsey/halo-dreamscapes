# Agent notes

Before designing, scouting, filming or rendering any shots, read and follow
[docs/SHOT_GUIDE.md](docs/SHOT_GUIDE.md). Always get the owner's approval of the
numbered contact sheets before filming. Never commit the Halo product key.

Every per-map setting lives in `maps/<map>/` (docs/SETUP.md, "Per-map settings"); don't hard-code
map settings in scripts. Render with `./render.py <map>` and commit the record it writes. Work
test-first and run `python -m pytest tests` before pushing.

Deliver renders with `./share.sh <file>` (Litterbox, 72 h links), plus a preview of
30 MB or less in chat. Chat attachments can't carry full cuts.
