# E09h.6b — fuente de cadencia nominal C1: Windows WM_TIMER

**Fecha:** 2026-11-21. **Resultado:** período **solicitado** al sistema operativo identificado estáticamente como 90 ms; **cadencia efectiva de un Norn NO medida**.

## Evidencia autenticada

- EXE PE32 original, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7, 387072 bytes. Inspección local sobre sus bytes: **17 firmas de instrucciones, 7 llamadas directas, 6 campos de tabla de mensajes** correctos; importación por IAT de USER32.SetTimer (VA 0x44114C) y USER32.KillTimer (VA 0x441144).
- [Preregistro](E09_H_06B_CADENCIA_PRE_REGISTRO.md), [auditor reproducible](../../experiments/neurolab/e09_historical_timer_audit.py), [tests sintéticos](../../experiments/neurolab/tests/test_e09_historical_timer_audit.py), [JSON de evidencia reducido](resultados/e09h6b_cadencia_original.json).

## Cadena de evidencia

1. La rutina de inicio 0x411F50 llama USER32.SetTimer en 0x411F63 con parámetros obtenidos de bytes x86: HWND de objeto global 0x43F08C +0x20, ID1, intervalo **0x5A = 90 ms** y callback NULL. La rutina 0x411F70 cancela ID1 en el mismo HWND mediante KillTimer en 0x411F7F.
2. El mapa de mensajes MFC en .rdata, VA 0x433988, registra **WM_TIMER = 0x113** y su puntero al manejador 0x418960 (misma entrada de seis DWORD). El manejador 0x418960 lee el objeto mundial global y en 0x418966 llama **0x4247B0**, el loop auditado en h6a.
3. Otros invocadores directos 0x424C98 y 0x426894 también llaman 0x4247B0, bajo condiciones de estado y pausa de ventana. En 0x424C4A / 0x424CD9 y 0x426846 / 0x4268C9 se llama a las rutinas para cancelar/restablecer el timer.
4. **Hay otro SetTimer de 500 ms** en 0x40D078, asociado a otra ventana/objeto. No se tomó como reloj del mundo ni se confundió con la llamada de 90 ms.
5. Junto con h6a, cada invocación del mundo utiliza fases 0..4 de índice de criaturas y stride4, y la criatura puede omitir cerebro, química o conducta según su estado. Por tanto **90 ms NO equivale a 90 ms por tick cerebral**, y tampoco corresponde extrapolar simplemente a 450 ms por Norn.

## Alcance de las puertas

- **G-H6-CLOCK-NOMINAL: VERIFICADA**, exclusivamente como intervalo pedido a USER32 y enlace estático WM_TIMER→world tick.
- **G-H6-CLOCK efectiva: ABIERTA**. Windows puede retrasar o combinar mensajes; las actualizaciones están condicionadas por pausa, estado de ventana, callback alternativo y distribución de criaturas. No se ejecutó el juego ni se midieron tiempos observados, así que **no** se afirma frecuencia real constante.
- **G-H6-FLOW (h6a):** condiciones de rutas regular y alternativa verificadas en subconjunto de llamadas directas; otros callbacks podrían existir.
- **G00-H/G05/G09:** abiertas; no se emuló el Norn ni se resolvió crédito causal.

## Decisión y próximo trabajo

Se dispone de una **cadencia nominal histórica respaldada**, suficiente para etiquetar hipótesis temporales de laboratorio, pero no para declarar fidelidad conductual o sincronización real. Antes de unificar el cerebro y la química en una simulación histórica, hace falta distinguir el contador de mundo, fases de criaturas y frecuencia efectiva/condicional por criatura mediante auditor adicional o una traza original controlada.

**No ejecutar Creatures sin autorización específica, no publicar EXE/GEN, mantener PR #103 draft y Nilo 0.7/main intactos.**


**Verificación CI posterior:** [run #44949141624](https://github.com/mxlzz/Nilo_public/actions/runs/44949141624), **success: 374 tests y 2 expectedFailure históricos**. La identidad de importaciones y mapeo WM_TIMER fue revalidada localmente sobre el EXE original; la CI solo prueba el auditor con un PE sintético. No implica un intervalo efectivo medido.
