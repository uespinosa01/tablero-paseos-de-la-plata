// Ejecutar: node tools/prueba_logica.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { buscarCalles, leerCasa } = require("../src/logica.js");

const tramos = JSON.parse(fs.readFileSync(path.join(__dirname, "../datos/calles.json"), "utf8"));
const calles = [...new Set(tramos.map((t) => t.n).filter(Boolean))].map((n) => ({ n, a: [] }));
const nombres = (r) => r.map((c) => c.n);

assert.ok(nombres(buscarCalles("carbon", calles).exactas).includes("Carbón"), "carbon sin acento");
assert.ok(nombres(buscarCalles("Cto. del Cobalto", calles).exactas).includes("Cobalto"), "ignora prefijos");
assert.ok(nombres(buscarCalles("peregrina", calles).exactas).includes("Mina la Peregrina"), "busca por palabra");
assert.ok(nombres(buscarCalles("circnonio", calles).parecidas).includes("Circonio"), "tolera typos");
assert.ok(nombres(buscarCalles("lapizlazuli", calles).parecidas).includes("Lapislázuli"), "tolera z por s");
assert.deepStrictEqual(buscarCalles("xxxxxxxx", calles), { exactas: [], parecidas: [] }, "nada parecido");

const casa = leerCasa("12. Jaspe #120, viernes 31 a partir de las 7:00 pm.", calles);
assert.strictEqual(casa.calle, "Jaspe");
assert.strictEqual(casa.numero, "120");
assert.strictEqual(casa.hora, "7:00 pm");
assert.strictEqual(leerCasa("Food Station Lapizlazuli #114, a partir de las 7:30 pm", calles).calle, "Lapislázuli");
assert.strictEqual(leerCasa("Peregrina #726 entre las 7:00 y 8:00 pm", calles).calle, "Mina la Peregrina");
assert.strictEqual(leerCasa("Real de minas #603", calles).calle, "Real de Minas");
assert.strictEqual(leerCasa("Citrino #145 despues de 8pm", calles).hora, "8:00 pm");
assert.strictEqual(leerCasa("Citrino #145 despues de 8pm", calles).calle, "Citrino");
assert.ok(nombres(buscarCalles("citrino", calles).exactas).includes("Citrino"), "Citrino confirmada por el usuario");
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
console.log("logica OK");
