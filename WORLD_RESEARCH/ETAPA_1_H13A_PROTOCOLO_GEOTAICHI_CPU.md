# Etapa 1 — H13A. Prueba de viabilidad del solver independiente GeoTaichi

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO PREVIO, no código ni CI de este hito ejecutados todavía. Etapa1 ABIERTA. Documentación relacionada: ADR-0007_GATE_MPM_3D.md, ETAPA_1_H12_RESULTADOS_REPOSO_MPM.md.

## Justificación y pregunta
H11 reveló deformación en PINNeAPPle, pero H12 no pudo aprobar soporte físico independiente del floor clamp: 61,11% de partículas exactamente en z=1,5dx con fricción30°. Antes de acoplar este solver a materia persistente, se necesita un **proveedor independiente** para contraste. GeoTaichi dispone de capacidades MPM/DEM y publicación científica revisada (Computer Physics Communications, doi:10.1016/j.cpc.2024.109219). Licencia GPL-3.0: no se copia código suyo a este repositorio.

**H13A (solo viabilidad, no física comparativa):** ¿es reproducible en CPU de GitHub Actions, con dependencias razonables y usando íntegramente sus propias pruebas, una escena 3D de materia deformable y la validación de un caso geométrico inválido?

**Alternativa:** si el upstream exige entorno pesado, GPU, compiladores o dependencias no justificadas para ensayos mínimos, registrar incompatibilidad/costo y reevaluar selección. No programar sustituto.

## Reutilización y alcance

Upstream GeoTaichi, commit exacto público fijado 6cae5a6998c4f0be9f59b5615bf2e26857df824f, GPL-3.0. Checkout en directorio temporal de GitHub Actions, no en main del proyecto; taichi==1.7.0 en Python3.11, CPU y tests del propio upstream, sin instalar GUI ni código propio del solver. Se documentarán versiones/importaciones y efectos de dependencias.

**Dos ensayos nativos exclusivamente:**
1. tests/integration/mpm/test_sparse_grid_explicit.py::test_sparse_grid_explicit_3d_solid — MPM 3D de casos LinearElastic/NeoHookean propios del proyecto con velocidad/posición finita y recursos de grilla activos.
2. tests/integration/mpm/test_direct_mpm_backend.py::test_direct_backend_rejects_particles_outside_the_background_grid — control adversarial upstream que rechaza puntos fuera de grilla, si es compatible con el mismo entorno.

No editar los tests. Su primer fallo se clasifica (entorno/compilación/geométrico/numeral) y **no** se considera refutación de constitutivo de arena porque esos tests NO simulan arena Drucker–Prager.

## Gate y límites
**Aprobado como baseline técnico** solo si ambos tests originales se ejecutan con éxito en CPU, a versión fijada y tiempo medido. Esto habilita *proponer* H13B con arena bajo gravedad, no demuestra colapso de columna ni explica H12. **No aprobado** si falla instalación/import/runtime; registrar fallo y costo, sin modificar upstream. Permitido un ajuste mínimo de dependencias comprobadas, documentado antes de repetir; no instalar paquetes pesados por inercia. No se incorpora motor definitivo ni se cierra ninguna etapa del plan.

Fuentes: https://github.com/Yihao-Shi/GeoTaichi y https://doi.org/10.1016/j.cpc.2024.109219
