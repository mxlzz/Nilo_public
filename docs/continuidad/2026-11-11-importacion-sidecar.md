# Nilo 0.7.1 — C1b: importación de capturas asociadas a partidas

Registro de continuidad: [#97](https://github.com/mxlzz/Nilo_public/issues/97).

## Situación anterior
El laboratorio permitía cargar una copia temporal de la SQLite del mundo,
pero no la sidecar `*.llm_requests.sqlite3`. El visor, aunque usara la
partida correcta tras PR #98, no podía mostrar solicitudes históricas de
un mundo importado sin un archivo emparejado.

## Cambio experimental
- Botón **Importar capturas LLM** habilitado solo tras importar una partida.
- Endpoint `/api/history/upload-sidecar`: acepta una SQLite de capturas y
  exige coincidencia exacta de al menos un `trace_call_id` de deliberación
  con los IDs de `llm_requests.call_id`.
- Comprobación `PRAGMA quick_check`, columnas mínimas y SHA-256/tamaño de
  cada cuerpo capturado. El archivo se copia al directorio temporal del
  servidor **solo después** de verificarlo.
- No escribe a la SQLite original, no reemplaza sidecars existentes y no
  acepta importar capturas sobre una partida de la carpeta. Historial y visor
  LLM utilizan el mismo mundo seleccionado, también para sus enlaces.
- Pruebas: pareamiento, rechazo de sidecar ajena, original intacto,
  condición sin capturas, consulta HTTP y enlace de episodio.

## Limitaciones explícitas
Una coincidencia de ID demuestra correspondencia para esos registros, **no**
que todas las capturas del archivo estén relacionadas con esa partida, ni que
Nilo haya utilizado cognitivamente un recuerdo. Archivos de partidas antiguas
sin `trace_call_id` deben rechazarse por falta de prueba verificable.
No convierte el contexto modular experimental en funcionalidad activa.

## Aceptación
CI completa, prueba HTTP y revisión con un par de SQLite real antes de
incorporar estos cambios a `main`.
