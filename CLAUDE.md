# Agent notes

Before designing, scouting, filming or rendering any shots, read and follow
[docs/SHOT_GUIDE.md](docs/SHOT_GUIDE.md). Always get the owner's approval of the
numbered contact sheets before filming. Never commit the Halo product key.

Every per-map setting lives in `maps/<map>/` (docs/SETUP.md, "Per-map settings"); don't hard-code
map settings in scripts. Render with `./render.py <map>` and commit the record it writes. Work
test-first and run `python -m pytest tests` before pushing.

Always share files with the owner through Filebin: `./share.sh <file>` uploads to a fresh, unguessable
bin and prints the link (bins expire after about a week). Deliver renders that way, plus a preview of
30 MB or less in chat. Chat attachments can't carry full cuts.
