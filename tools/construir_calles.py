"""Une geometria de OSM con las etiquetas leidas de Google Maps y escribe datos/calles.json."""
import csv, json, math, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TIPOS_FUERA = {"footway", "path", "cycleway", "steps", "track", "pedestrian"}
PERIMETRO = [(20.0622, -98.8046), (20.0590, -98.7987), (20.0585, -98.79946), (20.0505, -98.79946),
             (20.0505, -98.8005), (20.0516, -98.8022), (20.0522, -98.8050), (20.0528, -98.8066),
             (20.0548, -98.8063), (20.0572, -98.8057), (20.0586, -98.8052), (20.0592, -98.80495),
             (20.0600, -98.80485), (20.0607, -98.8048)]
EXCLUIDAS = {"Aguamarina", "Calle Turquesa", "Calle Cuarzo", "Calle Zafiro", "Calle Gavilanes",
             "Campo de Tiro", "El Dorado", "Tercera Cerrada Hacienda Pitahayas", "Primera San Antonio Regla",
             "Calle Las Aguilas", "Las Aguilas", "Privada Las Aguilas", "Calle Manganeso", "Isla Mujeres",
             "24 de Octubre", "Privada Nikte", "Calle Rubí"}
PREFIJO = re.compile(r"^(boulevard|calle|circuito)\s+", re.I)
ARTICULO = re.compile(r"^(paseo\s+)?(de la|de las|de los|del|de)\s+", re.I)
OSM_A_GOOGLE = {"Arcillas": "Las Arcillas", "Canteras": "Las Canteras (Paseo)", "Pizarras": "Las Pizarras",
                "Mina Las Ánimas": "Mina las Ánimas", "Mina La Peregrina": "Mina la Peregrina",
                "Mina La Mesilla": "Mina la Mesilla", "Mina La Siciliana": "Mina la Siciliana",
                "Esmeralda": "Esmeralda", "Paseos de la Plata": "Paseos de la Plata"}
ANGULO_RECTO_MAX = 28
DIST_SNAP_M = 28
LARGO_MAX_SIN_NOMBRE_M = 250
DIST_SNAP_AUDITORIA_M = 15
CENTRO_AUDITORIA = (337, 149.5)
VIAS_AJENAS = {1265010752, 850218347}  # Caminos al poniente, fuera del fraccionamiento.
SIN_NOMBRE = "-"  # Google no lo rotula ni al maximo acercamiento: se marca para que nada lo herede.


def base_osm(nombre):
    n = PREFIJO.sub("", nombre)
    if not n.lower().startswith("paseos"):
        n = ARTICULO.sub("", n)
    return OSM_A_GOOGLE.get(n, n[0].upper() + n[1:])


def dentro(lat, lon):
    hit = False
    for (a, b), (c, d) in zip(PERIMETRO, PERIMETRO[1:] + PERIMETRO[:1]):
        if (b > lon) != (d > lon) and lat < a + (lon - b) * (c - a) / (d - b):
            hit = not hit
    return hit


def etiqueta_a_coord(z, clat, clon, x, y):
    grados_px = 360 / (256 * 2 ** z) * 1.5
    return clat - (y - 300) * grados_px * math.cos(math.radians(clat)), clon + (x - 400) * grados_px


def etiqueta_auditoria_a_coord(z, clat, clon, px, py):
    """Capturas sin escalar de 674x299: un pixel de imagen es un pixel de pantalla."""
    grados_px = 360 / (256 * 2 ** z)
    return clat - (py - CENTRO_AUDITORIA[1]) * grados_px * math.cos(math.radians(clat)), clon + (px - CENTRO_AUDITORIA[0]) * grados_px


def dist_seg_m(p, a, b):
    kx, ky = 111320 * math.cos(math.radians(p[0])), 110574
    ax, ay, bx, by = (a[1] - p[1]) * kx, (a[0] - p[0]) * ky, (b[1] - p[1]) * kx, (b[0] - p[0]) * ky
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def rumbo(a, b):
    return math.atan2((b[1] - a[1]) * math.cos(math.radians(a[0])), b[0] - a[0])


def cargar_tramos():
    datos = json.loads((RAIZ / "datos/osm.json").read_text(encoding="utf-8"))
    tramos = []
    for e in datos["elements"]:
        tags = e.get("tags", {})
        if e["type"] != "way" or "highway" not in tags or "geometry" not in e or tags["highway"] in TIPOS_FUERA:
            continue
        if tags.get("name") in EXCLUIDAS:
            continue
        puntos = [(p["lat"], p["lon"]) for p in e["geometry"]]
        if sum(dentro(*p) for p in puntos) * 2 >= len(puntos):
            tramos.append({"id": e["id"], "puntos": puntos, "osm": tags.get("name"),
                           "nombre": None, "fuente": None})
    return partir_en_cruces(tramos)


def partir_en_cruces(tramos):
    """OSM a veces une dos calles en una sola via; se parte en cada cruce para nombrar pieza por pieza."""
    usos = {}
    for t in tramos:
        for p in set(t["puntos"]):
            usos[p] = usos.get(p, 0) + 1
    piezas = []
    for t in tramos:
        actual = [t["puntos"][0]]
        for p in t["puntos"][1:]:
            actual.append(p)
            if usos[p] > 1 and p != t["puntos"][-1]:
                piezas.append({**t, "puntos": actual})
                actual = [p]
        piezas.append({**t, "puntos": actual})
    return piezas


