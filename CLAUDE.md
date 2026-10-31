# Tablero Paseos de la Plata (Halloween)

Responde siempre en español. Proyecto express: mapa para celular, sin internet, con buscador de calles que ilumina la calle, GPS y lista de casas con dulces.

## Cómo está armado
- `datos/osm.json`: geometría de OpenStreetMap (Overpass).
- `datos/etiquetas.csv`: nombres leídos de Google Maps; cada fila guarda la captura (z, centro) y el píxel de la etiqueta. Google manda sobre OSM.
- `tools/construir_calles.py`: une ambos en `datos/calles.json`.
- `tools/construir_app.py`: inyecta datos en `src/app.html` y genera `docs/` (sitio instalable) y `salida/vista-previa.html`.
- `tools/prueba_logica.js`: pruebas de búsqueda y lectura de casas (`node tools/prueba_logica.js`).

## Reglas
- Ninguna casa va en el código ni en el repo público: son domicilios de vecinos. Las casas viven en el celular (localStorage) y llegan por el cuadro de pegar o por un enlace privado `#casas=` (el fragmento no se envía al servidor). La lista vigente se guarda en `salida/`, que no se versiona.
- Ningún mapa público trae números de casa: se ilumina la calle completa. No inventar posiciones.
- Sin dependencias ni llamadas de red en la app.
