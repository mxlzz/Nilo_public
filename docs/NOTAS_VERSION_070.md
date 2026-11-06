# Nilo 0.7.0 — Notas de versión

## Qué cambia

- El motor se organiza en el paquete `nilo_runtime`: aplicación/orquestación, mundo,
  física, necesidades, percepción, agente y proveedores, autonomía, cognición, persistencia,
  laboratorio y servidor/interfaz.
- Las operaciones, eventos y mediciones se auditan con contratos y referencias de evidencia.
  Historial SQLite transaccional, backups en copias nuevas, checkpoints y replay técnico.
- Interfaz separada en HTML, CSS y JS sin alterar intencionalmente su comportamiento.
- Herramientas automatizadas de arquitectura, QA, migración y evaluación de partidas.
- El ZIP portable contiene `BUILD_INFO.json` con la versión y el SHA del commit cuando
  se conoce al compilar, más `MANIFIESTO_SHA256.json` recalculado sobre sus bytes reales.
- Se conserva la API pública heredada por medio de fachadas de compatibilidad, para
  no romper partidas, tests ni scripts dependientes. No se instala un segundo motor.

## Lo que no cambia

- El formato de partida compatible conserva `SAVE_SCHEMA_VERSION = 5`; la etiqueta
  de producto pasa a 0.7.0. No atribuir evolución de física o conducta al mero refactor.
- No se completan automáticamente proyectos ni se imponen objetivos a Nilo.
- Siguen pendientes los bucles de cierre y recreación de proyectos, la gestión de
  objetivos compuestos y exploración reiterada sin frontera alcanzable.
- La primera corrida real de etapa 23 fue con Gemini. **Groq no fue verificado de
  extremo a extremo en esta fase**; se conserva su integración existente.

## Instalar y actualizar

1. Obtener **Nilo-0.7.0.zip** de GitHub Releases, no el ZIP de código fuente.
2. Extraer en carpeta nueva de Windows de 64 bits.
3. Ejecutar `INICIAR_NILO.bat`; prepara CPython 3.12.10 embebido, con SHA256 fijado.
4. Importar opcionalmente la configuración y **una copia** de una partida anterior.
5. Conservar la carpeta y copia original hasta comprobar arranque y datos.

Para volver atrás, cerrar Nilo y abrir la instalación anterior con su propia partida
o copia de seguridad; no sobrescribir la SQLite de una versión nueva con
una más antigua. Las claves API permanecen en `config.env` local y nunca
se incluyen en el ZIP.

## Validación y límites

- [Acta de etapa 23](ETAPA_23_CIERRE_ARQUITECTURA_07.md) y
  [etapa 24](ETAPA_24_APERTURA_07.md).
- Pruebas de regresión, laboratorio, replay, ZIP y compatibilidad; la publicación
  exige smoke del paquete en Windows y Linux y corroboración de migración y rollback.
- El hash de commit del bundle identifica el código distribuido; no convierte
  deliberaciones LLM en experimentos deterministas.
