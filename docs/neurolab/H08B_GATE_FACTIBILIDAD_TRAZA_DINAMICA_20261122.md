# H-08b — puerta de factibilidad antes de observar dinámicamente Creatures 1

**Fecha:** 22/11/2026. **Estado: PLAN DE FACTIBILIDAD, NO PREREGISTRO FINAL NI EJECUCIÓN AUTORIZADA.** Se deriva de [H-08a, evidencia auténtica](H08A_RESULTADO_RUTAS_ORIGINALES_20261122.md), [H-07](H07_AUDITORIA_CADENA_TEMPORAL_Y_BLOQUEO_20261122.md) y los preregistros [H6a](E09_H_06_SCHEDULER_PRE_REGISTRO.md)/[H6b](E09_H_06B_CADENCIA_PRE_REGISTRO.md). **No se ejecutó, instaló ni instrumentó el juego.**

## 1. Pregunta concreta

¿Cuál es el **orden y latencia efectiva observable** entre eventos de actualización cerebral, química, recepción y señales conductuales para **una criatura determinada**, bajo estados que activan ruta regular y alternativa? La medición de `SetTimer(90ms)` por sí sola no responde a esta pregunta ni determina crédito sináptico.

**Resultado que cambiaría una decisión:** constatar o refutar en ejecución que el refuerzo derivado de `Reward49/Punishment50` llega a los loci CHEM de Decision/Concept tras una separación de etapas que depende de la ruta; si fuese consistente, esa secuencia sería candidato a especificación H de un ensayo aislado. Sin esa relación, no justifica nuevas pruebas G05.

## 2. Dependencias antes de diseñar la prueba

- **Autorización específica** para ejecutar una copia legal del juego, con consentimiento sobre las herramientas de observación; la autorización general para investigar documentos o binarios estáticos no cubre ejecución del programa original.
- **Entorno Windows compatible** o virtualizado y componentes completos de la instalación, no solo `Creatures.exe` y `dad1.gen`. La comprobación local actual no encontró Wine/Wine64/DOSBox/QEMU, y ningún archivo adicional de instalación fue requerido o descargado. No prometer ejecución en el contenedor.
- La observación debe distinguir tres invocaciones químicas directas y dos de brain tick ya verificadas, así como su ejecución indirecta si existiera; las direcciones solo valen para EXE SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`.
- Seguridad y licencias: no subir ni distribuir el EXE/GEN completo en repositorio público; no ejecutar binarios de terceros ni instalar depuradores sin que el usuario apruebe el método; capturar solo metadatos mínimos y valores derivados relevantes.

## 3. Protocolo propuesto, sujeto a factibilidad y aprobación

1. **Validar entorno y proveniencia**: ejecutar solo la edición hasheada en un ambiente controlado con instantánea/reversión; documentar archivos necesarios y limitaciones de herramienta, sin modificar el equipo principal salvo consentimiento.
2. **Prueba mínima del cronómetro**: registrar timestamps monotónicos de entradas a `0x4247B0`, de decisiones `0x403BB0` y de química `0x421E70` para una criatura identificada por puntero estable, y contadores `+0x2C20` antes/después. Observar callbacks de `WM_TIMER`, rutas de pausa y ausencia de ticks; no forzar el supuesto de períodos constantes.
3. **Separar rutas** con sus direcciones `0x407583`/`0x407595`, `0x405D32`/`0x405DAF`, y química durante construcción `0x40B089`. Registrar estado `+0x2CBC`/`+0x2CCC` y condiciones de entrada/salida. Conservar también eventos omisos; no analizar únicamente secuencias que apoyen la hipótesis.
4. **Muestra química mínima**: cuando resulte técnicamente viable, registrar para un único individuo concentraciones 49/50/51 y bytes CHEM0/1 Decision, CHEM0 Concept antes y después de receptor, reacción y cerebral, con cuidado de no confundir puntos de copia `nominal` con cambios ocasionados por premio.
5. **Controles**: al menos un período sin criatura activa, otro en pausa y otro con criatura activa; prueba repetida desde estado reproducible. Registrar versión Windows, frecuencia de timer observada, número de muestras y pérdidas por depurador; contraste contra el diagrama H-07 sin reajustar hipótesis a posteriori.
6. **Salida y decisión**: distribuir únicamente resultados derivados, resúmenes temporales y checksums, no memoria completa del proceso. Si solo pueden observarse contadores globales pero no un Norn identificado, no declarar G-H6-CLOCK efectiva.

## 4. Criterios de detención y alternativas

Si falta el conjunto de archivos del juego, un sistema Windows compatible, consentimiento de ejecución o un observador fiable, **detener H-08b sin improvisar un estimador temporal**. La vía alternativa es mantener H como reconstrucción estática limitada y no utilizar su reloj como valor verificado de refuerzo en microC1.

**No se solicita instalar nada en esta fase** ni se preparan instrucciones de explotación del ejecutable. No se abre nueva línea N; G05/G09 permanecen abiertas. PR103 draft; `main` y Nilo0.7 intactos.
