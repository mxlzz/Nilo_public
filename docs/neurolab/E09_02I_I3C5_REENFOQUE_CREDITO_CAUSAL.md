# E09.02i-I3c.5 — reenfoque de investigación a crédito causal diferido

**2026-11-21. Estado: DISEÑO, NO NUEVO EXPERIMENTO NI CAMBIO DE PARÁMETROS.** Depende del [I3 científico negativo](E09_02I_I3_RESULTADO_NEGATIVO.md), [I3c.4, comparación químicamente apareada](E09_02I_I3C4_RESULTADO_QUIMICA_APAREADA.md), [I3c.4a, recambio](E09_02I_I3C4A_RESULTADO_TURNOVER.md) y [I3c.4b, ventana LTW](E09_02I_I3C4B_RESULTADO_GATE128.md). Meta principal: G05 atribución temporal de recompensa, no acumulación de mecanismos.

## Conclusión para decidir

- El nuevo migrador funciona: 3377 Type1 aceptadas en Y con química idéntica a B; sin embargo el holdout de Y/B/F permanece ~50% incluso con inversión. Añadir más neuronas por intuición no responde a esa falta de aprendizaje.
- En red migratoria Y la vida de una conexión entre migraciones sucesivas suele rondar20 ticks, mientras la regla LTW solo actualiza cada128. En cada fase de 20 semillas hay apenas **1/240** contactos con STW positiva en gate; cero LTW final.
- No alcanza con decir que la migración perjudica el aprendizaje: el control B SIN migración tampoco mejora. Sus algunas ganancias LTW incluyen estados de fortaleza0, cuyo significado funcional e histórico todavía requiere auditoría.
- El control original de refuerzo DIRECTO y el tabular CON ORIGEN explícito (I3) funcionan mucho mejor, pero los controles no tienen exposición igual. La insuficiencia puede mezclar **credit assignment**, amplitud química, consolidación y fortaleza.

## Alternativas ya disponibles

1. Reusar las pruebas de distractores/counterfactuales de E09g.10b y I3b.1 para medir si el refuerzo recae en sinapsis de la acción causante o del distractor. No escribir otro mecanismo de asignación de crédito antes de cuantificar.
2. Reusar el puente químico con pares B/Y/F del I3c.4, manteniendo química y decisiones/aportaciones de entorno como datos observados, pero no usar semillas900..919 para validar una solución seleccionada.
3. Usar el algoritmo histórico de migración actual y los oráculos C1 ya auditados; no modificar todavía SVRules, tasas40, dosis80, cantidad de conceptos ni temporizador lógico.

## Próxima unidad exacta

**I3c.5a: preregistro de prueba de trazabilidad de crédito en las conexiones, ANTES de implementar.** Aislar primero la **distribución de refuerzo por contexto** a una decisión previa y el tiempo de llegada del precursor (d0 vs d1/2/3) desde un mismo estado/clon, sin introducir mapping al cerebro. Reportar: fracción de refuerzo efectivo en conexiones de contexto objetivo versus distractor, evento sin acción, y supervivencia STW/LTW (cuando sean elegibles) con observador que no cambie la simulación. Abrir un nuevo conjunto de semillas nunca utilizadas 200..419, 800..919 ni 0..199, congelado con tamaño y criterio antes de ejecutar.

**Cautela:** entregar el mismo precursor en otro instante garantiza igual dosis total pero NO la misma concentración química por tick, ya que cambia el decaimiento. No confundir efecto total del momento con aislamiento de amplitud; incluir control con exposición equiparada sólo si se puede construir sin filtrar acción verdadera al cerebro. Las métricas primarias deben contrastar causalidad y rendimiento de decisiones, no sólo aumento de STW.

**I3c.5b: auditoría histórica de strength0**, previamente a cualquier intervención que ignore conexiones agotadas: verificar si C1 real sigue procesando una dendrita de fortaleza0, cuándo se descarta de la suma de señales y cuándo el adaptador debe reconectar; no corregir a ciegas el cerebro reducido.

Sólo tras resolver esos dos contratos diseñar un ensayo confirmatorio con cohortes nuevas de aprendizaje sostenido y reversión; preregistrar criterios antes de código/observación. G05/G09/G00-H abiertas. El modelo A base y Nilo0.7/main no se modifican.
