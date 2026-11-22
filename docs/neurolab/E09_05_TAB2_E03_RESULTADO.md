# NeuroLab — E09.05-TAB2: resultado de equivalencia exacta E03 ↔ tabla 2×2

**22/11/2026 · prueba implementada después de [preregistro](E09_05_TAB2_E03_PRE_REGISTRO.md).** [Código de control independiente](../../experiments/neurolab/e09_binary_tabular_equivalence.py), [tests](../../experiments/neurolab/tests/test_e09_binary_tabular_equivalence.py), [GitHub Actions run #45028560329](https://github.com/mxlzz/Nilo_public/actions/runs/45028560329) **SUCCESS**, commit probado `0e8d2670a7d4d9085ac7e6925aaeaae47ab4cd4a`, [artefacto JSON+SHA #14756592272](https://github.com/mxlzz/Nilo_public/actions/runs/45028560329/artifacts/14756592272), ZIP digest GitHub SHA256 `1e3c8adf39e630e9f190dc13981da93f4c3d7362023c5403fa211d99aaa2e2ba`. El ZIP de Actions es temporal; el runner, tests y preregistro están versionados.

## Evidencia obtenida, verificada en logs de CI

- Cuatro pruebas **OK**: replay original de 20 semillas con reversión, equivalencia de puntuaciones manuales, empate/abstención/saturación y rechazo explícito de entradas fuera del dominio.
- **20 semillas originales E03 (0..19, desarrollo)**, sin tocar semillas confirmatorias.
- **10.480 comparaciones** de ambas entradas legales en estados alcanzados; **3.200 comparaciones adicionales de holdout** sin entrenamiento.
- **5.200 actualizaciones** pareadas durante entrenamiento original (100×20) e inversión (160×20) sin reset de pesos.
- **0 discrepancias** en acciones, dos scores neuronales, vector completo de cuatro pesos y contador de ensayos. Comparador tabular reimplementado de forma independiente; los modelos reciben el mismo premio, nunca la etiqueta correcta.

## Fundamento y alcance

El circuito E03 posee neuronas E0/E1→C0/C1→D0/D1. **Cada ensayo reinicia el estado neuronal** y corre exactamente tres ticks de propagación; entrada A=(255,0) o B=(0,255). Con umbral0, decay255 y conexiones E→C de peso255, el único Concept activo en tick2 vale255; en tick3 las dos Decision reciben precisamente los dos pesos de la fila correspondiente. No hay estado residual entre ensayos. Una tabla con cuatro pesos inicializados por la misma semilla y actualización de +/−16 sobre el peso elegido ejecuta el mismo cálculo. Si ambos pesos de fila son0, los dos se abstienen; ante empate positivo, ambos eligen D0. La equivalencia resulta por inducción sobre los 260 eventos de entrenamiento y se extiende a toda secuencia legal de este mismo modelo.

**No** se afirma equivalencia para input mixto, amplitudes parciales, dinámica neuronal continua sin reinicios, química C1, refuerzo retrasado, nuevos conceptos o patrones cambiantes. Esta prueba es una **auditoría de representación y necesidad de complejidad**, no una replicación independiente de plasticidad biológica.

## Interpretación y decisión

- La puerta original **G03** permanece superada para la tarea episódica prevista: E03 aprende y revierte por feedback mejor que pesos congelados. No reinterpretar sus valores originales como inventados.
- El ensayo **no demuestra ventaja funcional exclusiva de seis neuronas** frente a una tabla con los mismos dos estímulos/cuatro pesos/dos acciones. La comparación con el control **congelado** prueba plasticidad, pero por sí sola no prueba superioridad arquitectónica.
- Junto con [E09.05-TAB1 E06](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md), establece que las dos demostraciones asociativas originales positivas E03 y E06 **se reducen exactamente a tablas bajo sus dominios predefinidos** (4 pesos en E03, 8 en E06). E07 tampoco supera LRU; E05 crédito temporal sigue fallando, E04 y E08 son fenómenos aislados.
- **Decisión local E09.05:** NO implementar una integración E03+E06 con el único objetivo de recuperar su desempeño previo. No se ha probado aún un cerebro neuronal integrado con capacidad no tabular. Una continuación de N exige un desafío realmente discriminante, no agregar nodos por analogía con Norns.

**E09.05-TAB2:** validación completa del contrato específico de equivalencia; **G09 global sigue ABIERTA**. Nilo0.7, `main`, química/genética C1 y 8 slots E09 no modificados.
