# E0.4 — Protocolo previo: sedimentos, ecología y realimentación

**Fecha:** 2026-11-21 · **Estado:** plan de experimentos, no arquitectura aprobada.  
**Base:** `ADR-0002_LANDLAB_PRIMERO.md` y `AUDITORIA_ETAPA_0_EXPERIMENTAL_2026-11-21.md`.

## Comprobación de alineación
Objetivo vigente: territorio inicialmente generado y autónomamente cambiante; investigar procesos ambientales que comparten materia/estado con reglas verificables, sin confundir mera variación con emergencia. Sigue prohibido desarrollar nuevas leyes por inercia o tocar NeuroLab. **El siguiente trabajo pertenece todavía a etapa 0.**

## Alternativas existentes revisadas ANTES de los tests
1. Landlab `Space` y `SpaceLargeScaleEroder`, modelo sedimentario publicado de Shobe et al. (2017): https://doi.org/10.5194/gmd-10-4577-2017 ; este último expone `sediment__deposition_flux`, `sediment__erosion_flux` y salida acumulada de sedimentos. https://landlab.csdms.io/generated/api/landlab.components.space.space_large_scale_eroder.html
2. Ejemplos nativos de LANDLAB: `docs/source/tutorials/landscape_evolution/space`; ecología `docs/source/tutorials/ecohydrology/`. Los auxiliares de ecología existen en https://github.com/landlab/tutorials/blob/next/ecohydrology/cellular_automaton_vegetation_DEM/Ecohyd_functions_DEM.py , aunque faltaban en la carpeta inspeccionada del repo principal.
3. Código científico de ecohidrología reproducible: https://github.com/landlab/pub_nudurupati_etal_wrr . No copiar la implementación sin comprobar licencia/versiones; leer contratos antes de enlazar.
4. Sharma y Ehlers (2023), **modelo específico de erosión influida por vegetación y precipitación**, con código/datos Zenodo https://doi.org/10.5281/zenodo.8033782 y paper https://doi.org/10.5194/esurf-11-1161-2023 . En particular: difusión con `K_d=K_b exp(-alpha*V)` y fluvial mediante Manning/partición de esfuerzo cortante, no sustituibles uno por otro sin justificación.

## H7 — Deposición y balance sedimentario REAL
**Pregunta:** ¿`SpaceLargeScaleEroder` produce deposición explícita y conserva inventario sedimentario en condiciones controladas?

- Ejecutar en GitHub Actions (Python compatible) la API pública, registrar versión, semilla, dt, parámetros, frontera y área.
- Construir una cuenca con bordes cerrados y salida definida, suelo móvil inicial, roca madre `K_br=0`, fines `F_f=0`, porosidad `phi=0`: así no hay fuente de sedimentos nuevos por erosión de roca.
- **Ablación:** `K_sed=0` manteniendo resto de variables → ningún flujo sedimentario ni variación de `soil__depth`.
- **Intervención:** `K_sed>0` → erosión (`sediment__erosion_flux` positiva), deposición (`sediment__deposition_flux` positiva) y flujo sedimentario.
- Medir por paso `sum(delta soil_depth × area)` frente a `V_leaving_riv` devuelto por la API y `vol_SSY_riv` (por diseño debe ser 0 porque `K_br=F_f=0`), con residual absoluto/relativo. **Nunca llamar 'balance cerrado' a un dominio con salida; incorporar la descarga al inventario.**
- Registrar explícitamente si crecen las cotas/espesores en algunos nodos: `deposition_flux>0` no prueba ganancia neta de espesor si entrainment simultáneo es mayor.
- **Criterio:** campos finitos, no negativos, control nulo, flujos de depósito/erosión positivos; residual del inventario < 1% del total movilizado si API y definición geométrica permiten computarlo, caso contrario no aprobar cierre de balance y auditar mapeo de fronteras.

## H8 — Feedback eco-geomorfológico basado en publicaciones
**Pregunta:** ¿existen componentes y ecuaciones publicadas suficientes para conectar dinámicamente humedad→biomasa/cobertura→erosión sin inventar un coeficiente?

**Primera acción:** revisar código de Landlab e investigaciones para escoger exactamente cómo variar erosividad/difusividad (distintas leyes para ladera y cauce). Establecer unidades, localización nodo/celda, resolución, timestep y propietarios del estado. **No implementar un feedback ad hoc hasta esta revisión.**

**Prueba futura:** dos escenas con misma topografía y lluvia pero vegetación inicial distinta, incorporando cobertura calculada por `Vegetation`, y control de desacoplamiento (`alpha=0` solo para difusión en laderas si se adopta la ecuación publicada). Comparar erosión y evolución vegetal en repetición temporal. La ecuación `K_d=K_b exp(-alpha V)` proviene de Sharma y Ehlers 2023, Eq. 3, no es una fórmula nueva de esta investigación. El caso de erosión fluvial debe seguir su propia formulación publicada, no compartir un coeficiente sin justificación.

## Gates
- E0.4-H7 puede ejecutarse ya; el archivo de ensayo debe ser solo arnés sobre Landlab.
- H8 **bloqueado a investigación y especificación** hasta verificar fuente, parámetros y compatibilidad de mallas/tiempo.
- Si H7 falla: inspeccionar límites del modelo/arnés sin manipular las aserciones para 'hacer pasar' un resultado; registrar medidas de diagnóstico y fallo.
- Tras H7: informe de evidencia y ADR de continuidad actualizado. **No** declarar etapa 0 cerrada sin H8 y reproducción del ciclo completo.

## H7b — Plan de control adicional de acreción neta (añadido ANTES de la prueba)

**Motivo:** H7 mostró `deposition_flux>0` y presupuesto de sedimentos consistente a precisión de máquina, pero en el paisaje con capa inicial homogénea **ninguna celda ganó suelo neto**. Una deposición local positiva no equivale a acreción cuando simultáneamente se erosiona más material.

**Intervención delimitada:** misma cuenca, mismos parámetros del solver, pero una zona receptora inicialmente sin aluvión (capa móvil inicial 0 en el tercio inferior del terreno) y una zona emisora con espesor 0.6 m aguas arriba. No se habilita erosión de roca (`K_br=0`). El modelo ya existente debe transportar suelo desde arriba y depositar una fracción en nodos originalmente desnudos; no se codifica una regla ad hoc de deposición.

**Control negativo:** repetir el perfil de suelo inicial con `K_sed=0` y demás condiciones iguales: no debe haber transporte, deposición ni acreción. **Criterio de éxito:** al menos un nodo receptor gana espesor neto, hay flujo deposicional positivo, y el balance (almacenado + exportado) cierra dentro de 1%. Si no ocurre, conservar el resultado como límite/falsación del escenario, no forzar el valor.
