# Revisión crítica — Etapa 1 después de H14 (22/11/2026)

**Propósito:** evaluar si los resultados de H1–H14 permiten declarar terminada la etapa 1 («materia compartida, sin paisaje») sin confundir ensayos demostrativos con arquitectura terminada. **Dictamen: NO.** Este registro no cambia la hoja rectora; la jerarquía continúa en `BASES_Y_HOJA_DE_RUTA.md` y `PROCEDIMIENTO_Y_AUDITORIA.md`.

## Evidencia consolidada

- **Estado y propiedad material:** H1–H3 muestran arrays, validación de límites, controles negativos y publicación de un estado candidato; H4–H6 prueban que una superficie 2.5D no preserva cavidades, y que una ROI 3D puede tener propietario exclusivo. Son escenarios pequeños y operaciones manuales.
- **Movimiento de objetos:** H7–H8 comprueban gravedad y contacto de sólidos rígidos Bullet incluso en cavidad invisible para una altura; no prueban la formación de dicha cavidad.
- **Redistribución:** H9 [SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45048479951) demuestra transporte fluvial 2.5D con masa publicada en xarray, pérdidas externas explícitas; H10 [SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45049166835) verifica interacción de 27 granos rígidos 3D que se dispersaron, sin estructura estable.
- **Deformación volumétrica:** H11 [SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45055263832) ensayó la constitución Drucker–Prager MPM 3D externa con efecto de fricción; H12 [FAIL por gate físico](https://github.com/mxlzz/Nilo_public/actions/runs/45055570920) no pudo acreditar estabilidad sin artefactos de soporte, por 61,11% de partículas en el piso/clamp. El owner xarray de H11/H12 refleja masa declarada en el solver: **no es aún el punto de entrada autoritativo a MPM**.
- **Proveedor independiente:** H13A [FAIL 1](https://github.com/mxlzz/Nilo_public/actions/runs/45055983838) y [FAIL 2](https://github.com/mxlzz/Nilo_public/actions/runs/45056130916) se bloquearon en imports de Open3D y luego Plotly, sin llegar a física. No demuestra ni desmiente estabilidad física de GeoTaichi, pero elevó el costo de integración.
- **Energía:** H14 [SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45056513417) muestra conducción 1D de calor con un único inventario de energía y masa en xarray, conservación dentro de4,7e-9J, ablaciones sin k/sin gradiente, replay y NetCDF. No hay transformación de materia ni origen de calor mecánico.

## Dificultad central pendiente (priorizada por objetivo)

Se demostraron fenómenos **aislados**, pero el objetivo es **un mismo mundo** con interacciones causales y estado persistente. Lo siguiente NO se ha demostrado:

1. **Compatibilidad física y contable simultánea** de masa, posición y energía en una transformación real que afecte más de un tipo de inventario o región. No construir un bus de eventos/orquestador previo a un caso concreto.
2. **Reglas de transformación justificadas** (una, mínima) con fuentes/sumideros o energía latente; no asignar materiales reales/recetas o cambios de fase por intuición.
3. **Escala y heterogeneidad**: los coeficientes, pasos y unidades de H9, H11 y H14 corresponden a bancos diferentes; no son coherentes entre sí ni representan una geología natural compartida.
4. **Reanudación de la física completa**: los snapshots muestran materia, pero no necesariamente deformación interna MPM, campos de solver ni energía al tiempo de restaurar una simulación acoplada.
5. **Validación geomecánica independiente:** H12 no probó reposo natural y H13A ni siquiera ejecutó el solver; no adoptar PINNeAPPle ni GeoTaichi como núcleo.

## Decisión de trabajo prioritaria

**No continuar acumulando solvers o formatos sin un ensayo causal nuevo.** Para el próximo gate, delimitar **una sola transformación de materia y energía publicada** (por ejemplo equilibrio/conducción con fuente o sumidero físico medible) y probar si puede usar los inventarios existentes sin masa/energía fantasma. Antes de ejecutarlo, comparar bibliotecas existentes y formular presupuesto/invariantes; si el resultado exige más código propio o no aporta a mundo generativo, rechazarlo. No inventar transformación térmica ni forzar integración Landlab–FiPy: primero debe haber una razón fenomenológica y unidades compatibles.

**Prioridad secundaria condicionada:** ensayos de granularidad/deformación 3D sólo si el fenómeno elegido requiere ese detalle; comparar Matter (GMD2025, GPL-3), HydraxMPM (BSD3/JAX, pre-alfa) y GeoTaichi (GPL3) por licencias y evidencia antes de instalaciones. La selección no se deduce de cantidad de frameworks.

**Decisión de gobierno:** etapa0 selección provisional cerrada, etapa1 **ABIERTA**, etapas2–8 no iniciadas/cerradas formalmente. Mantener rama de investigación aislada, sin cambios a `main` ni NeuroLab. Ninguna arquitectura definitiva aprobada por usuario.
