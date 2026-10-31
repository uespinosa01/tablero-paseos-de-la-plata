"""Lista los puntos a revisar en Google Maps: grupos de tramos sin confirmacion directa, del mas largo al mas corto."""
import json, math, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LARGO_MIN_M = 30


def largo_m(p):
    return sum(math.hypot((a[0] - b[0]) * 110574, (a[1] - b[1]) * 104500) for a, b in zip(p, p[1:]))


def punto_medio(p):
    resto = largo_m(p) / 2
    for a, b in zip(p, p[1:]):
        d = math.hypot((a[0] - b[0]) * 110574, (a[1] - b[1]) * 104500)
        if d >= resto:
            t = resto / d if d else 0
            return round(a[0] + t * (b[0] - a[0]), 5), round(a[1] + t * (b[1] - a[1]), 5)
        resto -= d
    return tuple(p[-1])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tramos = [t for t in json.loads((RAIZ / "datos/calles.json").read_text(encoding="utf-8"))
              if t["f"] != "google" and largo_m(t["p"]) >= LARGO_MIN_M]
    por_nodo = {}
    for i, t in enumerate(tramos):
        for extremo in (tuple(t["p"][0]), tuple(t["p"][-1])):
            por_nodo.setdefault(extremo, []).append(i)
    vistos, grupos = set(), []
    for i in range(len(tramos)):
        if i in vistos:
            continue
        pila, grupo = [i], []
        while pila:
            j = pila.pop()
            if j in vistos:
                continue
            vistos.add(j)
            grupo.append(tramos[j])
            for extremo in (tuple(tramos[j]["p"][0]), tuple(tramos[j]["p"][-1])):
                pila += [k for k in por_nodo[extremo] if k not in vistos and tramos[k]["n"] == tramos[j]["n"]]
        grupos.append(grupo)
    grupos.sort(key=lambda g: -sum(largo_m(t["p"]) for t in g))
    for g in grupos:
        mayor = max(g, key=lambda t: largo_m(t["p"]))
        lat, lon = punto_medio(mayor["p"])
        print(f"{lat},{lon}\t{mayor['n'] or '(sin nombre)'}\t{mayor['f']}\t{round(sum(largo_m(t['p']) for t in g))}m\t{len(g)}")
    print("grupos:", len(grupos))


if __name__ == "__main__":
    main()
