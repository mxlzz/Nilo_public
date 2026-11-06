# Correcciones del run 2026-11-05/06 · candidato Nilo 0.7.1

**Base estable:** v0.7.0. **Rama:** `work/0.7.1-autonomia-run1`.
Las observaciones provienen de una única corrida Gemini, dos snapshots consecutivos:
[primero](ETAPA_23_CORRIDA_REAL_01_07.md) y
[continuación](ETAPA_23_CORRIDA_REAL_02_07.md). No hay experimento
controlado sobre la mejora hasta ejecutar una partida nueva.

## Priorización

1. **Recreación tras cierre — implementado en rama, pendiente de CI.**
   `completar` con proyecto ausente o ID distinto del activo nunca crea
   otro proyecto. Detecta cierre anterior por ID/título exacto, registra razón,
   conserva evidencia y deja explícitamente disponible `nuevo`. Un rechazo
   viejo se descarta al retirar el proyecto correspondiente. Tests sintéticos
   reproducen el patrón observado.
2. **Criterio de cierre combinado y pruebas de agua — pendiente.**
   La conjunción explorar/identificar/recolectar requiere evidencias físicas
   específicas; una medición de agua recogida con recipiente no debe
   ignorarse si verifica el hecho, ni admitir una simple narración.
3. **Reintentos de cierre sin nuevas pruebas — pendiente.**
   Reducir las 445 reiteraciones de la sesión sin imponer objetivos
   ni completar automáticamente un proyecto.
4. **Exploración sin frontera elegida — pendiente.**
   Distinguir falta local de frontera de agotamiento del territorio
   y orientar con el mapa conocido, sin revelar terreno oculto.

La rama no modifica `VERSION`, `main` ni el release 0.7.0.
Cada corrección pasa por pruebas de regresión antes de fusionarse.
No se subió ninguna SQLite personal, conversación ni clave.
