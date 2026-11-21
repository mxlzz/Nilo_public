# E09.02g.1 — preregistro de dendrita C1 completa (reglas + transición + fortaleza)

**21/11/2026. Se fija antes del código.** Objetivo: integrar el intérprete SVRule f.6, transición numérica f.3 y fortaleza f.4 en **una única operación sináptica de un tick** usando configuraciones realmente extraídas de `dad1.gen`. No simular metabolismo completo, conectividad total, scheduler de lóbulos o cuerpo.

**Fuentes primarias locales inspeccionadas:** `dad1.gen` original de CD, SHA-256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`; `Creatures.exe` SHA-256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`. Ambos archivos pertenecen al usuario y **no deben incluirse** en el repositorio. Todas las constantes indicadas aquí se extrajeron de los genes de lóbulo 6 (Decision) y 8 (Concept) y cotejaron con las instrucciones x86.

## Genética real de una dendrita por clase

| Campo | Decision clase0 excitatoria | Decision clase1 inhibitoria | Concept clase0 |
|---|---:|---:|---:|
| source_lobe | 8 | 8 | 0 |
| initial LTW min/max | 0/0 | 0/0 | 128/128 |
| initial strength min/max | 2/4 | 2/4 | 1/10 |
| migration_type | 1 | 1 | 2 |
| susceptibility_decay | 48 | 48 | 0 |
| STW_relax | 80 | 80 | 0 |
| LTW_rate | 128 | 128 | 0 |
| gain_strength_rate | 3 | 3 | 2 |
| lose_strength_rate | 5 | 5 | 3 |
| susceptibility_rule | `OUTPUT TRUE INPUT` | idem | vacía |
| reinforcement_rule | `CHEM0` | `CHEM1` | vacía |
| gain_strength_rule | `SUSCEPT TRUE CHEM0 TRUE STW` | `SUSCEPT TRUE CHEM1 TRUE STW` | `OUTPUT TRUE CHEM0` |
| lose_strength_rule | `CHEM2` | `CHEM3` | `CHEM1` |

Químicos asociados por receptor: Decision CHEM0=Reward49, CHEM1=Punishment50, CHEM2=DecASH1-53, CHEM3=DecASH2-70. Concept CHEM0=Reinforcement51, CHEM1=ConASH52.

## Semántica de ciclo bajo prueba

1. Capturar **una sola** `C1SVTable` al entrar en una dendrita: fuente input, output/estado del destino, químicos CHEM0..3, susceptibilidad, STW, LTW y fortaleza **anteriores al tick**.
2. Evaluar cuatro SVRules **contra esa misma instantánea**, conservando los resultados en traza. No recargar silenciosamente valores modificados entre reglas.
3. Ejecutar `c1_dendrite_tick.transition` con `susceptibility_rule_output` y `reinforcement_rule_output` para calcular susceptibilidad, STW y LTW.
4. Ejecutar `c1_strength.update_strength` sobre el estado ya actualizado y la fortaleza previa, pero con `gain_rule_output` y `lose_rule_output` calculados **sobre la instantánea antigua**.
5. Si strength llega a0, borrar estado sináptico y registrar `owner_neuron_cleared=True`: el x86 en VA0x4047C6–0x4047DE también borra estado y salida de neurona propietaria. No migrar aquí: se espera la etapa de red/selector f.5.
6. No administrar reward=±1 ni incluir objetivo correcto dentro del cerebro. Los CHEM0..3 se introducen como concentraciones **abstractas de entrada** hasta crear un modelo de bioquímica interna.

## Oráculos manuales preregistrados

1. Decision clase0, sus0/STW0/LTW0/strength4, output destino80, input fuente200, químicos CHEM0=255, CHEM2=0, tick1 → sus4, STW3, LTW0, strength4 (la gain_rule ve **sus antigua cero**, por tanto salida0).
2. Decision clase0 desde sus4/STW3/LTW0/strength2, output80, input200, CHEM0=255, tick3 → sus8/STW7/LTW0, strength**3** (gain_rate3, gain_rule devuelve **STW antigua3**, no la nueva7).
3. Decision clase0 con strength1, sus0/STW5/LTW0, output0/input0, CHEM2=1, tick5 → strength0, sus/STW/LTW0, owner_neuron_cleared=True.
4. Concept clase0, strength2, output destino100, CHEM0=51, tick2 → strength51. Tick3 con CHEM1=1 → strength50 (si CHEM0=0 y output>0).
5. Decision clase1 sin CHEM1 pero CHEM0=255 no refuerza su canal inhibitorio; con CHEM1=255 sí debe modificar STW bajo condiciones de susceptibilidad.
6. Verificar que alteraciones de C1SVTable durante tick no se permiten: dataclass inmutable; trazas reproducibles.
7. Validaciones de byte, 20 secuencias reproducibles, conservación de C1 genes/sinapsis previas y test negativo para señales químicas ausentes.
8. La estructura genómica original se verificó localmente; fixtures sintéticos en CI, sin distribuir GEN/EXE.

**Gate E09.02g.1:** todos los oráculos, sin confundir el resultado con una mente completa ni con dinámica bioquímica general. Una distinción pendiente es el orden global de neuronas/lóbulos y la propagación de OUTPUT antes/después de WTA.

**Siguiente:** E09.02g.2 microcircuito de cinco unidades con señales químicas y reglas sinápticas reales de C1, y comparación preregistrada vs E09e bajo las mismas entradas; si no aprende, registrar resultado negativo en vez de ajustar números. Después estudiar qué mínima función adicional permite aprendizaje sin un cuerpo.
