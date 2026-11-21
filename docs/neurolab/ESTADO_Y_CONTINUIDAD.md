# NeuroLab — estado verificable y protocolo de continuidad

**Última actualización del estado inicial:** 2026-11-20.  
**Línea base documentada:** protocolo v0.1.0 en rama `docs/neurolab-protocolo-20261120`, propuesto para revisión.  
**Ejecución experimental:** NO INICIADA.  
**Código del cerebro:** NO IMPLEMENTADO.  
**Autorización vigente documentada:** dejar el protocolo completo asentado; la ejecución e integración son pasos independientes.

## 1. Marcador canónico de progreso

| Campo | Valor inicial |
|---|---|
| Investigación | NeuroLab: mente neuronal aislada inspirada en Creatures 1 (1996) |
| Documento rector | [README.md](README.md) |
| Etapa actual | E00 — arqueología histórica |
| Siguiente subtarea exacta | **E00.01 — inventariar y verificar fuentes originales** |
| Última subtarea validada | Ninguna |
| Experimentos ejecutados | **0** |
| Runs con evidencia | **0** |
| Última corrida del cerebro | No existe |
| Estado de E00 | Pendiente |
| Estado del código | No creado |
| Integración con Nilo 0.7 | Ninguna |
| Bloqueos | Acceso y verificación de parámetros históricos aún pendientes |
| Decisiones nuevas pendientes | Fidelidad C1 vs adaptación mínima tras E00 |

**Regla:** nunca actualizar `última subtarea validada` sin prueba enlazada al commit, log/fixture y criterio de aceptación. Si se hace un paso pero no se logra evidencia suficiente, permanece en curso/bloqueado. No marcar «terminada» una etapa porque se produjo un texto sobre ella.

## 2. Estado por fase

| Fase | Estado inicial | Próxima subtarea | Requisito de cierre |
|---|---|---|---|
| E00 | Pendiente | E00.01 | G00 documentación y reglas con incertidumbres |
| E01 | No iniciada | E01.01 | G01 neuronas/sinapsis deterministas |
| E02 | No iniciada | E02.01 | G02 red seis neuronas trazable |
| E03 | No iniciada | E03.01 | G03 aprendizaje vs controles |
| E04 | No iniciada | E04.01 | G04 memoria STW/LTW contrastada |
| E05 | No iniciada | E05.01 | G05 efecto del refuerzo retrasado |
| E06 | No iniciada | E06.01 | G06 generalización a holdouts |
| E07 | No iniciada | E07.01 | G07 utilidad de migración sináptica |
| E08 | No iniciada | E08.01 | G08 dinámica interna caracterizada |
| E09 | No iniciada | E09.01 | G09 comparación integral y arquitectura mínima |

No avanzar en una fase solo porque exista su definición en este archivo.

## 3. Registro de cada intervención futura

Agregar una nueva sección fechada, sin borrar las anteriores:

```markdown
### YYYY-MM-DD — NL-LOG-0001
- Objetivo/subtarea: E00.01
- Estado antes: pendiente
- Trabajo efectivamente ejecutado:
- Artefactos creados/modificados (ruta, SHA y enlace):
- Fuentes y evidencia, con grado de certeza:
- Pruebas y resultados reales (incluidos fallos):
- Limitaciones / hechos no comprobados:
- Criterio de aceptación aplicable:
- Resultado: validado | en curso | bloqueado | fallido | descartado
- Decisión y motivo:
- Siguiente subtarea exacta:
- Estado después:
```

Si se trabaja en PR o branch no fusionado, indicarlo explícitamente: un cambio en una rama experimental **no está en `main`**.

## 4. Procedimiento obligatorio para retomar desde otro chat

1. Abrir el [issue #102](https://github.com/mxlzz/Nilo_public/issues/102) y seguir su enlace a este protocolo.
2. Leer este archivo en la rama/commit donde efectivamente se trabaja, **no asumir que `main` lo contiene** si no hubo merge.
3. Verificar en GitHub el head de branch/PR y últimos commits; no inferir estado por conversaciones anteriores.
4. Leer la siguiente subtarea E##.## y sus dependencias en [ETAPAS_00_09.md](ETAPAS_00_09.md).
5. Consultar [FUENTES_Y_RECONSTRUCCION.md](FUENTES_Y_RECONSTRUCCION.md) y [PROTOCOLO_EVALUACION.md](PROTOCOLO_EVALUACION.md) pertinentes.
6. Confirmar permiso y alcance de esa intervención (documentar, programar o ejecutar pruebas). No interpretar la orden «continuá» como autorización general para modificar el motor Nilo 0.7 o fusionar ramas.
7. Ejecutar la mínima unidad verificable; registrar artefactos y fallos.
8. Actualizar exactamente un estado canónico, enlazar issue/PR/commit/ensayo y dejar la siguiente subtarea.
9. Si hay discrepancia entre archivo e issue, investigar qué fuente es más reciente y verificada; **no sumar ambos estados automáticamente**.
10. Reportar en el chat: hecho comprobado, evidencia, incertidumbre, siguiente paso.

**Prompt de continuidad sugerido (información de entrada, no autorización implícita):**
> Continuá NeuroLab según mxlzz/Nilo_public: issue #102 y docs/neurolab/ESTADO_Y_CONTINUIDAD.md. Verificá la rama/PR real, identificá la siguiente subtarea pendiente, ejecutá solo lo autorizado y dejá trazas, pruebas y siguiente paso sin saltar puertas de aceptación.

## 5. Política de decisiones

No tomar como decisiones confirmadas las propuestas del asistente. Una decisión de diseño se registra con:
- ID (NL-DEC-0001), fecha, estado `propuesta/aceptada/rechazada/reemplazada`;
- contexto, opciones y evidencia;
- criterio explícito de adopción;
- consecuencias y costes;
- quién la aprobó, si corresponde;
- reversibilidad y pruebas de regresión.

**Decisiones confirmadas por conversación hasta ahora:**
- La nueva investigación debe centrarse en comprender C1 antes de ampliar el sistema.
- El primer objeto experimental es la mente aislada, sin cuerpo/mundo y sin LLM.
- El programa debe seguir pasos y validaciones, con documentación suficiente para retomarlo.
- Dejar asentado el plan actual en GitHub, sin implementar todavía código de Nilo.

**Propuestas todavía NO aprobadas:** utilizar un controlador tabular, adoptar una ecuación propia, añadir instintos, elegir un LLM externo, construir un cuerpo/mundo, crear un agente desarrollador autónomo, integrar a la 0.8.

## 6. Control de versiones y fusiones

- Protocolo en rama docs específica, PR en borrador hacia `main` para revisión; el merge se deja para decisión posterior.
- Las ejecuciones futuras deben usar ramas separadas con commit por unidad verificable; conservar baseline.
- Nunca mezclar documentación de fidelidad histórica con código experimental sin etiquetar divergencia.
- Ante cambios del protocolo, actualizar versión, motivación, impacto sobre evaluaciones anteriores y migración de IDs.
- No borrar datos de ejecución negativos; si un archivo grande no debe entrar a Git, mantener índice de artefacto verificable con suma SHA y ubicación.

## 7. Registro de intervenciones

**NL-LOG-0000 — 2026-11-20**
- Subtarea: preparación documental del protocolo, externa a E00.
- Se registró el procedimiento integral para E00–E09, metodología y fuentes a verificar.
- No se ejecutó E00.01; no hay resultados ni capacidad neuronal demostrada.
- Siguiente acción verificable: E00.01.
