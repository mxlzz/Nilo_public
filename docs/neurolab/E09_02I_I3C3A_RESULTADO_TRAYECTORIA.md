# E09.02i-I3c.3a — resultado negativo de trayectoria sin recompensa

**2026-11-21.** [Preregistro anterior al runner](E09_02I_I3C3A_TRAYECTORIA_PRE_REGISTRO.md), [runner](../../experiments/neurolab/e09_i3c3a_migration_stress.py) y [GitHub Actions #44959905616](https://github.com/mxlzz/Nilo_public/actions/runs/44959905616): **success, 5/5 tests**. Artefacto completo por tick **neurolab-i3c3a-no-reward-migration-traces**, ID14729381171, retención hasta 2027-02-19.

## Diseño y resultado conservados

20 semillas nuevas 800..819, **256 ticks por semilla y condición**, cuatro contactos. B sin migración y B+ con migración, mismo wiring balanceado, mismos estímulos y químicos neuronales exógenos CHEM0/1=24 alternados cada8 ticks, **sin precursores, cuerpo, metabolismo, recompensa ni supervisión**. RNG migratorio Python local como fuente explícita N, NO CRT original. Checkpoint en tick128: **reprodujo exactamente todas las transiciones** hasta256 en ambos brazos.

| Conteo en 20 semillas | B | B+ |
|---|---:|---:|
| Elecciones D0 | 2576 | 2576 |
| Elecciones D1 | 2544 | 2544 |
| Contactos agotados al finalizar | **0** | **0** |
| Migraciones aceptadas | **0** | **0** |
| Semillas con migración | **0/20** | **0/20** |
| Draws de migración consumidos | 0 | **0** |
| Puerta destinatario inactivo | Sin migrador | 10.240 |
| Puerta no disconnected dendrite | Sin migrador | 10.240 |

**Conclusión:** el entorno sintético preregistrado no agotó ninguna dendrita, luego no hay recurso a reubicar. B y B+ fueron iguales neuronalmente: la posibilidad técnica de migración no implica que el régimen la active espontáneamente. El resultado NEGATIVO no es prueba de que el mecanismo falle o de que nunca migre con química de refuerzo. No modificar químico24, tasas, seeds ni topología para forzar un resultado positivo.

**Siguiente I3c.4:** probar un calendario de reacciones/precursores del protocolo I3 en nueva cohorte y cuatro ramas B (sin migración, recompensa propia), Y (migración, mismo calendario B), P (migración, recompensa propia) y F (sin plasticidad, mismo calendario B). Así se discrimina impacto mecánico y divergencia on-policy. G05/G09/G00-H ABIERTAS.
