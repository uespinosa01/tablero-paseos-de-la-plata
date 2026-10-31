// Logica pura (sin DOM) para buscar calles y leer lineas de casas. Se prueba con tools/prueba_logica.js.
const VACIAS = new Set(["calle", "circuito", "cto", "paseo", "po", "p", "o", "blvd", "boulevard", "bv", "privada", "priv",
  "c", "de", "del", "la", "las", "los", "el"]);

const GENERICAS = new Set(["mina", "real", "monte", "minas", "paseos", "plata"]);

function normalizar(texto) {
  return String(texto).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9 ]+/g, " ").replace(/\s+/g, " ").trim();
}

function clave(texto) {
  return normalizar(texto).split(" ").filter((p) => !VACIAS.has(p)).join(" ");
}

function distancia(a, b) {
  let fila = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const nueva = [i];
    for (let j = 1; j <= b.length; j++) {
      nueva[j] = Math.min(nueva[j - 1] + 1, fila[j] + 1, fila[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    fila = nueva;
  }
  return fila[b.length];
}

// calles: [{ n: nombre, a: [otros nombres] }]. Devuelve exactas y, si no hay, parecidas.
function buscarCalles(consulta, calles) {
  const q = clave(consulta);
  if (!q) return { exactas: [], parecidas: [] };
  const claves = (c) => [c.n, ...(c.a || [])].map(clave);
  const exactas = calles.filter((c) => claves(c).some((k) => k.includes(q) || k.split(" ").some((p) => p.startsWith(q))));
  if (exactas.length) return { exactas, parecidas: [] };
  const puntuadas = calles.map((c) => ({ c, d: Math.min(...claves(c).flatMap((k) => [k, ...k.split(" ")]).map((k) => distancia(q, k))) }))
    .filter((x) => x.d <= Math.max(2, Math.floor(q.length / 3)))
    .sort((a, b) => a.d - b.d);
  return { exactas: [], parecidas: puntuadas.slice(0, 4).map((x) => x.c) };
}

// Lee una linea como "Jaspe #120, viernes 31 a partir de las 7:00 pm".
function leerCasa(linea, calles) {
  const limpia = String(linea).replace(/^\s*\d+[.)]\s*/, "").trim();
  if (!limpia) return null;
  const texto = clave(limpia);
  const palabras = texto.split(" ");
  let calle = null, mejorLargo = 0;
  for (const c of calles) {
    for (const k of [c.n, ...(c.a || [])].map(clave)) {
      if (k && k.length > mejorLargo && (" " + texto + " ").includes(" " + k + " ")) {
        calle = c.n;
        mejorLargo = k.length;
      }
    }
  }
  if (!calle) {
    // "Peregrina #726" se refiere a "Mina la Peregrina": basta la palabra distintiva.
    calle = (calles.find((c) => clave(c.n).split(" ").some((p) => p.length >= 4 && !GENERICAS.has(p) && palabras.includes(p))) || {}).n || null;
  }
  if (!calle) {
    let menor = 3;
    for (const p of palabras.filter((x) => x.length >= 5)) {
      for (const c of calles) {
        for (const k of [c.n, ...(c.a || [])].map(clave)) {
          const d = distancia(p, k);
          if (d < menor) { menor = d; calle = c.n; }
        }
      }
    }
  }
  const num = limpia.match(/#\s*(\d+)/) || limpia.match(/\b(\d{2,4})\b(?!\s*:)/);
  const hora = limpia.match(/(\d{1,2})(?::(\d{2}))?\s*(?:pm|p\.\s?m)/i);
  return {
    calle,
    numero: num ? num[1] : "",
    hora: hora ? `${hora[1]}:${hora[2] || "00"} pm` : "",
    texto: limpia,
  };
}

const LOGICA = { normalizar, clave, distancia, buscarCalles, leerCasa };
if (typeof module !== "undefined") module.exports = LOGICA;
