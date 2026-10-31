// Ejecutar: node tools/prueba_logica.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { buscarCalles, leerCasa, leerLista, diaDeHoy } = require("../src/logica.js");

const tramos = JSON.parse(fs.readFileSync(path.join(__dirname, "../datos/calles.json"), "utf8"));
const calles = [...new Set(tramos.map((t) => t.n).filter(Boolean))].map((n) => ({ n, a: [] }));
const nombres = (r) => r.map((c) => c.n);

assert.ok(nombres(buscarCalles("carbon", calles).exactas).includes("Carbón"), "carbon sin acento");
assert.ok(nombres(buscarCalles("Cto. del Cobalto", calles).exactas).includes("Cobalto"), "ignora prefijos");
assert.ok(nombres(buscarCalles("peregrina", calles).exactas).includes("Mina la Peregrina"), "busca por palabra");
assert.ok(nombres(buscarCalles("circnonio", calles).parecidas).includes("Circonio"), "tolera typos");
assert.ok(nombres(buscarCalles("lapizlazuli", calles).parecidas).includes("Lapislázuli"), "tolera z por s");
assert.deepStrictEqual(buscarCalles("xxxxxxxx", calles), { exactas: [], parecidas: [] }, "nada parecido");

const casa = leerCasa("12. Jaspe #999, viernes 31 a partir de las 7:00 pm.", calles);
assert.strictEqual(casa.calle, "Jaspe");
assert.strictEqual(casa.numero, "999");
assert.strictEqual(casa.hora, "7:00 pm");
assert.strictEqual(leerCasa("Tienda Lapizlazuli #999, a partir de las 7:30 pm", calles).calle, "Lapislázuli");
assert.strictEqual(leerCasa("Peregrina #999 entre las 7:00 y 8:00 pm", calles).calle, "Mina la Peregrina");
assert.strictEqual(leerCasa("Real de minas #999", calles).calle, "Real de Minas");
assert.strictEqual(leerCasa("Citrino #999 despues de 8pm", calles).hora, "8:00 pm");
assert.strictEqual(leerCasa("Citrino #999 despues de 8pm", calles).calle, "Citrino");
assert.ok(nombres(buscarCalles("citrino", calles).exactas).includes("Citrino"), "calle en un circuito sin rotulo en OSM");
const leidos = (archivo) => fs.readFileSync(path.join(__dirname, "../datos", archivo), "utf8").trim().split(/\r?\n/).slice(1)
  .map((l) => l.split(",").pop()).filter((n) => n !== "-");
for (const n of new Set([...leidos("etiquetas.csv"), ...leidos("etiquetas_auditoria.csv")])) {
  assert.ok(nombres(calles).includes(n), `nombre confirmado perdido: ${n}`);
}
assert.ok(nombres(calles).includes("Ágata"), "Ágata hallada en la auditoria");
assert.ok(nombres(calles).includes("Las Beolas"), "Beolas sustituye a la lectura erronea Brecia");
assert.ok(!nombres(calles).includes("Brecia"), "Brecia no debe quedar");
assert.ok(!nombres(calles).includes("-"), "el marcador de sin nombre no llega a la app");
assert.strictEqual(leerCasa("   ", calles), null);
assert.strictEqual(leerCasa("Aluminio - 6:30 p. m", calles).numero, "", "la hora no es numero de casa");
assert.strictEqual(leerCasa("Aluminio - 6:30 p. m", calles).hora, "6:30 pm");
assert.strictEqual(leerCasa("Travertino 999 - Antes de las 6 pm", calles).hora, "antes de las 6:00 pm");
assert.strictEqual(leerCasa("Traventino 999", calles).calle, "Travertino", "tolera typo del volante");
assert.strictEqual(leerCasa("Mina de Mesillas 999", calles).calle, "Mina la Mesilla", "tolera plural en calle de mina");
assert.strictEqual(leerCasa("Carbon 999", calles).calle, "Carbón", "Carbón y Carbono son calles distintas");
assert.strictEqual(leerCasa("Carbono 999", calles).calle, "Carbono");

const lista = leerLista("Sin horario: 7:00 pm\nSábado 31\nCuarzo 999\nPedernal 998 - 6 pm\n\nDomingo 1:\nCuarzo 999", calles);
assert.strictEqual(lista.length, 3, "los encabezados no son casas");
assert.deepStrictEqual(lista.map((c) => c.dia), ["Sábado 31", "Sábado 31", "Domingo 1"]);
assert.strictEqual(lista[0].hora, "7:00 pm", "sin horario toma el valor general");
assert.strictEqual(lista[1].hora, "6:00 pm", "el horario propio gana");
assert.strictEqual(diaDeHoy(["Sábado 31", "Domingo 1"], new Date(2026, 10, 1)), "Domingo 1");
assert.strictEqual(diaDeHoy(["Sábado 31", "Domingo 1"], new Date(2026, 10, 9)), "", "fuera de fechas muestra todas");
console.log("logica OK");
