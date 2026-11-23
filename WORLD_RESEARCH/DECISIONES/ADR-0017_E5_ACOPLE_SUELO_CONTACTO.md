# ADR-0017 — E5: primer acoplamiento causal entre suelo, geometría y contacto rígido

**Fecha:** 2026-11-22. **Estado:** decisión experimental reversible H31, NO aprobación E5 ni motor final.

## Brecha medida

[H29](../ETAPA_4_H29_RESULTADOS_SEMILLAS_TERRITORIO.md) validó el transporte sedimentario Landlab2.11 desde un owner de masa suelo y [H30](../ETAPA_4_H30_RESULTADOS_CONTACTO_TERRENO.md) validó una malla local rigid Bullet desde **el mismo artefacto WorldEngine**, pero en **escenas independientes**. Una misma fuente no equivale a acoplamiento: H30 usó alturas iniciales, **no terreno modificado por H29**.

**Preguntar ahora:** ¿la erosión/deposición que Landlab publica a un owner material puede cambiar la altura de una malla triangular reconstruida **solo a partir de ese owner**, causando un cambio observable del **contacto nativo de Bullet**, con masa total+salida y cuerpo sin fuentes ocultas?

## Soluciones existentes y mínima adaptación

1. **Landlab `PriorityFloodFlowRouter+SpaceLargeScaleEroder`**, MIT, CI H9/H18/H29; calcular transporte sin modificar ecuaciones.
2. **PyBullet3.2.7**, Bullet zlib, CI H17/H26/H30; reconstruir mesh local de cuatro posiciones nodales desde el relieve del propietario, lanzar una esfera y medir ray y contacto nativo sin implementar colisiones.
3. **`xarray.Dataset`**, owner de suelo, bedrock inerte, máscara core y materia/pose de cuerpo en la misma estructura; Landlab y Bullet usan solo vistas temporales durante sus pasos, antes de publicar candidatos. Uso de un adapter pequeño por proceso, **no** escribir motor general/orquestación autónoma.
4. Alternativas de acople completas **OpenFOAM, MuJoCo+Landlab, Chrono multifísica**: mayor costo/portabilidad y no resuelven el gate particular con menos complejidad; se reservarían para evidencia de necesidad en etapas posteriores.

**Elegir** prueba H31 de un **acoplamiento estrictamente unidireccional**: suelo/relieve Landlab→malla/contacto Bullet. No retropropagar fuerza del cuerpo al material ni afirmar conservación térmica o energética mecánica (fricción Bullet disipa). Cuerpos y suelo coexisten en propietario xarray desde el estado inicial, pero solo el solver Landlab actúa durante fase1; solo Bullet durante fase2. Dos relojes declarados, **sin equivalencia física temporal**.

## Control y salida

Dos semillas WorldEngine7321/8128, mismo NPZ y metros NOMINALES H29; K_sed=.1 vs K_sed=0 en cada semilla. Ambos usan la misma materia inicial y condición de frontera. Selección determinista del patch de 2×2 donde el cambio de altura **interpolada en el punto de prueba** por Landlab sea máximo en magnitud, con desempate. Crear dos superficies inicial/erosionada desde **el owner**, sin modificar mapa para probar contacto. Colisión Bullet en punto local y altura de primer contacto/reycast sensible a intervención K, no una imagen. Balance suelo+export+masa del cuerpo. [Prerregistro H31](../ETAPA_5_H31_PROTOCOLO_SUELO_CONTACTO.md).

**NO concluir:** ciclo bidireccional, coherencia agua/calor, trayectoria del mundo autónoma, carga granular de H26 sobre erosión, ni cierre de E5. Etapa6/7/8 y NeuroLab fuera de alcance. Preservar main y los tests originales.
