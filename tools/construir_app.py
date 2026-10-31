"""Inyecta datos y logica en src/app.html. Escribe docs/ (sitio instalable) y salida/ (vista previa como artifact)."""
import json, math
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
tramos = json.loads((RAIZ / "datos/calles.json").read_text(encoding="utf-8"))
puntos = [p for t in tramos for p in t["p"]]
norte, oeste = max(p[0] for p in puntos), min(p[1] for p in puntos)
sur, este = min(p[0] for p in puntos), max(p[1] for p in puntos)
kx = 111320 * math.cos(math.radians((norte + sur) / 2))
ky = 110574


def xy(p):
    return [round((p[1] - oeste) * kx, 1), round((norte - p[0]) * ky, 1)]


calles, otros = defaultdict(lambda: {"a": set(), "s": []}), defaultdict(set)
sin_nombre = []
for t in tramos:
    pieza = [xy(p) for p in t["p"]]
    if t["n"]:
        calles[t["n"]]["s"].append(pieza)
        if t["a"]:
            calles[t["n"]]["a"].add(t["a"])
    else:
        sin_nombre.append(pieza)
datos = {
    "norte": norte, "oeste": oeste, "kx": round(kx, 2), "ky": ky,
    "ancho": round((este - oeste) * kx), "alto": round((norte - sur) * ky),
    "calles": {n: {"a": sorted(c["a"]), "s": c["s"]} for n, c in sorted(calles.items())},
    "sinNombre": sin_nombre,
}
plantilla = (RAIZ / "src/app.html").read_text(encoding="utf-8")
logica = (RAIZ / "src/logica.js").read_text(encoding="utf-8")
cuerpo = plantilla.replace("/*__LOGICA__*/", logica).replace("/*__DATOS__*/null", json.dumps(datos, ensure_ascii=False, separators=(",", ":")))

(RAIZ / "salida").mkdir(exist_ok=True)
(RAIZ / "salida/vista-previa.html").write_text(cuerpo, encoding="utf-8")
(RAIZ / "docs").mkdir(exist_ok=True)
(RAIZ / "docs/index.html").write_text(
    '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">\n'
    '<meta name="theme-color" content="#211d2c"><link rel="manifest" href="manifest.webmanifest">\n'
    '<link rel="icon" href="icono.svg"><style>:root{padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px);box-sizing:border-box;height:100%}body{margin:0}[hidden]{display:none!important}</style>\n'
    '</head><body>\n' + cuerpo + "\n</body></html>\n", encoding="utf-8")
print("calles", len(datos["calles"]), "sin nombre", len(sin_nombre), "bytes", len(cuerpo.encode("utf-8")))