def tramo_cercano(p, tramos):
    mejor, dist = None, 1e9
    for t in tramos:
        for a, b in zip(t["puntos"], t["puntos"][1:]):
            d = dist_seg_m(p, a, b)
            if d < dist:
                mejor, dist = t, d
    return mejor, dist


def aplicar_etiquetas(tramos):
    fallidas = []
    with (RAIZ / "datos/etiquetas.csv").open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            p = etiqueta_a_coord(int(fila["z"]), float(fila["clat"]), float(fila["clon"]),
                                 float(fila["x"]), float(fila["y"]))
            mejor, dist = tramo_cercano(p, tramos)
            if mejor is None or dist > DIST_SNAP_M:
                fallidas.append((fila["nombre"], round(dist)))
            elif mejor["fuente"] != "google" or dist < mejor.get("dist", 1e9):
                mejor.update(nombre=fila["nombre"], fuente="google", dist=dist)
    # La auditoria se leyo con mas acercamiento: gana sobre la primera pasada.
    with (RAIZ / "datos/etiquetas_auditoria.csv").open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            p = etiqueta_auditoria_a_coord(float(fila["z"]), float(fila["clat"]), float(fila["clon"]),
                                           float(fila["px"]), float(fila["py"]))
            mejor, dist = tramo_cercano(p, tramos)
            if mejor is None or dist > DIST_SNAP_AUDITORIA_M:
                fallidas.append((fila["nombre"], round(dist)))
            else:
                mejor.update(nombre=fila["nombre"], fuente="google", dist=0)
    return fallidas


def largo_m(t):
    return sum(dist_seg_m(a, a, b) for a, b in zip(t["puntos"], t["puntos"][1:]))


def nombrar_con_osm(tramos):
    """Google manda: dentro de una via de OSM, cada pieza toma la etiqueta mas cercana; sin etiquetas, el nombre OSM."""
    por_via = {}
    for t in tramos:
        por_via.setdefault(t["id"], []).append(t)
    for piezas in por_via.values():
        con_etiqueta = [i for i, t in enumerate(piezas) if t["fuente"] == "google"]
        for i, t in enumerate(piezas):
            if t["nombre"] or not t["osm"]:
                continue
            if con_etiqueta:
                cercana = min(con_etiqueta, key=lambda j: abs(j - i))
                t.update(nombre=piezas[cercana]["nombre"], fuente="inferido")
            else:
                t.update(nombre=base_osm(t["osm"]), fuente="osm")


def propagar(tramos):
    """Un tramo sin nombre hereda el de un vecino si sigue recto, o si une dos brazos con el mismo nombre."""
    por_nodo = {}
    for t in tramos:
        por_nodo.setdefault(t["puntos"][0], []).append(t)
        por_nodo.setdefault(t["puntos"][-1], []).append(t)
    while True:
        # Por rondas: dos nombres que avanzan por la misma linea se encuentran a la mitad.
        nuevos = [(t, n) for t in tramos if not t["nombre"] for n in [nombre_heredado(t, por_nodo)] if n]
        if not nuevos:
            return
        for t, n in nuevos:
            t.update(nombre=n, fuente="inferido")


def heredable(t):
    return t["nombre"] and t["nombre"] != SIN_NOMBRE


def nombre_heredado(t, por_nodo):
    ini, fin = t["puntos"][0], t["puntos"][-1]
    comun = {v["nombre"] for v in por_nodo[ini] if heredable(v)} & {v["nombre"] for v in por_nodo[fin] if heredable(v)}
    if comun:
        return sorted(comun)[0]
    mejor, menor = None, ANGULO_RECTO_MAX
    for extremo, sig in ((ini, t["puntos"][1]), (fin, t["puntos"][-2])):
        for v in por_nodo[extremo]:
            if not heredable(v) or v is t:
                continue
            otro = v["puntos"][1] if v["puntos"][0] == extremo else v["puntos"][-2]
            giro = abs(math.degrees(rumbo(extremo, sig) - rumbo(otro, extremo)))
            giro = min(giro % 360, 360 - giro % 360)
            if giro < menor:
                mejor, menor = v["nombre"], giro
    return mejor


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tramos = cargar_tramos()
    fallidas = aplicar_etiquetas(tramos)
    nombrar_con_osm(tramos)
    propagar(tramos)
    for t in tramos:
        if t["nombre"] == SIN_NOMBRE:
            t.update(nombre=None, fuente=None)
    tramos = [t for t in tramos if t["id"] not in VIAS_AJENAS]
    tramos = [t for t in tramos if t["nombre"] or (largo_m(t) <= LARGO_MAX_SIN_NOMBRE_M and any(dentro(*p) for p in t["puntos"]))]
    salida = [{"id": t["id"], "n": t["nombre"], "f": t["fuente"],
               "a": base_osm(t["osm"]) if t["osm"] and base_osm(t["osm"]) != t["nombre"] else None,
               "p": [[round(a, 6), round(b, 6)] for a, b in t["puntos"]]} for t in tramos]
    (RAIZ / "datos/calles.json").write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    nombres = sorted({t["nombre"] for t in tramos if t["nombre"]})
    print(f"tramos={len(tramos)} con_nombre={sum(1 for t in tramos if t['nombre'])}")
    print("etiquetas sin tramo cercano:", fallidas)
    print(len(nombres), nombres)
    conflictos = sorted({(t["osm"], t["nombre"]) for t in tramos if t["osm"] and t["fuente"] == "google"
                         and base_osm(t["osm"]) != t["nombre"]})
    print("conflictos osm/google:", conflictos)


if __name__ == "__main__":
    main()
