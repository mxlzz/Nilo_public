# E09.02f — informe forense del motor cerebral C1 (ejecutable aportado)

**Fecha:** 2026-11-21. **Estado:** f.1 (aritmética), f.2 (decay/relax/LTW), f.3 (transición parcial de dendrita) y f.4 (fortaleza y desconexión) **implementadas y verificadas contra oráculos estáticos**. La reconstrucción completa de migración, el reloj global y la química todavía **NO** están validados. No es una emulación completa.

## 1. Procedencia inequívoca

- Archivo aportado: `Creatures.exe` extraído por el usuario de la imagen de instalación del CD de Creatures 1.
- **SHA-256:** `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`.
- Tamaño: **387.072 bytes**. Formato: Windows PE32 x86, Windows GUI, 6 secciones.
- Metadatos del PE: timestamp de enlace 1997-08-06 19:48:28 UTC; `VS_FIXEDFILEINFO FileVersion/ProductVersion 1.0.0.1`. Esto no demuestra automáticamente que sea idéntico al primer ejecutable de 1996.
- **Método:** inspección estática exclusivamente, sin ejecutar/instalar ni guardar el ejecutable de terceros en el repositorio. Se identificaron clases `CBrain`, `CGenome`, `CBiochemistry`. `CBrain` reserva 0xC8C=3.212 bytes y construye 16 estructuras internas de lóbulo de 0xC8=200 bytes (capacidad; el `dad1.gen` inspeccionado contiene **9 lóbulos/952 neuronas nominales**).

## 2. Operaciones observadas

| Módulo / dirección virtual del binario | Comportamiento inferido directamente del código máquina | Entrega |
|---|---|---|
| 0x4032E0–0x4034B9 | Construcción de redes a partir de genes | Investigación genética |
| 0x403F2F–0x403F8F | Dendrita: `(output*STW)>>8`, suma limitada a255, atenuación `>>8` y señal conjuntiva AND | [E09f.1](../../experiments/neurolab/c1_runtime_math.py) |
| 0x403FC2–0x4040B6 | Intérprete de SVRule; PLUS/MINUS saturados por operación, TIMES `>>8` | E09f.1 |
| 0x4040B6–0x404110 | Salida neuronal: `max(0,state-threshold)` | E09f.1 |
| 0x4042C9–0x404306 | Susceptibilidad sube 4 cuando la regla supera el valor anterior; si no, decaimiento controlado por tasa | [E09f.3](../../experiments/neurolab/c1_dendrite_tick.py) |
| 0x40442B–0x4044A1 | Refuerzo modulado por susceptibilidad afecta STW | E09f.3 |
| 0x4044A1–0x4044E8 | STW se relaja hacia LTW mediante helper de tasa | E09f.2/f.3 |
| 0x4044EF–0x40451B | LTW se acerca ±1 unidad a STW en ticks divisibles por tasa genética | E09f.2/f.3 |
| 0x419E40 / 0x419E90 | Decay y relax a partir de dos tablas de 32 valores, datos VA0x43A0E8 y 0x43A168; index `rate>>3`, máscara temporal | [E09f.2](../../experiments/neurolab/c1_decay_math.py) |
| 0x40451E–0x40467A | Regla de ganancia de fortaleza asigna nuevo valor si supera fortaleza previa, en ticks habilitados | [E09f.4](../../experiments/neurolab/c1_strength.py) |
| 0x40467A–0x4047E2 | Regla de pérdida reduce fortaleza en 1; al llegar a cero limpia susceptibilidad/STW/LTW y marca conexión agotada | E09f.4 |
| 0x4048CC–0x404911 | Competencia neuronal winner-takes-all | Evidencia de mecanismo histórico |
| **0x404A80 / 0x404B90** | **Dos rutinas de reasignación de dendritas**: una selecciona nuevas fuentes entre candidatos y rechaza duplicados; la segunda tiene restricciones adicionales sobre agrupación de fuentes | **Solo investigación estática inicial; NO reimplementadas** |

**Límites:** las direcciones dependen exactamente del ejecutable hasheado. No se midió el comportamiento durante ejecución ni se verificó equivalencia con otros builds de C1; por tanto, el informe usa «observado/inferido del flujo estático», no «comportamiento empírico del juego». Las SVRules químicas son un circuito adicional, no reemplazables por etiquetas de acción correcta.

## 3. Diferencias medibles respecto de los experimentos NeuroLab anteriores

| Situación | Modelo experimental antiguo | Cálculo derivado del ejecutable |
|---|---:|---:|
| Decision STATE80+TYPE0 240-TYPE1 200 | 120 | **55** por saturación intermedia |
| Dos dendritas con outputs100/80, pesos128 y atenuación255 | 90 | **89** por escala binaria256 |
| Salida de neurona estado80/umbral24 | Convención según módulo | **56** |
| STW al primer refuerzo desde cero | 26 en variante E09e, regla propia E04 | **3** cuando susceptibilidad sube de 0→4, salida química255 y tick1; LTW permanece0 |
| STW decay con tasa80 para valor200 | Aproximación genérica por tick | **194 en tick7, 200 en tick6** |

Los resultados de E09e **siguen siendo verdaderos para su propio algoritmo experimental**, pero no pueden transferirse numéricamente al motor C1. No cambiar sus métricas, parámetros o criterios retrospectivamente.

## 4. Evidencia de test

- [Pruebas de aritmética f.1](https://github.com/mxlzz/Nilo_public/actions/runs/44929478194).
- [Pruebas de tablas de decaimiento f.2](https://github.com/mxlzz/Nilo_public/actions/runs/44929737314).
- [Pruebas de transición de dendrita f.3](https://github.com/mxlzz/Nilo_public/actions/runs/44930063295).
- [Pruebas de fortaleza/agotamiento f.4](https://github.com/mxlzz/Nilo_public/actions/runs/44930221183), **188 tests; success, 2 expected failures** correspondientes a criterios científicos negativos E09c y E09d mantenidos intactos. Los errores corregidos durante el desarrollo fueron oráculos de fixture, no modificaciones de la regla aprendida.

Pre-registros: [f.1](E09_02F_EJECUTABLE_C1_PRE_REGISTRO.md), [f.2](E09_02F_02_DECAIMIENTO_PRE_REGISTRO.md), [f.3](E09_02F_03_SINAPSIS_PRE_REGISTRO.md), [f.4](E09_02F_04_FORTALEZA_PRE_REGISTRO.md).

## 5. Siguiente trabajo y restricciones

**E09.02f.5 — migración genética/neuronal**, con foco en comprender x86 `0x404A80` (Decision-style) y `0x404B90` (Concept-style), entradas, condiciones de duplicados, reinicialización de LTW/strength, elección de fuente y semilla/RNG. **No reusar el algoritmo simplificado de E07** como si fuera el histórico. Antes de codificar, decodificar direcciones y parámetros y preregistrar pruebas con ejemplos independientes.

Luego: **E09.02g** microcerebro de cinco unidades que use cálculo neuronal y sináptico corregido, comparar con E09e en tareas con semillas nuevas y evaluar si sigue aprendiendo/revirtiendo. El objetivo no es replicar 952 neuronas por tamaño sino descubrir qué funciones mínimas son necesarias.

**G00-H (motor C1 exacto), G05 (crédito causal diferido) y G09 (mente integrada) permanecen abiertas.** El usuario **no necesita enviar otro archivo** para proseguir la inspección estática; lo pendiente es la reconstrucción, no falta de fuentes.
