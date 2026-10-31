"""PNG de revision: azul=Google, verde=OSM, naranja=inferido, rojo=sin nombre. Solo control de calidad."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
COLOR = {"google": (30, 90, 220), "osm": (20, 150, 70), "inferido": (230, 130, 0), None: (225, 30, 30)}
S, W, N, E = 20.0505, -98.8075, 20.0632, -98.7972
if len(sys.argv) > 2:
    S, W, N, E = map(float, sys.argv[2].split(","))
ESC = 1000 / (E - W)
tramos = json.loads((RAIZ / "datos/calles.json").read_text(encoding="utf-8"))
im = Image.new("RGB", (1000, int((N - S) * ESC * 1.064)), "white")
d = ImageDraw.Draw(im)


def xy(p):
    return (p[1] - W) * ESC, (N - p[0]) * ESC * 1.064


for t in tramos:
    d.line([xy(p) for p in t["p"]], fill=COLOR[t["f"]], width=2)
for t in tramos:
    if t["n"]:
        d.text(xy(t["p"][len(t["p"]) // 2]), t["n"][:14], fill=(0, 0, 0))
im.save(sys.argv[1])
