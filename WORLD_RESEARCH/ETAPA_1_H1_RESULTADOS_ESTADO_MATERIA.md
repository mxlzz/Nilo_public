# Etapa 1 — H1: resultados del contrato de estado material

**Fecha:** 2026-11-21. **Estado:** H1 APROBADA como prueba de representación, **no** como selección definitiva de arquitectura.
**Plan preregistrado:** `WORLD_RESEARCH/ETAPA_1_H1_PROTOCOLO_ESTADO_MATERIA.md`.
**Script:** `WORLD_RESEARCH/experiments/probe_e1_state_representations.py`.
**CI verificable:** https://github.com/mxlzz/Nilo_public/actions/runs/44959062997 (**SUCCESS**; 8 tests de `matter_v0.py` preexistentes también pasaron).

## Condiciones
El estado de referencia es `MatterGrid(3,2)`, con materiales A de densidad 2 y B de densidad 1, capacidad por celda de 1 m³, inventarios iniciales y transferencia manual por el método existente. Ningún solver de física, transporte espontáneo o creación de material ha sido construido.

## Resultados
- `RasterModelGrid((4,5))` de Landlab 2.11.0 expuso exactamente **6 celdas** y dos campos de masa material en kg; el contrato explícito de coordenadas celda↔centro permitió reconstruir **bit a bit** el snapshot de MatterGrid.
- `xarray.Dataset` 2026.9.0 con dimensión `(material, level, y, x)`, 2 materiales y 2 niveles, reconstruyó exactamente el nivel 0 con mismo snapshot y masa. El segundo nivel se conservó independiente y se insertó **manualmente como condición inicial** una masa A de 0.3 kg; no se simuló movimiento vertical.
- Inventario de referencia por componente: **A=1.1kg, B≈0.6kg**. Con nueva carga explícita en nivel superior, A total ≈1.4kg.
- NetCDF exportado (motor scipy): **964 bytes**, roundtrip exacto de valores, nombres, unidades, versión y niveles.
- Cantidades negativas y sobrecapacidad rechazadas por **validador del contrato basado en MatterGrid**, no por xarray ni Landlab de forma automática.
- SHA-256 del snapshot original: `321c0d02b2be89a7d003cbcb32a6e6dc3e89d9d923c53189101c7b731af50c36`.

## Dictamen
**H1 validada:** bibliotecas existentes representan sin pérdida el inventario 2D y xarray permite una dimensión explícita de niveles. **No** demuestra colisiones, materiales generales, soporte volumétrico continuo, puentes/cavidades, conservación automática por los contenedores ni un mundo tridimensional. Landlab sigue siendo una buena interfaz para campos ambientales superficiales. El hecho de guardar capas en xarray no es suficiente para seleccionar xarray como estado único del motor.

## Siguiente gate
H2 investigará **propiedad única del estado e intercambio sin duplicación**, no nuevas leyes. Verificar si `RasterModelGrid.add_field(...,copy=False)` puede mantener referencia compartida a un array existente de xarray/NumPy, si la mutación en ambos sentidos es visible, si el `copy=True` del control sí separa el estado y si guardar/cargar exige restablecer referencias. No sostener que nombres de campos iguales garanticen interoperabilidad. Etapa 1 ABIERTA.
