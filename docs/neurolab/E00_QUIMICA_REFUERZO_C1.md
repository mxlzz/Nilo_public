# E00-H04 — reacciones químicas que conectan necesidades y aprendizaje (C1 original)

**21/11/2026.** Evidencia: inspección directa del `dad1.gen` de 10001 bytes suministrado por el usuario (SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`) y verificación con [artículo de Grand/Cliff/Malhotra](https://www.cp.eng.chula.ac.th/~vishnu/gameResearch/AI/creatures.pdf). **No se sube el archivo binario.**

## 1. Estructura de las reacciones genéticas C1

Se localizaron **58 registros** de reacción de tipo/subtipo **1/2** en la referencia de CD, cada uno con **9 bytes de cuerpo** después de marcador `gene` (4 bytes) y cabecera (6 bytes). El cuerpo se interpreta como ocho pares cantidad/identificador químico para dos reactivos y dos productos, más un byte de tasa:

```text
cantidad_A, químico_A, cantidad_B, químico_B,
cantidad_C, químico_C, cantidad_D, químico_D, tasa
```

Esto coincide con el esquema de reacción **iA + jB ⇒ kC + lD** del artículo original. La ecuación de velocidades **no** queda reconstruida a partir de estos campos; depende del motor y del tamaño de concentraciones. No simular velocidad exacta sin corroboración.

## 2. Circuito demostrado en registros concretos del dad1.gen

Los siguientes ejemplos representan **bytes derivados de genes originales** (números de gen base0, no reproducción del archivo completo):

| Gen | Reactivos | Productos | Tasa genética |
|---:|---|---|---:|
| 57 | 1 × Pain Increase (17) | 1 × Pain (1) + 1 × Punishment (50) | 8 |
| 71 | 1 × Pain Decrease (33) + 1 × Pain (1) | 1 × Reward (49) | 8 |
| 111 | 1 × Reward (49) | 1 × Reinforcement (51) + 1 × Reward Echo (54) | 16 |
| 112 | 1 × Punishment (50) | 1 × Reinforcement (51) + 1 × Punish Echo (55) | 16 |

**También se identificaron trece relaciones** de aumento de necesidades (químicos 17–29) que producen Punishment 50, y trece pares de disminución (químicos 33–45) que consumen una necesidad y producen Reward49. Algunas otras reacciones pueden modular estas sustancias; la tabla no pretende ser toda la bioquímica.

Nombres de sustancias: [C1 Chemical List, transcripción del Genetics Preview Kit](https://creatures.fandom.com/wiki/C1_Chemical_List).

## 3. Cadena funcional

```text
aumento de drive → Punishment (50) ──→ Decision: CHEM1 refuerza clase inhibitoria
                                        ↘ Reinforcement (51) → Concept: CHEM0

disminución de drive → Reward (49)  ───→ Decision: CHEM0 refuerza clase excitatoria
                                        ↗ Reinforcement (51) → Concept: CHEM0
```

Además se producen químicas Echo (54 y55) más duraderas que indican recompensa/castigo reciente, y compuestos **ConASH (52), DecASH1 (53), DecASH2 (70)** que regulan pérdidas de fortaleza de dendritas. Véase [mapa neuroquímico](E00_MAPA_NEUROQUIMICO_C1.md).

**No es una ecuación de aprendizaje completa:** para traducir las concentraciones a cambios de susceptibilidad/STW/LTW/fortaleza faltan parámetros de paso, relajación y estados reales del motor. La inyección de refuerzo desde el laboratorio es una simplificación legítima solo si se declara como tal.

## 4. Qué cambia para el diseño del experimento mínimo

Los experimentos E09.02c y d usaban un evaluador que fijaba D0 o D1 como «correcto» e inyectaba un score +1/-1. Eso sirve para medir reversibilidad pero no reproduce el origen de refuerzo del Norn.

El próximo prototipo que justifica nuestro objetivo de una **mente sin cuerpo ni mundo** debe poder:
- mantener al menos un estado interno de necesidad abstracta;
- recibir señales discretas del banco de pruebas que **aumenten o disminuyan ese estado**;
- convertir sus cambios en dos químicos **distintos** Reward/Punishment, y éstos en Reinforcement transitorio;
- usar los químicos para actualizar sinapsis según las reglas genéticas documentadas, sin introducir una función «acción correcta» en el cerebro;
- registrar la procedencia de cada variación y controlar que esto no se convierta en una tarea de maximización impuesta artificialmente.

**No desarrollar un mundo ni representar comida, calor, materiales, mapas o necesidades humanas** por este experimento. El drive puede ser un número.

## 5. Pruebas de evidencia y límites

- [ ] Parser automatizado de reacciones C1 comprueba las cuatro muestras con oráculos calculados independientemente.
- [ ] Conteos y rangos reales sobre el genoma de usuario (local; sin guardar archivo).
- [ ] Comparación de genes químicos originales vs parche de envejecimiento sin confundir cambio del último gen con aprendizaje.
- [ ] Modelado del tick químico cuando se confirme su ecuación temporal; no inventarla.

**G00-H:** mejor especificado, pero todavía abierto en la ejecución exacta de las reacciones y en el motor neuronal.
