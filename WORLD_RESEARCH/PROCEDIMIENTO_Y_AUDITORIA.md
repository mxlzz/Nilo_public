# Marco de gobierno y auditoría — Mundo autónomo

Fecha de adopción: 2026-11-21
Estado: obligatorio para la investigación de mundo. Excluye NeuroLab, cerebro, Norns, genética neuronal y LLM.
Rama de trabajo provisional: `research/world-foundations-2026-11`; NO integrar en `main` de Nilo sin una decisión posterior explícita.

## Jerarquía de documentos

1. **Objetivo y restricciones confirmadas:** `BASES_Y_HOJA_DE_RUTA.md`, apartado 2; no se cambian unilateralmente.
2. **Plan de investigación versionado:** `BASES_Y_HOJA_DE_RUTA.md`, etapas 0–8; modificable solo con justificación, análisis de impacto y registro de decisión.
3. **Evaluación de alternativas / decisiones:** `DECISIONES/ADR-0001_REUTILIZACION.md` y siguientes; cada opción debe tener evidencia, incertidumbre y motivación.
4. **Experimentos:** archivos `ENSAYO_NN_*.md`, código y pruebas; nunca sustituir hipótesis por una demostración visual.
5. **Evidencia verificable:** enlace al commit, CI, resultados, semillas, configuración, versión y controles negativos.

## Auditoría retrospectiva 2026-11-21

**Incumplimiento detectado:** la etapa 0 (análisis de alternativas) no había concluido cuando se creó `experiments/matter_v0.py`. Es un **spike exploratorio** no autorizado como base definitiva.

**Segundo desvío:** el plan describía densidad como derivada, mientras que el código la almacena como parámetro y deriva el volumen ocupado. Esta diferencia no es necesariamente errónea, pero demuestra que la especificación física aún no está aprobada.

**Tercer desvío:** el documento inicial decía «sin implementación» pese a existir posteriormente un prototipo y pruebas. Este documento prevalece en estados hasta que se actualice la hoja de ruta.

**Resultado real:** se verificó ejecución correcta de 8 pruebas de invariantes en GitHub Actions: https://github.com/mxlzz/Nilo_public/actions/runs/44942005067. No hay prueba de gravedad, dinámica, emergencia, rendimiento o viabilidad del modelo físico. No dar por ejecutadas pruebas fuera de evidencias conservadas.

**Estado del ensayo 01:** válido solo como prueba de contrato mínimo de datos; **no validado** como motor del mundo. Congelar expansión de `matter_v0.py` hasta cerrar decisión de reutilización.

## Gate obligatorio antes de cada cambio

Se prepara una ficha breve que responda, por escrito, a las ocho preguntas:

1. **¿Qué objetivo confirmado justifica esta etapa?** ID de requisito y etapa del plan.
2. **¿Qué hipótesis falsable se probará?** También resultado alternativo plausible.
3. **¿Existe algo reutilizable?** Comprobar soluciones preexistentes relevantes antes de desarrollar, más importante en un componente nuevo.
4. **¿Por qué esta técnica?** Registro de decisión con alternativas descartadas y condicionantes (licencia, interfaz, costo, complejidad, madurez).
5. **¿Cuál es el mínimo alcance?** Sin agregar capacidades «por si acaso».
6. **¿Cuáles son las pruebas definidas ANTES de implementar?** Unitarias, integración, control negativo/ablación, reproducibilidad, indicadores de causalidad, rendimiento cuando corresponda.
7. **¿Qué evidencia de ejecución se conservará?** Commit, CI, semilla, parámetros, métrica, resultados y límites de interpretación.
8. **¿Cuál es la conclusión de auditoría?** Aceptar / corregir / descartar / investigar más; cotejo con objetivos y cambios de plan si hacen falta.

No se inicia una etapa siguiente si la actual carece de un dictamen de puerta de salida. Un resultado positivo de CI es **necesario pero insuficiente**.

## Regla de evolución del plan

Si aparece mejor herramienta, evidencia que invalida el enfoque o nueva restricción:
- documentar nuevo hecho, su origen y qué hipótesis afectó;
- proponer modificación acotada y el costo de oportunidad de mantener el plan;
- conservar versión anterior en Git;
- validar invariantes de etapas anteriores cuando cambian contratos;
- no presentar el desvío como si hubiese sido planificado desde el inicio.

Las hipótesis técnicas reversibles pueden cambiar por evidencia. Los objetivos confirmados por el usuario no cambian por iniciativa del implementador.

## Regla de reutilización

Por defecto preferir **usar, adaptar o combinar soluciones existentes** antes que reconstruir su funcionalidad. Desarrollo propio solo si se acredita mediante pruebas una brecha material, incompatibilidad de licencia, extensión desproporcionada o riesgo técnico mayor. Una biblioteca de referencia puede inspirar criterios sin copiar código.

El trabajo específico y pequeño (por ejemplo interfaces o adaptadores) puede requerir código propio incluso si se reutiliza un motor. Eso no justifica crear uno desde cero.

## Estado de avance al cierre de auditoría

- Etapa 0: **abierta, parcialmente investigada; decisión de motor pendiente de prueba comparativa ejecutada**.
- Etapa 1: **spike experimental en cuarentena; no aprobado como base del proyecto**.
- Etapas 2–8: **no iniciadas**.
- Bloqueo actual: prueba de encaje técnico y licencias de al menos dos candidatas sobre los mismos casos de uso.
- Próximo trabajo autorizado por el plan: documentación, inspección de alternativas, definición de benchmarks y pruebas limitadas de adaptación; **no** desarrollar nuevas leyes físicas en el prototipo existente.
