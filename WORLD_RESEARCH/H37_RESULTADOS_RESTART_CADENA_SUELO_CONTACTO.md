# H37 — Causalidad de suelo reanudado hasta contacto Bullet, sin reloj ficticio

**2026-11-22 local. H37 APROBADA bajo todos los gates preregistrados.** [Protocolo previo](H37_PROTOCOLO_RESTART_CADENA_SUELO_CONTACTO.md), [CI 45094662094 — SUCCESS cuatro jobs independientes](https://github.com/mxlzz/Nilo_public/actions/runs/45094662094) y ejecutores `experiments/probe_h37_extended_landlab_producer.py`, `probe_h37_sequential_landlab_resume.py`, `probe_h37_sequential_bullet_contact.py`. Proveedores originales WorldEngine revision`3b9113ecfad884cab4b32081d138a15e6262ada8`, Landlab2.11 Python3.13, PyBullet3.2.7 Python3.11. No se modificaron leyes de sedimento ni cuerpo/colliders, no se introdujo un integrador físico nuevo ni se ajustó K.

## Qué se comparó realmente

Dos terrenos WorldEngine raw seeds7321 y8128, cada uno con **K_sed=.1 y control K=0**, mismo inventario inicial de suelo921.600.000kg y cuerpo2kg en reservorio, misma fuente/geom nominal/contabilidad total921.600.002kg.

1. Job WorldEngine produjo raw hashes canónicos, como H29/H31.
2. Job Landlab calculó baseline6 pasos continuos dt0,2 y checkpoint después de paso3, con una extensión para control K0 seed8128; los otros3 casos reutilizaron H33 sin cambios.
3. Nuevo runner Landlab reanudó estrictamente pasos4,5,6 desde checkpoint; los **cuatro casos** reprodujeron arrays de suelo, salida de materia, clocks y hashes de owner t6 **bit a bit**. Máximo saldo de masa al reanudar1,1920929×10⁻⁷kg, tolerancia0,09216kg. K0 no exportó material y mantuvo stock original.
4. Runner Bullet Python3.11 leyó **ambos** estados t6 (continuo y reanudado) y ejecutó contacto720 pasos `dt=1/240s` con cuerpo idéntico sobre **la malla derivada del owner**, usando el mismo patch seleccionado por algoritmo H31 desde diferencia entre K0 y K.1, **sin reoptimizar según los resultados de Bullet**. First contact, conteo de contactos, arrays del body/soil y SHA de owner final fueron idénticos bit a bit entre continuo y reanudado para las cuatro combinaciones.

**Dos relojes, no uno:** `landlab_t_bench=6×0.2` de simulación geomorfológica **NO se interpreto como segundos**; `bullet_t_s=720/240=3s` después del paso6. Relieve WorldEngine/posiciones `m_nominal` siguen sin calibrar: el resultado de H37 prueba conectividad lógica y repetibilidad física de cada proveedor en una **secuencia**, no evolución natural simultánea ni cartografía métrica de un lugar real. Ver [auditoría dimensional](AUDITORIA_UNIDADES_Y_RELOJES_PRE_CICLO_INTEGRADO.md).

## Métricas decisivas

**Seed7321:** patch(10,10), descenso nominal superficie por erosión **−0,0812199272m**, primera altura de contacto sobre suelo original13,409623m y sobre suelo erosionado13,328396m; desplazamiento de primer contacto **−0,0812273215m**, mismos datos en camino reanudado. Contactos K0 546 y K.1 543. Stock sedimento exportado K.1 **13.637.273,698kg**. SHA final conjunto tras cuerpo K.1 `b947b6874ac58b88c1eee919c8b5ad02ba594d0285fba7311bb0c42c5f8ae357`.

**Seed8128:** patch(10,16), descenso nominal superficie por erosión **−0,0707744464m**, contacto original25,717064m y erosionado25,646084m; cambio de primer contacto **−0,0709806729m**, idéntico tras restart. Contactos K0 546 y K.1 543. Exportado K.1 **13.657.955,999958kg**. SHA final conjunto K.1 `1bd60a80c94219851102a2fe1463c0c163faefc4e13279e25562230856872b6d`.

En ambas semillas el signo y magnitud de contacto responde a erosión, no a edición geométrica artificial; los casos K0 no erosionan. Cada Bullet final NetCDF recuperó el SHA original. `failed_preregistered_gates=[]`, las4 jobs SUCCESS.

## Conclusión y decisión

**Avance real:** el mismo owner canónico de suelo y cuerpo permite que **un reinicio físico antes de completar erosión** desemboque exactamente en el mismo contacto posterior, comparado con una historia sin reinicio; no depende de memoria compartida entre los motores. Esto agrega una prueba de cadena causal **end-to-end** que no se podía inferir automáticamente solo de H33 y H34 por separado.

**Aún no demostrado:** reanudar Bullet **dentro de esa misma cadena de malla erosionada** (H34 se limitó a dos cuerpos), sincronización del reloj `landlab_t_bench` con segundos Bullet, respuestas del suelo a impactos del cuerpo, flujo real de agua/temperatura, actualización de deformación 3D, fuentes geológicas o un mundo vivo con autonomías. E7 continúa abierto (H36 NO aprobada para soporte duradero); E5/E6 mantienen sus cierres experimentales mínimos reversibles, con deuda de integración temporal real.

**Siguiente inversión:** no perseguir ajustes de impacto o salidas downstream H32 solo para aprobar. Definir un **ciclo material mínimo multiescala y reanudable** con políticas de relojes separadas y estado observable, primero como benchmark completo de las capacidades H31/H33/H34/H35/H37, evitando backend propio, UI, LLM y arquitectura innecesaria. Solo después retomar tests de funciones E7 con estructuras que interactúen en el **mismo mundo** y nulos condicionados. `main` y NeuroLab intactos.
