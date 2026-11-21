# Etapa 1 — H1: contrato de inventario material en contenedores existentes (sin paisaje ni física)

**Fecha:** 2026-11-21 · **Estado:** protocolo experimental previo al código. Etapa 0 superó gate de alternativas `DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md`, pero **ningún motor material ni esquema volumétrico está adoptado**. Etapa 1 se abre exclusivamente para este ensayo de estado.

## Propósito
Probar cómo representar una cantidad de materia en una región sin reprogramar física. Reutilizar `experiments/matter_v0.py` como **oráculo de invariantes ya probado** (8 tests), NO como motor definitivo. Los nuevos candidatos son bibliotecas de datos:
- **Landlab RasterModelGrid 2.11** (MIT): grilla científica 2D de nodos/celdas, campos con unidades, ya usada por hidrología/geomorfología H7–H14; candidata a estado ambiental de superficie, no a volumen universal.
- **xarray Dataset** (Apache-2.0): arrays multidimensionales etiquetados, metadatos de unidades, serialización NetCDF; candidato a representar cantidades por material y por nivel. No aplica por sí mismo exclusión, hidrodinámica, gravedad o conservación.

## Tres estados de prueba — NO leyes nuevas
1. Oráculo existente `MatterGrid(3,2)`, catálogo A densidad2 y B densidad1 en unidades del ensayo `kg/m³`, volumen de celda1m³. Cargas iniciales válidas, luego transferencia **manual** mediante `MatterGrid.transfer` ya existente. Se conserva masa por material, capacidad y snapshot determinista (baselines actuales).
2. Proyección sin pérdida a un **RasterModelGrid((4,5),dx=1m)** cuyos seis centros de celda corresponden a x=1..3,y=1..2; `mass_A` y `mass_B` en `at_cell` con unidad `kg`. Reconstruir MatterGrid usando valores y mapa explícito celda↔centro, comparar snapshot exacto, densidades y volumen derivado. Este ensayo no da al raster volumen 3D ni agrega física.
3. Proyección a un **xarray.Dataset** con dimensiones `(material,level,y,x)`, dos niveles (el segundo vacío en proyección inicial), masa kg, densidad kg/m³ y capacidad de cada celda por nivel 1m³. Reconstruir el oráculo del nivel0 y comparar snapshot exacto. Añadir manualmente material a nivel1 como fuente explícita y comprobar que ambos niveles conservan su identidad. Exportar/leer NetCDF sin pérdida y verificar unidades, versión y posiciones. **Este nivel extra es un test de representación, no simulación 3D.**

## Controles e invariantes preregistrados
- Igualdad exacta de masa A/B por posición y de balances entre `MatterGrid`, Landlab y xarray tras proyección; vectorización de estado no debe crear/destruir masa ni transformar materiales.
- Capacidad: `sum(mass_i/density_i) <= 1m³` por celda; fase/mezcla **no** se modela. Para xarray nivel1, capacidad se aplica por volumen independiente; la asignación de segunda capa debe ser una fuente inicial explícita y no ocurrir por render.
- Una entrada inválida de masa negativa o sobrecapacidad en arrays debe ser **rechazada por validación externa** o por `MatterGrid.from`; las librerías de contenedor no garantizan física, no afirmar lo contrario.
- La proyección Landlab depende de definir coordenadas (no índice plano supuesto) y no representa solapamientos/puentes/cavidades 3D.
- Reproducción determinista, rango de valores finito, huella y formato NetCDF medidos, coste de importación no usado como benchmark de un solver. Toda física futura deberá tener owner único y unidades definidas.

## Criterio de decisión
**H1 aprobada si** ambos contenedores preservan completamente la información del estado 2D que representan, xarray distingue dos capas sin colisión de nombres, NetCDF roundtrip preserva unidades/valores, y los valores corruptos son detectados por validador/contrato externo. **No** se elige xarray como motor ni se puede afirmar que todo el mundo es 3D; solo demuestra factibilidad del formato.

**Gate siguiente**: decidir si conviene usar Landlab como estado ambiental y xarray solo como interfaz/intercambio de campos o como sustrato material, comparando memoria/costo y capacidades frente a estructuras existentes (TPT/Sandspiel). No desarrollar leyes de caída/colisión nuevas; ya existen alternativas probadas. La parte volumétrica general requiere aún hipótesis de almacenamiento/exclusión y pruebas de capas superpuestas, no analogía automática con 2D.
