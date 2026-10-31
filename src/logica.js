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
          // "Mina de Mesillas" se compara tambien contra la palabra distintiva de "Mina la Mesilla".
          for (const opcion of [k, ...k.split(" ").filter((x) => !GENERICAS.has(x))]) {
            const d = distancia(p, opcion);
            if (d < menor) { menor = d; calle = c.n; }
          }
        }
      }
    }
  }
  const num = limpia.match(/#\s*(\d+)/) || limpia.replace(/\d{1,2}:\d{2}/g, " ").match(/\b(\d{2,4})\b/);
  const hora = limpia.match(/(antes de las?\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:pm|p\.\s?m)/i);
  return {
    calle,
    numero: num ? num[1] : "",
    hora: hora ? `${hora[1] ? "antes de las " : ""}${hora[2]}:${hora[3] || "00"} pm` : "",
    texto: limpia,
  };
}

const ENCABEZADO_DIA = /^(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+(\d{1,2})\s*:?$/i;
const SIN_HORARIO = /^sin horario:\s*(.+)$/i;

// Lee una lista completa: "Sabado 31" abre un dia y "Sin horario: 7:00 pm" da la hora de las casas que no traen una.
function leerLista(texto, calles) {
  let dia = "", horaGeneral = "";
  const casas = [];
  for (const linea of String(texto).split(/\r?\n/)) {
    const limpia = linea.trim();
    const encabezado = limpia.match(ENCABEZADO_DIA);
    const general = limpia.match(SIN_HORARIO);
    if (encabezado) dia = `${encabezado[1]} ${encabezado[2]}`;
    else if (general) horaGeneral = general[1];
    else {
      const casa = leerCasa(limpia, calles);
      if (casa) casas.push({ ...casa, dia, hora: casa.hora || horaGeneral });
    }
  }
  return casas;
}

function diaDeHoy(dias, fecha) {
  return dias.find((d) => Number(d.split(" ").pop()) === fecha.getDate()) || "";
}

const LOGICA = { normalizar, clave, distancia, buscarCalles, leerCasa, leerLista, diaDeHoy };
if (typeof module !== "undefined") module.exports = LOGICA;
