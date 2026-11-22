# H-08a — preregistro de auditoría estática de rutas cerebrales/químicas C1

**Fecha:** 22/11/2026. **Tipo:** protocolo de comprobación de evidencia histórica P2, no experimento de aprendizaje. **Fuentes:** EXE original obtenido directamente de la carpeta Google Drive `neurolab`, hash SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`, 387072 B; genoma `dad1.gen` SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`, 10001 B. Ambos iguales a las fuentes E09h.1–h.6b. **Sin redistribuir bytes de archivos propietarios; sin ejecutar el juego.**

## 1. Objetivo y necesidad

Cerrar la laguna documental identificada en [H-07](H07_AUDITORIA_CADENA_TEMPORAL_Y_BLOQUEO_20261122.md): **qué rutas concretas del ejecutable pueden actualizar cerebro y química fuera del tick normal, y qué implican para atribución temporal del refuerzo**. No reiterar la reconstrucción ya validada de TIMER nominal 90ms, emisores, receptores, reacciones y genes; distinguir nuevos hechos de reconfirmaciones.

**Observación exploratoria previa a este protocolo:** un barrido manual de llamadas E8 en el desensamblado GNU objdump local identificó un tercer sitio de llamada directa a la rutina química `0x421E70` desde `0x40B089`, además de los dos sitios clásicos `0x405D32` y `0x407595`. Este hecho preliminar **no es resultado preregistrado ni prueba de ruta independiente**, y debe ser examinado con pruebas contra bytes directos y contexto de control de flujo.

## 2. Preguntas de auditoría

**H08a.1 — universo de llamadas directas.** Dentro de sección `.text` del PE32 de esa edición, enumerar los `call rel32` `E8` cuyos destinos sean `0x403BB0` (cerebro), `0x421E70` (química) o `0x4247B0` (mundo); contrastar el desensamblado de GNU objdump con cálculo independiente sobre los cinco bytes de cada callsite y tabla PE. Distinguir enumeración de llamadas directas desde un desensamblado de exhaustividad sobre código muerto, indirecto, virtual o ensamblado desalineado.

**H08a.2 — tercera llamada química.** Determinar qué información y contador recibe `0x421E70` en `0x40B089`, qué ocurre antes/después (marcadores de estado, inicialización, salida), si hay `brain tick` explícito en esa misma ruta, y qué puede concluirse sin ejecutar.

**H08a.3 — ruta regular y alternativa.** Verificar nuevamente con un oráculo *distinto* del informe anterior las llamadas y orden dentro de `0x405D20`, `0x407540`, `0x4075C0`, y los dos pases del mundo `0x4247B0`, y caracterizar específicamente **condiciones y valores de contador** cercanos a ellas. Señalar qué llamadas pueden omitir química/cerebro.

**H08a.4 — direcciones materializadas.** Buscar punteros literales de 32 bits little-endian a las rutinas de interés en las secciones del PE y separar datos de posibles instrucciones, sin interpretar ausencia como demostración de que no hay llamadas indirectas.

**H08a.5 — conclusión de crédito causal.** Contrastar el orden estático `brain→chemistry` / `chemistry→brain` con las inyecciones `chemicals_t` directas de `C1ContextBrain.step`, sin afirmar cadencia efectiva ni causalidad neuronal específica. Decidir: (A) se encontró una ruta adicional que debe integrarse en especificación histórica, (B) no se encontró y quedan lagunas indirectas, o (C) evidencia ambigua requiere traza dinámica. Se permite resultado mixto A+C.

## 3. Integridad y criterios de salida

- Hash exacto de EXE/GEN antes de leerlos; no usar archivo diferente por nombre. `objdump` para lectura estática y **script stdlib** que revalida PE, destinos `E8`, orden/offsets y ausencia/presencia de punteros literales. Comparar el output de herramienta con funciones propias, registrar versión de `objdump`.
- Guardar únicamente **direcciones, destinos, opcodes de 5 bytes relevantes, condiciones y hashes**, nunca binario completo ni desensamblado extendido en GitHub.
- Tests sintéticos adversariales: firma modificada, E8 apuntando a destino incorrecto, PE inválido/truncado y contadores/rutas inconsistentes; CI no tiene originales y no puede fingir que auditó el juego.
- Completar H-08a solo respecto a **rutas directas verificadas y su contexto de estado**; si faltan llamadas virtuales u otras vías, dejar H global ABIERTA.
- **No abrir modelos neuronales N, no consumir cohortes, no ejecutar Creatures ni modificar `main`/Nilo0.7.** PR#103 draft.

**Decisión posterior:** si la evidencia estática modifica el reloj causal de refuerzo, actualizar diagrama histórico y evaluar si vale diseñar un test de laboratorio H independiente. Si el límite es el comportamiento real/efectivo, **solicitar autorización explícita antes de ejecutar el programa original**, nunca extrapolar de WM_TIMER a tiempos del cerebro.
