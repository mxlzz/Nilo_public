# NR01.04-A y NR01.06 — resultados completos de desarrollo y decisión STOP (22/11/2026)

**Estado: cohorte de desarrollo EJECUTADA / VALIDADA TÉCNICAMENTE. NR01.05 (confirmación): NO EJECUTAR con esta configuración. NR01.06: cierre negativo/limitado de la hipótesis seleccionada.**

## 1. Integridad y evidencia

- [Plan NR01](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md), [desafío preregistrado](NR01_02_PREREGISTRO_DESAFIO_20261122.md), [decoder preregistrado](NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md), [cohorte preregistrada antes de correr](NR01_04A_PREREGISTRO_DESARROLLO_20261122.md).
- Commit ejecutado: `9c16605a938c59a6c27a803897005bfb5bce349a`. [GitHub Actions #45049703202](https://github.com/mxlzz/Nilo_public/actions/runs/45049703202): **SUCCESS**, tests previos y ejecución, artefacto subido.
- **20 semillas desarrollo 23000..23019**, A/B × ocho brazos = **320 condiciones**, todas reportadas; **0 excepciones**. Replay23000 coincide con el primer [piloto](NR01_03D_RESULTADO_PILOTO_DESARROLLO_20261122.md). Se verificó identidad de cintas por SHA256 entre brazos por mundo/familia, recompensa posterior a acción y lectura sin modificación de pesos en test.
- **Nunca se abrieron confirmación24000..24019 ni históricos1400..1419.** No existe prueba independiente confirmatoria.
- Resultado completo: JSON con **320 filas**, JSONL incrementales, huellas de entradas, checkpoints y costes, [artefacto Actions ID14765345436](https://github.com/mxlzz/Nilo_public/actions/runs/45049703202/artifacts/14765345436) (retención90d).
- Respaldo permanente adicional: ZIP en [Google Drive / neurolab](https://drive.google.com/file/d/1CKUVUpAtBGfRV2QveMueeH6AOvCT_HtP/view?usp=drivesdk), ID `1CKUVUpAtBGfRV2QveMueeH6AOvCT_HtP`, verificado por metadatos en la carpeta `1lUxvBeYDhrAXM619kq6CTOm1nWFq1jE8`; **ZIP SHA256 `3c0c662eb7685b9d9fe3f36f97bb72f9c5dad002d4811e54b1a2b920c1f9b040`**, JSON interior SHA256 `1913198be506e35a4c47a33bc03d14e405f8ac72d41aced08a59fd10341d3ef3`. Se extrajo y cotejó el JSON independientemente en este chat; 20 semillas y 320 filas coinciden. El almacenamiento de Drive no sustituye git versionado del resumen.
- **Alerta de acceso:** el metadata devuelto por Drive para ese ZIP muestra permiso `anyone: writer` (sin descubrimiento público), además de owner. **No asumir que es privado ni modificar permisos sin autorización del usuario.** Son datos sintéticos, no datos personales ni binarios de Creatures.

## 2. Resultados primarios de desarrollo

Métrica congelada: `S = 0.5*A-original-32 + 0.25*B1-32 + 0.25*B2-32`. Unidad estadística: mundo pareado; A inversión32 se reporta aparte. Comparación contra **mejor baseline simple seleccionado únicamente en desarrollo**, FIFO 1-NN16.

| Método | S medio en 20 mundos | Estado completo medio, bytes (checkpoints32) | A inversión32 media |
|---|---:|---:|---:|
| Raw16 + D-v1 | 0.688125 | 449 | 0.4875 |
| **FIFO 1-NN16 (mejor baseline simple)** | **0.812083** | **5131** | **1.0000** |
| **KMeans K4** | **0.847396** | 6859 | **0.4875** |
| KMeans K8 | 0.795469 | 7481 | 0.385938 |
| KMeans K16 | 0.742708 | 8694 | 0.363438 |

KMeans4 vs 1-NN: diferencia pareada media **+0.0353125 (=+3.53pp)**, mediana +0.03958; bootstrap95% predefinido de 5000 resamples por mundo: **[+0.0122891,+0.0586458]**; mejora en15 mundos, empeora en4, empate en1. Aunque el intervalo descriptivo es positivo, **no alcanza la puerta de ventaja media ≥5pp** fijada antes de correr. La selección del mejor candidato en desarrollo hace que ese IC no sea evidencia confirmatoria independiente. Ganancia A original apenas +1.25pp; B promedio +5.8125pp.

**Costo:** KMeans4 usa aprox. **34% más estado serializado** en checkpoint32 que FIFO 1-NN16 (6859 vs5131 bytes). Adquisición CPU A+B promedia ~118 ms vs ~9 ms del control (métrica de runner específico, no benchmark portable). Además, la reversión A de KMeans4 es **48.75%** vs **100%** en el baseline; la ventaja de transferencia no implica adaptabilidad ante cambio de contingencia, defecto relevante para una mente autónoma.

KMeans8 y KMeans16 no mejoran al baseline; diferencias compuestas -1.66pp y -6.94pp respectivamente.

### FuzzyART y presupuesto

Tres configuraciones por dos familias por 20 mundos = 120 condiciones. **104/120 superan la capacidad preregistrada de 16 categorías**:
- rho=.60: A 5/20 fuera de presupuesto; B 20/20.
- rho=.80: A 20/20; B 19/20.
- rho=.90: A 20/20; B 20/20.

Ninguna configuración es evaluable en los 20 mundos completos bajo la regla acordada; **no asignar 0% a casos inviables ni escoger solo los mundos exitosos**. Esto es un resultado de presupuesto para **este entorno, los rho y este límite de16**, no refuta universalmente ART.

## 3. Juicio crítico y decisión según puertas

1. **NR01.04 desarrollo:** realizado y reproducible a través del runner y los artefactos. La revisión no encontró filtración de información observable en las comprobaciones programadas; esto **no equivale a demostrar ausencia absoluta** de defectos.
2. **NR01.05 confirmación:** **NO habilitada**. Ningún candidato aprendido elegible alcanzó la ventaja mínima preregistrada de5pp; KMeans4 falla además la adaptación a reversión y no hay ablación causal de su encoder. No consumir holdouts para confirmar una alternativa insuficiente.
3. **NR01.06:** decisión técnica **STOP de esta línea/configuración**; no fabricar otro encoder, subir topes, redefinir gate o introducir cuerpo/mundo/LLM para salvar la hipótesis. Archivar hallazgos como resultado negativo/limitado; el conocimiento reutilizable es que un baseline simple alcanza rendimiento alto, KMeans4 muestra una ventaja modesta de transferencia de difícil compensación por coste/adaptación, y ART excede capacidad.
4. **Sin decisión de producto:** nada de lo anterior acredita una mente mínima integrada, causalidad cognitiva ni utilidad como arquitectura de Nilo. G00-H, G05, G09 originales NO se transforman en superadas.
5. Si se quiere una **nueva línea distinta**, exigirá pregunta científica discriminante no satisfecha por 1-NN, hipótesis causal y evaluación de soluciones existentes, antes de abrir otro plan. No continuar automáticamente NR01 con parámetros elegidos ex post.

**Estado de código:** todo este trabajo permanece en PR#103 **draft**, sin merge, y sin modificaciones a `main` ni Nilo0.7.

## 4. Reproducción y limitaciones

- Código: `experiments/neurolab/nr01_worlds.py`, `nr01_decoder.py`, `nr01_knn.py`, `nr01_encoders.py`, `nr01_harness.py`, `nr01_dev_analysis.py`, `nr01_development.py`.
- Workflow `.github/workflows/neurolab-nr01-development.yml`, Python3.11.18, `artlib==0.1.12`, `scikit-learn==1.9.1`.
- El benchmark de CPU y bytes corresponde a un runner determinado. No generalizar fuera de las familias sintéticas A/B, de 16 dimensiones ni al comportamiento espontáneo de Nilo. El bootstrap sobre semillas seleccionadas no convierte desarrollo en confirmación.
- El archivo JSON completo está archivado en Drive, pero el **permiso de editor para `anyone` devuelto por Drive debe revisarse con autorización** si se pretende conservación privada o inmutable; no se hizo cambio de permisos.

**Siguiente acción de continuidad:** NO nuevos experimentos NR01 por inercia. Si el usuario pide seguir NeuroLab, primero revisar este cierre y proponer **una pregunta diferente con criterios refutables**, no más tuning de este conjunto.
