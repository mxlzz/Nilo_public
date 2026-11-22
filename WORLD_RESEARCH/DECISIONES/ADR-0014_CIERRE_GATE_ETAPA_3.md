# ADR-0014 — Cerrar provisionalmente gate de Etapa3, sin adoptar motor mundial

**Fecha:** 2026-11-22. **Estado:** ADOPTADO PARA LABORATORIO y REVERSIBLE.

## Decisión

Tras [auditoría explícita de criterios originales E3](../AUDITORIA_CIERRE_ETAPA_3_2026-11-22.md), **cerrar provisionalmente solo la formación de agregado granular rígido local** en etapa3. No aprobar evolución abierta, estructuras minerales ni un mundo ambiental integrado.

## Fundamento y evidencia

- [H26](../ETAPA_3_H26_RESULTADOS_DEPOSITO_GRADUAL.md) [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45085243163) con125 esferas3,125kg en suelo sin paredes, alimentación gradual que evita interpenetración, Bullet3.2.7 sin física propia: componentes de contactos positivos73/92 en dos semillas, montículos0,724/0,894m, desplazamiento post-emisión mediano0,0031/0,0043m y velocidad P90<0,08m/s. Ablación de fricción produjo monocapa y cero contactos grano-grano, con masa/owner/replay consistentes.
- [H28](../ETAPA_3_H28_RESULTADOS_NULO_MCMC.md) [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45085820365) produjo256 nulos casi excluyentes por semilla con2 cadenas y gates de mezcla, manteniendo alturas/contaje radial. Redes geométricas observadas107/101 vs P95 de nulo31/33, lo que supera margen previsto de≥10 sin modificar prueba. El fracaso instrumental de H27 (inserción secuencial sin suficientes muestras) **permanece** como NO APROBADO, y H28 no reemplaza sus resultados a posteriori.
- Ensayos negativos H19/H21/H22/H23/H24/H25 explican por qué no son suficientes la deposición heredada de cuenca, mezcla phase-field, liberación masiva o simplemente más tiempo. No borrar fracasos y no alterar el plan.

## Límites no negociables

- Etapa3 demuestra solamente **pila de partículas rígidas soportada durante un intervalo finito** con superficie base y punto de emisión prescritos, no que se generen cuevas, bosques, ríos, rocas u organismos.
- Nulos H28 son configuraciones geométricas con MCMC correlacionada y tolerancia numérica de2mm; el p empírico es un **estadístico de rango**, no evidencia de independencia perfecta ni equilibrio mecánico nulo.
- Los resultados no garantizan conservación de energía mecánica/termal durante impactos; la masa total se conserva, pero no un único estado de todos los solvers.
- H26 persiste el estado final, **no** reservorio+estado del solver durante el proceso; identidad por orden de emisión en owner final en vez de source IDs merece decisión posterior para Etapa6.
- E3 debe reabrirse si alguna integración posterior demuestra que los montículos solo se sostienen por artefacto del modelo o si la invariancia material/identidad falla al mantener causalidad conjunta.

## Siguiente etapa autorizada

Abrir **Etapa4** como investigación de **generador de condiciones iniciales**, no integrar nuevo motor físico. Primero leer/validar los bridges experimentales ya existentes WorldEngine→Landlab antes de implementar; comparar su madurez, dependencia/costo y reproducibilidad contra alternativas nativas de Landlab/arrays. La salida de E4 exige estados válidos para leyes E2, múltiples semillas, sin balances negativos ni estructuras finales prescritas. **No mover `main` ni NeuroLab.**
