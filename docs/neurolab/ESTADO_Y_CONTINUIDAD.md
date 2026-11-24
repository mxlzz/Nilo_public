> **H-08b.9–.12 ORIGINAL OPERATIVO, PRIMERA EVIDENCIA DINÁMICA · 24/11/2026:** [arranque documentado + DDE](H08B_09_MODO_ARRANQUE_DOCUMENTADO_20261124.md), [Norn original](H08B_10_PRIMER_NORN_OBSERVADO_20261124.md), [orden alternativo](H08B_11_ORDEN_ALTERNATIVO_OBSERVADO_20261124.md), [transferencia CHEM observada](H08B_12_TRANSFERENCIA_CHEM_OBSERVADA_20261124.md). Resuelto arranque con opción documentada de distribución comercial, CD montado, mismo EXE/GEN, sin parches. CI #45449178994 valida DDE real y mundo inicial vacío; #45449497913 y #45449814988 crean Norn único con copia exacta dad1 y leen química/célula; #45450061479 **29 ciclos alternativos completos química→cerebro**; #45450393703 **19 ciclos completos con snapshots pareados, 19/19 predicción Reward→DecisionCHEM0 y Reinforcement→ConceptCHEM0 exacta** (Punishment también 19/19, todos ceros). AP=AB= AQ en 11 bytes observados. Primera evidencia dinámica compatible con H3/H4/H7, no prueba de aprendizaje ni latencia nativa ni ruta regular. JSONs derivados guardados. Corrigieron error sintáctico de observador CAOS y filtro de depuración; no alterar binario. **Siguiente contraste:** [CI #45450765463](https://github.com/mxlzz/Nilo_public/actions/runs/45450765463) espera ventana posterior 85s sin debugger y verifica identidad; pendiente resultado. N STOP, G05/G09 abiertas, G-H6-CLOCK no cerrada. No se necesitan archivos ni permisos del usuario. PR103 draft, main intacto.

> **H-08b.8 TRAZA DE ARRANQUE ORIGINAL · 24/11/2026 — PASS de observación, motor NO operativo:** [informe y adenda MFC](H08B_08_TRAZA_INICIALIZACION_20261124.md), [CI #45447761937](https://github.com/mxlzz/Nilo_public/actions/runs/45447761937), job 138636124043. Depurador x86 verificó secuencia init → registration_branch (etiqueta provisional) → early_return, sin apertura World.sfc ni world tick observados. Localmente se verificaron IAT ordinal296 constructor y ordinal5214 parseo en MFC42 del archivo; constructor pone +8/+C=0, parser sin argumentos no invoca método virtual, original comprueba dichos campos. No inferir causa sin verificar argumentos legítimos de AUTORUN/SETUP/Launcher y módulo realmente cargado. No forzar flags ni eludir comprobaciones. **No intervención del usuario necesaria ahora**, ISO y DATA ya accesibles. Próxima unidad: inspección de cadena original de instalación/lanzamiento y módulo cargado, antes de otro arranque. N STOP, G05/G09 abiertas, PR103 draft, main intacto.

> **H-08b.6–.7 CD ORIGINAL COMPLETO · 24/11/2026:** [inventario y montaje](H08B_06_MEDIO_COMPLETO_MONTADO_20261124.md) PASS, ZIP 591498236 B, SHA256 `91805784212380b804ec5c3889f2524ff358379c6a0a964e5dadba147c5498af`, ISO 591384576 B, SHA256 `555ac57e00d2080268da75ef6063708a7ad20f56f9fd79f0507ab3505c91b297`; CI #45446481434 intento2 y #45447141306 verificaron CRC, ISO9660, CDFS, CD-ROM real de solo lectura. Segundo secreto operativo. [Contraste con CD montado](H08B_07_CONTRASTE_CD_MONTADO_20261124.md), CI #45447365541: original Build47, rutas y CD Drive correctos, proceso termina código0 sin mundo/DDE válido; montaje no basta. Retirada de recursos temporales confirmada. **No solicitar de nuevo archivos ni secretos.** Siguiente: diagnóstico acotado de ruta de inicialización (o instalador original en entorno compatible), no nuevos intentos arbitrarios. N STOP, G05/G09 abiertas, PR103 draft, main intacto.

> **H-08b.6 MEDIO COMPLETO RECUPERABLE · 24/11/2026 — PENDIENTE DE TRANSFERENCIA:** localizado en carpeta Drive neurolab el nuevo archivo `creatures_202102.zip`, 591498236 B, acceso por enlace lector. El conector rechazó descarga directa por límite 268435456 B (HTTP 413); el entorno local no pudo resolver DNS de Drive. No se ha inspeccionado su contenido ni verificado su hash. [Workflow de inventario read-only](../../.github/workflows/neurolab-full-cd-inventory.yml), commit `cc007b67ea174cfb419a440625a93d6cba4b8df1`, preparado para transferir mediante secreto independiente `NEUROLAB_CD_FILE_ID`, comprobar tamaño y CRC, registrar SHA256, enumerar medios y detectar ISO9660/CUE sin ejecutar ni publicar archivos. [Primer intento](https://github.com/mxlzz/Nilo_public/actions/runs/45446481434) condicionado al nuevo secreto. No incluir identificador del archivo en repositorio; conservar secreto DATA existente. Tras inventario, auditar instalador/estructura del CD y verificar correspondencia con Build47 antes de montar o probar; la autorización previa de ejecución del juego sigue vigente. No se afirma que el medio resuelva el cierre. N STOP, G05/G09 abiertas; PR103 draft, main intacto.

> **H-08b.4–.5 EJECUCIÓN ORIGINAL AUTORIZADA · 24/11/2026:** [cinco ensayos Win32](H08B_04_ARRANQUE_WIN32_ORIGINAL_20261124.md) y [contraste Wine + puerta de medio original](H08B_05_CONTRASTE_WINE_Y_MEDIO_ORIGINAL_20261124.md). Original hasheado iniciado en Windows remoto; WinG resuelto con DLL original temporal, ocho valores de registro reproducidos desde x86 del EXE; DDE Vivarium/Anything conecta durante aviso, pero sin respuesta CAOS válida. Con rutas correctas, arranque por defecto y World.sfc explícito terminan código 0 antes de observar carga. [Wine 9.0 CI #45390024315](https://github.com/mxlzz/Nilo_public/actions/runs/45390024315) reproduce cierre temprano; CI SUCCESS = prueba ejecutada, **NO juego operativo**. Evidencia estática nueva: rutina 0x4119D0 consulta CD Drive en ruta alternativa de recursos (0x411AE2–0x411AFA); manual original requiere CD. No demuestra que sea causa del cierre. **Intervención necesaria:** recuperar imagen completa original ISO/BIN-CUE (o contenido íntegro con estructura y etiqueta) para auditar instalador y montar CD genuino; no volver a pedir DATA.zip/EXE/GEN, no pedir ISO Windows todavía. N STOP, sin medición neuronal, G05/G09 abiertas, PR103 draft, main intacto. Sin parches ni distribución propietaria.

> **H-08b.3 TRANSFERENCIA ORIGINAL AL RUNNER · 24/11/2026 — PASS:** el usuario configuró el secret solicitado; [workflow de integridad](../../.github/workflows/neurolab-original-input.yml), commit `d193f226231cd32bf2cf83507c246fa43a5732e8`, [CI #45388848833](https://github.com/mxlzz/Nilo_public/actions/runs/45388848833), job 138426865890 SUCCESS. Log verificado: tamaño y SHA256 del DATA.zip exactos; 1163 archivos y CRC correctos; SHA256 de EXE y GEN originales coincidentes; ZIP temporal eliminado. Sin extraer, ejecutar, publicar ni conservar los archivos en runner; sin revelar ID del secreto. **Dependencia de transferencia resuelta.** Pendiente únicamente consentimiento específico del usuario para prueba acotada de arranque original en runner Windows efímero. No se presupone compatibilidad ni evidencia dinámica. N STOP, G05/G09 abiertas; PR103 draft y main/Nilo0.7 intactos.

> **H-08b.2 WIN32 DDE REMOTO · 24/11/2026 — PASS sintético:** [informe y gate](H08B_02_FACTIBILIDAD_WIN32_DDE_20261124.md), [CI #45325543969](https://github.com/mxlzz/Nilo_public/actions/runs/45325543969), job 138214139804 SUCCESS. Windows runner `windows-2022`, programa x86 compilado y comunicación DDEML real entre servidor/cliente sintéticos; respuesta exacta verificada. Priorizar Windows nativo antes de VM Windows98/ReactOS. **No C1 ejecutado, no cadencia ni compatibilidad histórica demostradas.** Requiere intervención específica: propietario configura secret `NEUROLAB_DATA_FILE_ID` de DATA.zip (no ID en código público) y autoriza ejecución aislada del original. Mantener hash congelado y no publicar recursos ni logs sensibles. No se necesita ISO Windows para primer ensayo. N STOP, G05/G09 abiertas; PR103 draft, main intacto.

> **H-08b.1 FACTIBILIDAD QEMU REMOTO · 24/11/2026 — PASS sintético:** [workflow](../../.github/workflows/neurolab-vm-capability.yml) commit `f7da93c4f63cfcb89430acba00bee01f2bf6d515`; [CI #45325080079](https://github.com/mxlzz/Nilo_public/actions/runs/45325080079), job `138212625077`, SUCCESS, log confirma QEMU 10.2.1 y marcador `PASS: synthetic x86 guest ran; QMP resumed and paused it; no network or proprietary files.` Se arrancó un sector de arranque sintético propio en x86 TCG, sin red, se comprobó ejecución, pausa/reanudación/consulta y cierre por QMP. Entorno local Linux no dispone de QEMU/Wine/KVM ni DNS útil para instalación. **Se demuestra control remoto por scripts desde GitHub Actions, NO arranque de Windows ni Creatures ni persistencia ni fidelidad temporal**. Próxima unidad: evaluar medio legal de Windows 95/98 (o prueba separada Windows runner moderno para compatibilidad, no oráculo histórico), transferencia privada autorizada de recursos originales y persistencia de estados; no subir binarios ni imágenes de disco a repositorio público. No ejecutar juego sin permiso específico. Mediciones en VM deben distinguir orden lógico y tiempos virtualizados, no equivaler a hardware histórico. N STOP y G05/G09 abiertas. PR103 draft, main intacto.

> **H-08b.0 INVENTARIO DATA COMPLETADO · 24/11/2026:** [evidencia y decisión](H08B_00_INVENTARIO_DATA_Y_OBSERVACION_NATIVA_20261124.md). DATA.zip de Drive contiene 1163 archivos, CRC íntegro, EXE/GEN con hashes exactos originales, Build47 US, mundo, gráficos, genética, Hatchery, Science Kit y DLLs WinG/runtime. Presencia de interfaz DDE/CAOS comprobada estáticamente en motor y Science Kit; herramientas históricas CDR permiten sondeos neuronales/químicos, no garantizan resolución intratick. Priorizar observación nativa antes de depuración selectiva. **No se ejecutó el juego ni se verificó el arranque portable**; quedan entorno compatible y permiso específico. Si arranque falla por registro/recursos, solicitar solo manifiesto de instalación o error concreto. N STOP, G05/G09 abiertas, PR103 draft, main/Nilo0.7 intactos.

> **H-08b PLAN DE FACTIBILIDAD · 22/11/2026:** [requisitos verificables de observación dinámica](H08B_GATE_FACTIBILIDAD_TRAZA_DINAMICA_20261122.md), sin ejecutar ni instalar el juego. H-08a estática completada sobre EXE/GEN genuinos, H08a-DIRECT PASS, pero no permite medir cadencia efectiva ni crédito temporal real. Para H-08b dinámica se requieren **consentimiento específico de ejecución** y **entorno Windows compatible con recursos completos del juego**, no solo EXE/GEN. Se ha llegado a un punto de intervención legítimo. No inferir timings a partir de timer90ms ni reiniciar bancos N; PR103 draft y `main` intactos.

> **H-08a CIERRE ESTÁTICO · 22/11/2026:** se verificó directamente en la carpeta Drive `neurolab` el EXE SHA256 `548a...d7` y GEN `e2bb...dd4` originales. [Preregistro](H08A_PREREGISTRO_RUTAS_EJECUTABLE_20261122.md) → [informe H08a](H08A_RESULTADO_RUTAS_ORIGINALES_20261122.md) → [evidencia exacta](resultados/h08a_original_evidence_20261122.json), [auditor](../../experiments/neurolab/h08a_static_audit.py), [CI sintética #45061311716](https://github.com/mxlzz/Nilo_public/actions/runs/45061311716) SUCCESS. Recuento directo E8 en el binario: **brain2, química3, world3**. Nueva llamada química `0x40B089` en rutina de construcción del objeto; lee contador/objeto químicos y precede al flag `[criatura+0x2CBC]=1`. G-H08a-DIRECT PASS delimitado; indirectos y reloj efectivo ABIERTOS. **No se ejecutó el juego**. Las antiguas notas «faltan archivos originales» quedaron supersedidas. Próxima etapa H-08b dinámica **requiere autorización específica y un entorno de ejecución compatible**, no suponer 90ms por Norn. Línea N y NR01/G05-NX01 continúan STOP; G05/G09 NO superadas. PR103 draft, `main` y Nilo0.7 intactos.

> **H-07 AUDITORÍA DOCUMENTAL COMPLETADA · 22/11/2026:** [cadena temporal histórica C1 vs microC1](H07_AUDITORIA_CADENA_TEMPORAL_Y_BLOQUEO_20261122.md). La reconstrucción H previa YA estableció WM_TIMER nominal90ms, condiciones de ruta cerebro→química y excepción química→cerebro, orden emisores→receptores→reacciones→decaimiento y enlace genético CHEM/SVRule. Se demostró **diferencia de secuenciación** con `C1ContextBrain` (químicos directos por tick), NO fidelidad de un Norn activo. Pendiente H-08a: inspección nueva de rutas y eventos x86 requiere recuperar EXE original (y GEN para cruces químicos); archivos binarios no aparecen accesibles en la sesión ni por búsqueda de Drive. H-08b (cadencia efectiva en ejecución) exige además consentimiento específico antes de correr juego. **N STOP por saturación de G05-NX01**, NR01 STOP, G05/G09 NO superadas; no nuevos experiments. PR103 draft; main/Nilo0.7 intactos.

> **DECISIÓN CANÓNICA 22/11/2026 — G05-NX01 STOP / N EN PAUSA:** [resultado reproducible y decisión](G05_NX01_RESULTADO_Y_STOP_20261122.md). Tras [G05-INFO.03 PASS técnico](G05_INFO_03_RESULTADO_FACTIBILIDAD_20261122.md), el desarrollo **solo de controles** preregistrados 25000..25019 evidenció que TK (tabla con soporte de demoras conocido, sin ID causal) logra **S=1.0000 en 20/20 mundos y ambas fases**, T0 S=.9361, Tλ S=.9347. [CI #45059347950](https://github.com/mxlzz/Nilo_public/actions/runs/45059347950) SUCCESS, [JSON por semilla](resultados/g05_nx01_baselines_dev_summary_20261122.json). La mejora neuronal obligatoria de ≥+.05 vs TK es **imposible por techo1.0**: **no se ejecutaron C/F/P**, NO se abrió confirmación26000..26019, G05/G09 no superadas. **No ajustar el mundo a posteriori ni abrir nuevas cohortes N por inercia.** Próxima vía alineada con el plan original: **H histórica** (scheduler neuronal/químico del C1) como análisis documental acotado, antes de plantear otra hipótesis N. **NR01 STOP** vigente. PR103 draft; `main` y Nilo0.7 intactos.

> **G05-INFO.02 DOCUMENTAL COMPLETADA · 22/11/2026:** [diseño conceptual de banco sin atajo determinista](G05_INFO_02_DISENO_CONCEPTUAL_BANCO_SIN_ATAJOS_20261122.md). Se propone flujo continuo de acciones, potenciales consecuencias diferidas y demoras variables **sin marcador de target por transición**; se especifican señal estadística ideal y controles de misma información. **No hay parámetros congelados, no hay nueva campaña ni evidencia experimental**. Próxima unidad `G05-INFO.03` documental: decidir semántica de colisiones/químicos y reloj, probar factibilidad analítica con adversarios, verificar compatibilidad de baselines existentes, y decidir si justifica preregistro. Aplican cierres anteriores: [G05-INFO.01 fuga estructural](G05_INFO_01_RESULTADO_IDENTIFICABILIDAD_20261122.md), [priorización](DECISION_PRIORIZACION_Y_GATE_G05_INFO_20261122.md), NR01 STOP, G05/G09 no superadas. PR103 draft; main/Nilo0.7 intacto.

> **G05-INFO.01 COMPLETADA · 22/11/2026 — RESULTADO C:** [auditoría de identificabilidad](G05_INFO_01_RESULTADO_IDENTIFICABILIDAD_20261122.md) verificó contra el runner g.10b una fuga estructural: en cada pulso no nulo el contexto causal es el opuesto al actual y la decisión puntuable es la última antes del cambio de contexto. Prueba algebraica y **648/648 fixtures sintéticos de calendario** (NO corridas científicas) confirman la reconstrucción sin ID del evaluador. **G05 g.10b NO es banco discriminante general; NO reejecutar ni tunear.** [Priorización científico-metodológica](DECISION_PRIORIZACION_Y_GATE_G05_INFO_20261122.md): crédito G05 primero, retención ACTIVE segundo, NR01 detenida; siguiente **G05-INFO.02: diseño documental de una tarea sin atajo de contexto/tiempo**, antes de cualquier preregistro o ejecución. G05/G09 siguen NO superadas; H histórica separada; PR103 draft, main/Nilo0.7 sin cambio.

> **CONTROL DE ALINEACIÓN PREVIO A NUEVA ETAPA · 22/11/2026:** [auditoría contra objetivo original y puertas G00–G09](AUDITORIA_ALINEACION_PREVIA_SIGUIENTE_ETAPA_20261122.md). NR01 se ejecutó conforme al plan y se cerró sin superar su puerta de ingeniería; **el objetivo global de NeuroLab sigue incompleto**. No abrir nuevos experimentos por inercia. Próxima unidad **propuesta, no aprobada**: elegir documentalmente entre preguntas pendientes o pausar N; mantener H histórica separada. Evitar leer secciones históricas de este archivo como progreso vigente.

# Estado canónico vigente — NeuroLab NR01 · 22/11/2026

**DECISIÓN DE CONTINUIDAD: NR01.04 DESARROLLO COMPLETO; NR01.05 CONFIRMACIÓN BLOQUEADA; NR01.06 CIERRE NEGATIVO/LIMITADO.** Leer primero [resultado y cierre auditado NR01](NR01_04_06_RESULTADO_Y_CIERRE_20261122.md), cuyo antecedente es el [preregistro de la cohorte](NR01_04A_PREREGISTRO_DESARROLLO_20261122.md). [CI de los 20 mundos](https://github.com/mxlzz/Nilo_public/actions/runs/45049703202) SUCCESS (320 condiciones, 0 excepciones, 104 ART fuera de presupuesto). Mejor baseline simple 1-NN16 S=.81208; mejor modelo aprendido KMeans4 S=.84740, ventaja de **+3.53pp** (IC bootstrap de desarrollo positivo), **menor al gate5pp**; reversión A KMeans4=.4875 vs 1-NN=1.0 y costo de estado superior. **No hay mérito para confirmación ni nuevo mecanismo; STOP de esta configuración, sin tuning retrospectivo.** JSON y JSONL completos verificados por SHA y almacenados en [Drive / neurolab](https://drive.google.com/file/d/1CKUVUpAtBGfRV2QveMueeH6AOvCT_HtP/view?usp=drivesdk); ver informe por digest. **ADVERTENCIA Drive:** el permiso devuelto para el ZIP es `anyone:writer`; no se cambiaron permisos, no describir el archivo como privado. Confirmación24000..24019 e históricos1400..1419 no usados. PR#103 continúa draft, sin merge; `main` y Nilo0.7 intactos. **Próximo:** no ejecutar NR01.05 ni seguir este modelo; una investigación distinta requiere nueva pregunta, nuevos controles y autorización/dirección de trabajo, no rescate de los parámetros fallidos.

---

**NR01.03-C SOFTWARE PARCIAL 22/11/2026:** además del [contrato](NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md), se incorporaron [decoder común](../../experiments/neurolab/nr01_decoder.py) SHA commit `0340c779378b8c92b9da7ce4b96261c23bf5bbd8` y [cinco tests toy](../../experiments/neurolab/tests/test_nr01_decoder.py) commit `e2873d3c54630dfb48d717be0144ea51b1159cfa`. **Cinco pruebas equivalentes ejecutadas localmente y PASS**, sin datos científicos; al consultar GitHub el último commit no registraba statuses ni workflow runs, de modo que **NO hay CI del commit verificada**. Pendientes: integridad del harness, adaptadores ART/KMeans, 1-NN, igualdad de observaciones, coste, congelamiento y suites totales. NO declarar NR01.03-C superada ni ejecutar cohortes 23000..23019/24000..24019. PR103 draft, Nilo0.7/main intactos.

**NR01.03-C CONTRATO DOCUMENTAL 22/11/2026:** [contrato de decoder, presupuesto e igualdad de información](NR01_03C_CONTRATO_DECODER_COSTOS_20261122.md) creado en commit `7d5b13443fcbadc97271cca1cac4be3a4495c16d`. Define interfaces, decoder lineal común de feedback binario, ART hasta 16 categorías, KMeans K4/8/16, controles raw lineal y FIFO 1-NN, métricas de coste y siete grupos de tests toy. **NO se implementó ni probó aún NR01.03-C; NO se usaron semillas científicas.** Siguiente: implementar adaptadores/harness y tests con semillas 0/1/42 y verificar CI antes de ejecutar desarrollo 23000..23019. PR103 sigue draft; `main` y Nilo0.7 intactos.

# NeuroLab — estado verificable y protocolo de continuidad

**NR01.03-B API PASS 22/11/2026:** [resultado](NR01_03B_RESULTADO_APIS_20261122.md), [Actions #45044290040](https://github.com/mxlzz/Nilo_public/actions/runs/45044290040) SUCCESS; `artlib==0.1.12` FuzzyART y `scikit-learn==1.9.1` MiniBatchKMeans instalados y validados **solo en vectores ficticios** (categorías 2/2, `predict` sin mutar pesos/centroides). **No constituye capacidad de aprendizaje transferible**; ningún modelo NR01 corrió sobre mundos científicos. Próximo paso NR01.03-C: congelar interfaz/decoder y tests de igualdad de información/costo, antes de 23000..23019. Confirmación24000..24019 e históricos1400..1419 sin usar.

**SOFTWARE NR01.03-A VERIFICADO 22/11/2026:** [GitHub Actions #45043853284](https://github.com/mxlzz/Nilo_public/actions/runs/45043853284), commit `958a346bf54797fa8ecde5ed1819e1c5000af215`, paso `E01 deterministic numerical oracles and state replay` aprobado: **573 tests** (2 expected failures históricos), incluidos **7 tests de `test_nr01_worlds.py` correctos**; generador de mundos y bloqueo de holdouts verificados. **Esto NO es corrida científica ni aprobación NR01**. La ejecución completa del workflow continuaba procesando benchmarks cuando se revisó; no afirmar que toda CI terminó si no se constata luego. No se ejecutó cohortes 23000..23019 o 24000..24019, ni se usó ARTlib/KMeans todavía. Siguiente: smoke técnico documentado de APIs y preparación/congelamiento de modelos basales; no ajustar experimento hasta medir.

**ESTADO VIGENTE · 22/11/2026 — CONTINUIDAD NR01 (reemplaza encabezados históricos posteriores):** La campaña original E00–E09 se [cerró como resultado parcial/negativo](E09_CIERRE_FORMAL_RESULTADO_20261122.md): **G09 NO superada**, G05 (crédito temporal) y R-ACT-I3c (retención activa) tampoco. [Ocho artefactos críticos de E09 preservados](E09_ARCHIVO_EVIDENCIAS_20261122.md) en Drive privado del usuario, con SHA256 del ZIP y manifiesto público de trazabilidad; no se logró archivo completo de todas las corridas. **Nueva línea NR01** (no E10 ni reescritura de G09): [plan por puertas](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md), [investigación de herramientas existentes](NR01_REVISION_ALTERNATIVAS_REPRESENTACIONES_20261122.md), [desafío preregistrado](NR01_02_PREREGISTRO_DESAFIO_20261122.md), [generador preregistrado antes de código](NR01_02A_CONTRATO_GENERADOR_PRECODIGO.md). **Software escrito, no experimentos científicos:** `nr01_worlds.py` + `tests/test_nr01_worlds.py` solo para verificar mundos/datos; cohortes de desarrollo 23000..23019 y confirmación 24000..24019 **NO ejecutadas**. El bloque de siete pruebas técnicas NR01.03-A pasó en CI; aún no se ha validado toda la batería completa de workflows ni algoritmos candidatos. No se ha instalado ni entrenado ARTlib, KMeans ni ningún modelo NR01. **PR #103 draft y sin merge; `main`, Nilo 0.7 y semillas históricas 1400..1419 intactos**. El resto de este archivo conserva la historia previa y sus erratas fechadas.

**SEGUIMIENTO E09.01/E09.07 22/11/2026:** [Auditoría de conservación y reproducibilidad](E09_01_07_PRESERVACION_EVIDENCIAS_20261122.md) inspeccionó 48 archivos de resultados versionados (~1,44MB); JSON E03/E06/E07/E08 permanentes, I3c7h/i/k archivos grandes íntegros principalmente en Actions temporales y solo hashes/manifiestos persistentes. Regresión de Nilo/NeuroLab en SHA f9fe2364 [CI45028914964](https://github.com/mxlzz/Nilo_public/actions/runs/45028914964)/[CI45028915032](https://github.com/mxlzz/Nilo_public/actions/runs/45028915032) SUCCESS. Conservación integral E09.01 y síntesis global G09 PARCIALES/ABIERTAS, se permite comunicar resultados negativos limitados, no afirmar mente mínima integrada. Continuidad: no inventar otro experimento por rutina; resolver política de archivo o cerrar línea N actual con limitaciones explícitas. PR103 draft, main/Nilo0.7 intactos.


**SEGUIMIENTO 2026-11-22 — TAB2 y síntesis:** [TAB2 de E03](E09_05_TAB2_E03_RESULTADO.md), preregistro antes de código, contrastó neuronas E03 de seis unidades con una tabla 2×2 de cuatro pesos bajo protocolo episódico original: [CI45028560329](https://github.com/mxlzz/Nilo_public/actions/runs/45028560329) SUCCESS4, 10.480 comparaciones completas de las dos entradas, 3.200 observaciones holdout, 5.200 actualizaciones, discrepancias0. [TAB1 de E06](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md) estableció equivalencia de detectores fijos con una tabla 4×2. [E09.08–.10](E09_08_10_SINTESIS_DECISION_20261122.md) sintetiza la evidencia, recomienda **PAUSA de desarrollo incremental de N** por ausencia de ventaja neural en E03/E06 bajo tareas originales, sin declarar G09 pasada. Siguiente: auditar preservación de datos crudos antes de informe de cierre; G05 y R-ACT tienen significados distintos y siguen no superados. Ninguna confirmación1400–1419 ni merge.

**ADENDA CANÓNICA 2026-11-22 — E09 retomada contra plan original:** [reconciliación G00–G09](E09_00R_RECONCILIACION_GATES_20261122.md), [inventario E00–E08](E09_01_AUDITORIA_CAPACIDADES_20261122.md), [integración/coste](E09_02_EVALUACION_INTEGRACION_MINIMA_20261122.md), [TAB1 resultado comprobado](E09_05_TAB1_RESULTADO_EQUIVALENCIA.md). **G05 = crédito temporal**, no retención ACTIVE (criterio específico `R-ACT-I3c`); **G09 = síntesis/arquitectura mínima del cerebro aislado**, no agente con mundo. E09.05-TAB1 [CI45028224155](https://github.com/mxlzz/Nilo_public/actions/runs/45028224155) SUCCESS4, 38.720 comparaciones+1.600 holdout y 4.800 updates, discrepancias0: E06 detector fijo es equivalente a tabla de cuatro pares×dos pesos en su dominio. Descarta implementar una integración que solo reproduzca E06. G05 original, R-ACT-I3c, G09 y G00-H no superadas/cerradas. La familia miniC1 permanece congelada, PR#103 draft, main/Nilo0.7 intactos, seeds1400..1419 reservadas. **El texto previo sobre «G05 retención» y «G09 organismo» se conserva SOLO como registro histórico de denominaciones erróneas**, véase adenda.

**Estado actualizado:** 2026-11-22 (I3c.7e–k cerrados: aprendizaje de recompensa/decisión local verificado, G05 retención ACTIVE no superada. I3c7k oráculo de transferencia STW→LTW [CI44987744410](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) SUCCESS5, +4,90pp IC95[+.83,+8.91] por debajo de puerta10pp. [I3c7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md) determina STOP incremental mini C1 y separación H histórica vs N autonómica. [I3c8](E09_02I_I3C8_ALTERNATIVAS_EXISTENTES_MEMORIA.md) revisa antecedentes verificados de elegibilidad, consolidación multiescala, EWC/SI y simuladores Brian2/Nengo; ninguna solución lista fue verificada para reemplazar el miniC1 sin añadir complejidad. No nuevas simulaciones ni semillas confirmatorias. **G05/G09/G00-H ABIERTAS, PR103 draft/main/Nilo0.7 intactos**).
**Línea base documentada:** protocolo v0.1.0 en rama `docs/neurolab-protocolo-20261120`, propuesto para revisión.  
**Ejecución experimental:** I3c7e,f,g,h,i verificaron aprendizaje químico y efectos causales locales, pero nunca persistencia G05. **I3c7j** [evaluación estratégica y diagnóstico LTW](E09_02I_I3C7J_MEMORIA_DIAGNOSTICO_ESTRATEGIA.md) POSTHOC, no simulación nueva: LTW de I3c7g LONG no conserva contribución discriminativa para ambos contextos en M0 (0/20), pese a 75 slots≥5; D0 160 slots≥5 pero contribución LTW-only bilateral nula. **I3c7k** [prereg posthoc](E09_02I_I3C7K_TRANSFERENCIA_CONTENIDO_PRE_REGISTRO.md), [CI44987744410](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) SUCCESS5, original 20 semillas1700..1719 fuentes SHA exactas, oracle STW→LTW incrementa ACTIVE ~4.90pp (IC95+.83,+8.91), menos que mínimo10pp predefinido, swap owner decrece precisión; [reporte](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md). G05/G09/G00-H ABIERTAS, sin nuevos seeds/reglas C1.
**Código del cerebro:** inspección estática del ejecutable y genoma C1 alimenta módulos E09f (SVRule, sinapsis, strength, migración) y microredes E09g de cinco y seis unidades; sin motor Nilo, cuerpo, mundo ni LLM.  
**Autorización vigente documentada:** el usuario autorizó continuar ejecución secuencial hasta necesitar intervención; ninguna integración con el motor Nilo 0.7 ni merge a main.

## 1. Marcador canónico de progreso

| Campo | Valor inicial |
|---|---|
| Investigación | NeuroLab: mente neuronal aislada inspirada en Creatures 1 (1996) |
| Documento rector | [README.md](README.md) |
| Etapa actual | **E09 CAMPAÑA CERRADA, G09 NO SUPERADA. NR01.00/01 DOCUMENTADAS; NR01.02 DESAFÍO Y GENERADOR PREREGISTRADOS. NR01.03-A generador + 7 tests y NR01.03-B ARTlib/KMeans API VALIDADOS en CI45043853284 (CI45043853284; paso 6, 573 tests; 2 fallos esperados) y [CI45044290040](https://github.com/mxlzz/Nilo_public/actions/runs/45044290040) API PASS**, no hay aprendizaje ni corrida científica. [Cierre](E09_CIERRE_FORMAL_RESULTADO_20261122.md), [archivo](E09_ARCHIVO_EVIDENCIAS_20261122.md), [NR01 plan](NR01_PLAN_INVESTIGACION_REPRESENTACIONES.md). PR103 draft sin merge. |
| Siguiente subtarea exacta | **NR01.03-C:** fijar decoder y presupuestos comparables, representar creación/exceso de categorías y baselines crudos/kNN; preregistrar interfaces exactas y construir tests software sólo sobre toy seeds (0/1/42). [ARTlib y KMeans API verificadas](NR01_03B_RESULTADO_APIS_20261122.md), aún **sin corridas científicas**. Tras superar gates técnicos usar solo desarrollo 23000..23019, reservar confirmación 24000..24019 y semillas históricas1400..1419. |
| Última subtarea validada | **NR01.03-B compatibilidad ARTlib0.1.12/KMeans1.9.1**, [CI45044290040](https://github.com/mxlzz/Nilo_public/actions/runs/45044290040) SUCCESS; [informe](NR01_03B_RESULTADO_APIS_20261122.md); precedida por **NR01.03-A generador**, siete tests individuales correctos dentro del paso de suite 573/573 (2 expected failures históricos), [CI45043853284](https://github.com/mxlzz/Nilo_public/actions/runs/45043853284). Ninguna prueba científica NR01 ejecutada; G09 no superada. |
| Experimentos ejecutados | I3c7e desarrollo1600..1619 factorial; I3c7f same20 posthoc; I3c7g desarrollo1700..1719 horizon con LTW>=5 sin retención; I3c7h desarrollo1800..1819 contingencia B vs P con química cambiante; I3c7i posthoc misma1800..1819 STW lesional; **I3c7j** análisis POSTHOC de LTW-only fuente I3c7g sin correr nuevo cerebro; **I3c7k** POSTHOC fuente I3c7g mismas20 semillas1700..1719, clones LTW original/transfer STW al mismo owner/transfer a owner cambiado, 128 ticks ACTIVE sin reward + FROZEN, no modificar entrenamiento. Ninguna de estas unidades supera G05 ni demuestra organismo C1 completo |
| Runs con evidencia | [I3c7k](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) SUCCESS5 artifact14740013286, [proveniencia](resultados/e09i3c7k_resultado_proveniencia.json); [I3c7i](https://github.com/mxlzz/Nilo_public/actions/runs/44987034290) SUCCESS7; [I3c7h](https://github.com/mxlzz/Nilo_public/actions/runs/44986258314) SUCCESS7; [I3c7g](https://github.com/mxlzz/Nilo_public/actions/runs/44970705424) SUCCESS6, [I3c7f](https://github.com/mxlzz/Nilo_public/actions/runs/44970236994) SUCCESS5, [I3c7e](https://github.com/mxlzz/Nilo_public/actions/runs/44969153930) SUCCESS7. G05/G09/G00-H abiertas |
| Última corrida del cerebro | I3c7k, mismas20 seeds I3c7g LONG tras reversión: sham S ACTIVE steady=.836979, LTW<-STW C=.885938, swapped owner X=.631250, todas FROZEN=.927083 (acciones idénticas), ΔC−S=.048958 IC95[.008333,.089063], ΔC−X=.254688 IC95[.134375,.367708]. Puerta precomprometida ΔC−S≥.10 NO. Conteo seeds steady≥.90 sólo fase B: S8/20,C10/20,X3/20, NO es criterio ambas fases G05. S quarter final .7281,C .8344,X .4641 (POSTHOC), efecto de magnitud no suficiente. G05/G09/G00-H abiertas |
| Estado de E00 | GEN y EXE originales SHA comprobados. E09h.4/5 vínculo emisor/receptor; [I3c.6a](E09_02I_I3C6A_RESULTADO_REALIMENTACION_ATROFIA.md) añade writer Type1 MIN / Type2+1 desde diez x86 anclas originales. Scheduler global/chemistry total y emulación dinámica completa siguen ABIERTOS |
| Estado del código | [I3c7j](E09_02I_I3C7J_MEMORIA_DIAGNOSTICO_ESTRATEGIA.md) investigación estratégica y análisis LTW del artefacto I3c7g, [I3c7k](../../experiments/neurolab/e09_i3c7k_transfer_stw_to_ltw.py) oráculo exclusivo de clone readout, sin modificaciones al módulo C1ContextBrain/genética/EXE/Nilo. Tests5 [CI44987744410](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) success, [manifest source](resultados/e09i3c7g_fuente_huellas.json) y [manifest output](resultados/e09i3c7k_resultado_proveniencia.json). PR#103 draft sin merge; main Nilo0.7 intactos |
| Integración con Nilo 0.7 | Ninguna |
| Bloqueos | **Retención duradera G05 sigue NO validada**: contingencia de recompensa/función local sí probadas, pero no perduran en ACTIVE. Atrofia nominal M16 no puede autoregularse fielmente en 8 slots; sin ella M0 STW decae; más LTW y horizonte de entrenamiento no resuelven; transferir patrón STW a LTW en un ORÁCULO mejora solo4.9pp vs mínimo10pp. No hay fundamento para nuevo algoritmo LTW/eligibilidad ni escalar C1 mini sin hipótesis mayor. Reconstrucción C1 histórica original G00-H y autonomía funcional N son líneas distintas, con costos separados. G05/G09/G00-H ABIERTAS |
| Decisiones nuevas pendientes | I3c7l STOP incremental mini C1 (no eliminación), I3c8 survey completado: ninguna librería/mecanismo existente estudiado resuelve por sí mismo la memoria ACTIVE y reversión sin alterar la arquitectura y presupuesto. **PROPUESTA abierta**: N memoria local definida funcionalmente o H reconstrucción C1 separada, sólo tras objetivo/coste y criterio de suficiencia; si no hay hipótesis discriminante, detener, no usar costo hundido como argumento. Mantener seeds1400..1419 y PR draft/main/Nilo0.7 intactos |

**Regla:** nunca actualizar `última subtarea validada` sin prueba enlazada al commit, log/fixture y criterio de aceptación. Si se hace un paso pero no se logra evidencia suficiente, permanece en curso/bloqueado. No marcar «terminada» una etapa porque se produjo un texto sobre ella.

## 2. Estado por fase

| Fase | Estado inicial | Próxima subtarea | Requisito de cierre |
|---|---|---|---|
| E00 | Genoma original del CD comparado con parche; PE32 C1 examinado estáticamente | Reproducir scheduler/química completos si se exige fidelidad bit a bit | [Genoma original](E00_GENOMA_ORIGINAL_COMPARACION.md), [análisis PE32](E09_02F_INFORME_EJECUTABLE.md); G00-H parcial |
| E01 | Validación automatizada | — | CI E01, 19 tests; benchmark en workflow |
| E02 | Validación automatizada | — | CI E02, 8 tests; sin aprendizaje |
| E03 | Validada N | — | [G03 CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727); no replica C1 |
| E04 | Validada como dinámica sináptica aislada | — | [CI E04](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622); no integrado al selector aún |
| E05 | **Parcial / límite negativo confirmado** | Revisar crédito causal | G05 no superada; refuerzo espurio en distractor correlacionado |
| E06 | Validada: invariancia contextual, no creación de conceptos | — | CI 44851722169 |
| E07 | Verificada en modelo experimental | — | [CI E07](https://github.com/mxlzz/Nilo_public/actions/runs/44852027094), sin ventaja demostrada frente a LRU |
| E08 | Verificada dinámica matemática | — | [CI E08](https://github.com/mxlzz/Nilo_public/actions/runs/44852126108) |
| E09 | I3c7h/i aprendió contingencia y funciones locales, pero nunca G05 ACTIVE; I3c7k copia STW a LTW gana sólo4.9pp < gate10pp. I3c7l STOP/PIVOT de mini C1 y separación de H de N; I3c8 [antecedentes](E09_02I_I3C8_ALTERNATIVAS_EXISTENTES_MEMORIA.md) compara reglas tres factores, consolidación multiescala, EWC/SI y Brian2/Nengo, no hay solución turnkey probada bajo los requisitos sin complejidad extra. | Sin nuevo entrenamiento automático. Si surge una hipótesis de suficiencia verificable y de costo acotado, prereg independiente; si no, documentar cierre negativo. H GEN/EXE con preguntas históricas separadas. | [I3c7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md), [I3c8](E09_02I_I3C8_ALTERNATIVAS_EXISTENTES_MEMORIA.md); G05/G09/G00-H ABIERTAS |

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


### 2026-11-20 — NL-LOG-0001 (E00)
- Se leyeron y contrastaron directamente ocho fuentes C1, incluidas dos de los autores (paper Grand/Cliff/Malhotra y `I Am Ron's Brain` fechado 1995).
- Evidencia: [E00_INFORME_HISTORICO_01.md](E00_INFORME_HISTORICO_01.md).
- E00.01 validada; E00.02 solo parcial (se conoce `dad1.gen` pero no hash); E00.03 y E00.07 con base documental; el resto contiene lagunas explicitadas.
- G00-H (réplica fiel): **ABIERTA**; discrepancia de salida sobre umbral y orden exacto de tick.
- G00-N (modelo propio): admite E01 si el motor deja claras sus convenciones. No se resolvieron dudas por suposición.

### 2026-11-20 — NL-LOG-0002 (E01)
- Código experimental nuevo: [kernel.py](../../experiments/neurolab/kernel.py), [tests E01](../../experiments/neurolab/tests/test_kernel.py), [bench.py](../../experiments/neurolab/bench.py).
- En [CI #44850766887](https://github.com/mxlzz/Nilo_public/actions/runs/44850766887), SHA `2d7a8496677702e9364ea0534c1c4ea0b49cef89`, compilación y **19 tests E01 exitosos**.
- Benchmark de 100.000 ciclos incorporado a CI y ejecutado en [run #44850839844](https://github.com/mxlzz/Nilo_public/actions/runs/44850839844); en este registro se confirma paso correcto, no se inventan métricas numéricas del log.
- Cubre activación, umbral dos variantes, excitación/inhibición, saturación, reposo, propagación retardada de 1 tick, determinismo y checkpoint. Sin aprendizaje.
- G01 funcional: **VALIDADA para modelo NeuroLab**, no para reconstrucción byte a byte de Creatures 1.

### 2026-11-20 — NL-LOG-0003 (E02)
- Código de seis neuronas: [circuit.py](../../experiments/neurolab/circuit.py), [8 tests E02](../../experiments/neurolab/tests/test_circuit.py).
- [CI #44850881701](https://github.com/mxlzz/Nilo_public/actions/runs/44850881701), SHA `a267c5b73512ccd594bb2775cf948211614cffe3`, compila y ejecuta **27 métodos de test (19 E01 + 8 E02)**; conclusión `success`.
- Demuestra propagación E→C→D, WTA explícito, empates, inactividad, repeticiones por semilla, variación sin respuesta correcta cableada y pesos estables.
- G02 funcional: **VALIDADA**, siempre sin aprendizaje ni mundo. Etapa siguiente: E03.01.

**Advertencia de trazabilidad:** los SHA de CI corresponden a los commits indicados, no necesariamente al HEAD futuro cuando se agreguen E03+.


### 2026-11-20 — NL-LOG-0004 (E03)
- Pre-registro previo a implementación: [E03_PRE_REGISTRO.md](E03_PRE_REGISTRO.md), fija 20 semillas, 100 episodios iniciales, 160 de inversión, holdouts y controles congelados, tasa de ajuste ±16 por refuerzo.
- Código: [plasticity.py](../../experiments/neurolab/plasticity.py), [e03_protocol.py](../../experiments/neurolab/e03_protocol.py), [tests E03](../../experiments/neurolab/tests/test_plasticity.py).
- [Ejecución CI #44851094727](https://github.com/mxlzz/Nilo_public/actions/runs/44851094727), SHA `ea4cf2de7ba9166edfefb568536f24c2a911bdaf`: **success**, pruebas y evaluación preregistrada completadas sin errores.
- La suite contiene 37 métodos de test (19 E01, 8 E02, 10 E03); los tests de E03 comprueban aislamiento de la contingencia en evaluador, feedback posterior a decisión, ausencia de aprendizaje en baseline congelado, reversión, seeds y checkpoint.
- El runner `run_all` sale con error si no se cumplen simultáneamente ≥18/20 semillas con exactitud ≥0.90 tras aprendizaje, ≥18/20 tras inversión y mejora media ≥0.30 frente al control congelado. Al completarse el paso con `success`, **los tres umbrales preregistrados se alcanzaron**, pero aquí no se inventan valores exactos que no se recuperaron del stdout.
- Resultado: G03 **VALIDADA para el modelo experimental N**, no es aprendizaje químico de C1 ni una mente autónoma general.
- Siguiente: E04.01 (STW/LTW de dos tiempos).

### 2026-11-20 — NL-LOG-0005 (E04)
- Pre-registro previo al código: [E04_PRE_REGISTRO.md](E04_PRE_REGISTRO.md): STW/LTW de modelo propio, refuerzo breve y prolongado, reposo sin recompensa y control de un peso.
- Código: [twin_weight.py](../../experiments/neurolab/twin_weight.py), [tests E04](../../experiments/neurolab/tests/test_twin_weight.py).
- [CI #44851265622](https://github.com/mxlzz/Nilo_public/actions/runs/44851265622), SHA `9b0960667fa27bbc2ba9e0dcf7f0896dcf246151`: `success`. Tests manuales, saturación, recuperación, memoria lenta, inversión sostenida y checkpoint superados.
- **G04 validada solo para la dinámica aislada de STW/LTW de NeuroLab.** No se ha medido todavía si un cerebro que utiliza ese mecanismo generaliza mejor ni se lo presenta como reproducción histórica exacta.
- Siguiente: E05.01 — elegibilidad temporal para una asociación ya existente.

### 2026-11-20 — NL-LOG-0006 (E05)
- Pre-registro previo al código: [E05_PRE_REGISTRO.md](E05_PRE_REGISTRO.md); ecuación propia elegibilidad=floor(3e/4), peso posterior condicionado por floor(32e/255).
- Código: [eligibility.py](../../experiments/neurolab/eligibility.py), [10 tests E05](../../experiments/neurolab/tests/test_eligibility.py).
- [CI #44851485383](https://github.com/mxlzz/Nilo_public/actions/runs/44851485383) para SHA `c24a6c6a21ae4ff313b18cfb0c1dca06dbdfb31b`: `success` (57 métodos de prueba, y evaluación prereg E03 todavía verde).
- Refuerzo sin uso previo: 0; refuerzo inmediato: +32; retraso temporal discreto reduce influencia; elegibilidad y checkpoint deterministas.
- **Caso negativo confirmatorio:** A causa refuerzo, B distrae y se activa después; elegibilidad A=107, B=191; ante premio +1, A termina peso 141 y B peso 151 (ambos desde128). El algoritmo refuerza **más a B**, pese a que B no causó la consecuencia.
- Diferenciar **tests del cálculo esperable: éxito**, de **hipótesis de crédito causal correcto: NO VERIFICADA / FALLA EN ESTE CASO**. **Puerta G05 permanece abierta**, no aprobar hasta abordar limitación por diseño o delimitar el escenario de uso.
- **Trabajo permitido independiente:** E06 solo evaluará detectores de patrones y transferencia con refuerzo inmediato de E03; no integrará ni dependerá de la elegibilidad E05. Registrar antes el diseño y no afirmar que se saltó la puerta G05.
- La elección histórica vs nueva regla correctiva queda abierta para una decisión posterior basada en ensayos, sin imponer una respuesta por comodidad.


### 2026-11-20 — NL-LOG-0007 (E06)
- Pre-registro: [E06_PRE_REGISTRO.md](E06_PRE_REGISTRO.md), con 20 semillas, XOR, contexto C inédito y tres controles (memoria exacta, singleton aditivo, sin plasticidad).
- Implementación: [concepts.py](../../experiments/neurolab/concepts.py), [e06_protocol.py](../../experiments/neurolab/e06_protocol.py), [tests E06](../../experiments/neurolab/tests/test_concepts.py).
- [CI #44851722169](https://github.com/mxlzz/Nilo_public/actions/runs/44851722169), SHA `eeb0945a338b4167008e0138b2a8440b82a55610`: success, pasa tests y criterios preregistrados (≥18/20 semillas con precisión ≥0.90, ventaja media ≥0.20 sobre memorizador y ≥0.15 sobre singleton).
- **Resultado acotado:** detectores conjuntivos **predefinidos** permiten retener decisiones ante señal distractora nueva. No aprende la representación de conceptos, no transfiere a pares esenciales no entrenados.
- E06 fue ejecutada independientemente de E05; no modifica G05 que permanece abierta.

### 2026-11-20 — NL-LOG-0008 (E07.01, primera verificación)
- Paper primario Grand/Cliff/Malhotra: migración de dendritas cuando `strength=0` **sí** parte del modelo presentado; migraciones permanecen en el mismo lóbulo de origen. Un mecanismo *adicional* de competencia «supervivencia del más apto» fue dejado desconectado, **no** toda la migración.
- Guía C1 posterior (fuente secundaria): detalla dos estilos diferentes, Decision-style y Concept-style, y restricciones de duplicados, exclusividad y actividad. La exactitud byte a byte de esas rutinas respecto al ejecutable de 1996 permanece abierta.
- Fuentes directas: [paper de autores](https://eem.foo/ccarchive/Sites/fp.cyberlifersrch.plus.com/articles/agents_%2797_paper.htm) y [C1 Brain Guide](https://zenzoa.com/creatures/c1-brains.html).
- Descubrimiento de [Gene Loom](https://lisdude.com/Creatures/Community/GeneLoom/) (v1.8.0, junio 2026), editor que admite genomas C1: alternativa existente para inspeccionar el `dad1.gen` auténtico **si se dispone legítimamente del archivo**, sin obligar a desarrollar un editor de genomas.
- **E07.01 parcialmente verificada** a nivel de principios y estilos; parámetros y genoma exacto todavía abiertos. El archivo original no fue adquirido ni analizado.


### 2026-11-20 — NL-LOG-0009 (E07)
- [Pre-registro E07](E07_PRE_REGISTRO.md); dos slots, patrones antiguos y nuevos, controles con conexiones fijas y LRU.
- Código: [rewiring.py](../../experiments/neurolab/rewiring.py), [e07_protocol.py](../../experiments/neurolab/e07_protocol.py), [tests E07](../../experiments/neurolab/tests/test_rewiring.py).
- [CI #44852027094](https://github.com/mxlzz/Nilo_public/actions/runs/44852027094), SHA `c6542f53f7656699f871a5757a90060b1667e4ee`, `success`: umbral preregistrado satisfecho.
- Conexiones reutilizadas bajo cupo fijo y olvido de asociaciones anteriores. No se infiere superioridad a LRU ni equivalencia histórica de reglas de atrofia. E07.01: Grand confirma migración cuando strength=0, salvo mecanismo competitivo adicional desconectado.

### 2026-11-20 — NL-LOG-0010 (E08)
- [Pre-registro E08](E08_PRE_REGISTRO.md), dos neuronas recurrentes, controles sin conexiones y con atenuación.
- Código: [recurrent.py](../../experiments/neurolab/recurrent.py) y [tests E08](../../experiments/neurolab/tests/test_recurrent.py).
- [CI #44852126108](https://github.com/mxlzz/Nilo_public/actions/runs/44852126108), SHA `060ecc3d369e18a4627b8c0a7c0bfbab3b3dc671`, `success`.
- Oscilación de dos ticks caracterizada, control sin recurrencia se apaga; no atribuir pensamientos.

### 2026-11-20 — NL-LOG-0011 (E09, auditoría preliminar)
- [E09_AUDITORIA_INTERMEDIA.md](E09_AUDITORIA_INTERMEDIA.md): capacidades parciales comprobadas, sin unificación bajo un cerebro/tick común.
- **G09 abierta**; G05 abierta por atribución equivocada; G00-H abierta por genoma original y reglas históricas contradictorias.
- Próximo trabajo técnico: E09.01 exportar resultados agregados, congelar configuraciones y luego investigar integración con controles.

### 2026-11-20 — NL-LOG-0012 (E09.01 — evidencia congelada)
- Corrida canónica preintegración: [GitHub Actions #44852299967](https://github.com/mxlzz/Nilo_public/actions/runs/44852299967), job `136686250858`, commit ensayado `56cb2e7456103eee7a65cdadc275da01a1869720`, `success`.
- Artefacto Actions `neurolab-metrics` confirmado (ID `14686047092`, retención temporal). Sus cinco resultados JSON se recuperaron del log y están **guardados permanentemente como documentos versionados en GitHub** bajo [resultados/run-44852299967](resultados/run-44852299967/).
- Índice canónico con métricas exactas por fase: [E09_EVIDENCE_INDEX.md](E09_EVIDENCE_INDEX.md).
- E03 exactitud media=1.0, control congelado=0.425, reversión=1.0; E06 conceptos=1.0 vs singleton=0.5375 y memorizador=0.5; E07 migración=1.0 vs fixed=0.5 **y LRU=1.0**, olvido antiguo medio=0.5.
- Se ha cumplido **E09.01 (conservación reproducible de evidencia)**, no E09.02–09.10 ni G09.
- **Intervención necesaria para fidelidad histórica:** obtener `dad1.gen` auténtico de Creatures 1 (o un genoma C1 equivalente con procedencia verificable). Si el usuario prefiere continuar sin ese archivo, el siguiente trabajo debe reconocer que la mente será una variante propia basada en principios documentados, no reconstrucción fiel. Esa decisión no está asumida aquí.


### 2026-11-21 — NL-LOG-0013 (E00.02 — archivo aportado)
- **ZIP inspeccionado:** `Updated C1 V2.zip`, SHA256 `2661f07b33a4d617c723466883ac9dbfc14a4211dad674a6d3cae9a936130d4f`; archivo de usuario, no subido a repo.
- **dad1.gen localizado:** SHA256 `f32c0cac5985d9c71c9a6765b98cd321dd49574f315a1f2813cd4f0bb91babfe`; 20.001 bytes, 320 genes y 9 registros de lóbulos tipo/subtipo 0/0 identificados mediante marcadores de formato C1. La comparación interna con siete genomas del paquete revela identidad byte a byte de sus nueve registros de lóbulos.
- **Origen modificado confirmado** por `readme.txt`: cambio para evitar inmortalidad y corregir envejecimiento; no se afirma originalidad del genoma.
- **Registro exhaustivo y fuentes:** [comentario en issue #102](https://github.com/mxlzz/Nilo_public/issues/102#issuecomment-7064159473).
- E00.02 ha avanzado desde ausencia de archivos concretos a espécimen modificado identificable/hasheado. **G00-H sigue abierta** por falta de referencia original de 1996 y divergencias del ejecutable no resueltas.
- Siguiente subtarea documental: interpretar los nueve genes de lóbulos reales y sus campos SVRule; comparar contra documentación de C1 y prototipo N. No subir ni redistribuir genomas de terceros.


### 2026-11-21 — NL-LOG-0014 (dad1.gen del CD y nueve lóbulos decodificados)
- El usuario aportó `dad1.gen` extraído de `INSTALL/DATA.Z` en la imagen del CD. Archivo analizado: 10001 bytes, SHA-256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. **No se subió el binario**.
- Comparado contra `Updated C1 V2.zip/dad1.gen` (20001 bytes, SHA-256 `f32c0cac5985d9c71c9a6765b98cd321dd49574f315a1f2813cd4f0bb91babfe`).
- 320 marcadores `gene` en ambas; mismos offsets. Solo 15 posiciones byte diferentes (7834,7835,7837,7839–7850); el cambio es el último gen (reacción → receptor químico) y posición de `gend`. Los nueve genes neuronales son **idénticos byte por byte**.
- [Informe técnico E00-H02](E00_GENOMA_ORIGINAL_COMPARACION.md): nueve lóbulos 112+16+40+16+40+32+16+40+640=**952** posiciones, SVRules extraídas, conectividad Decision (128+128 dendritas por neurona), Attention (1+1), Concept (1–3).
- [Mapa E00-H03](E00_MAPA_NEUROQUIMICO_C1.md): seis receptores y tres emisores cerebrales originales, con químicos identificados por códigos numéricos. No se asignan nombres funcionales no contrastados.
- Código de inspección reproducible [c1_genome_inspector.py](../../experiments/neurolab/c1_genome_inspector.py) y [siete pruebas sintéticas](../../experiments/neurolab/tests/test_c1_genome_inspector.py): primer CI falló por tratar `gend` como parte de un gen terminal; causa documentada, corregida sin tocar datos. [CI corregida #44919429305](https://github.com/mxlzz/Nilo_public/actions/runs/44919429305): **success**, conjunto de tests de NeuroLab validado.
- La estructura **genética** C1 queda muy bien especificada para este archivo aportado; G00-H **ejecutable** permanece abierta en cálculos hardcoded, reloj y parámetros/identidad química exacta. No atribuir fidelidad total a NeuroLab E01–E08.
- Próximo paso: E09.02a definir microcircuito de prueba con las SVRules y conexiones históricas verificables, haciendo explícitas las convenciones temporales propias y controles necesarios.


### 2026-11-21 — NL-LOG-0015 (E09.02a–e, línea experimental y evidencia)

- **E09.02a**: tres SVRules originales `ANDTYPE0`, `STATE PLUS TYPE0 MINUS TYPE1`, `STATE PLUS TYPE0 PLUS TYPE1` decodificadas y probadas con oráculos; [especificación](E09_02A_PRE_REGISTRO_SVRULE_C1.md), [módulo](../../experiments/neurolab/c1_svrule_subset.py).
- **E09.02b**: circuito mínimo de cinco unidades P0,P1,C,D0,D1, sin aprendizaje, con reglas neuronales C1; [protocolo](E09_02B_MICROCIRCUITO_PRE_REGISTRO.md), [código](../../experiments/neurolab/c1_microcircuit.py), tests CI verificados.
- **E09.02c**: primer refuerzo fijo ±16, aprende primera preferencia con precisión1.0 pero **falla inversión** (precisión0.30, 6/20 semillas). [Registro negativo](E09_02C_RESULTADO_NEGATIVO.md).
- **E09.02d**: con exploración ε=0.10, sube inversión a0.80 y16/20, pero **NO supera** criterio18/20. [Registro negativo](E09_02D_RESULTADO_NEGATIVO.md).
- **E09.02e**: idénticas cinco unidades y política original, pero con 4 sinapsis STW/LTW (reglas NUMÉRICAS de E04, no ejecutable C1). Aprendizaje original1.0, reversión1.0, **20/20 semillas** superan ambas puertas. Control congelado media0.4925. [Reporte completo](E09_02E_RESULTADOS_STW_LTW.md).
- **Corrida canónica:** [CI #44920963462](https://github.com/mxlzz/Nilo_public/actions/runs/44920963462), commit probado `7066bef28ff6788cb89b4dc85063238e40f0331b`, `success`; resultados íntegrales con pesos por semilla en [E09c](resultados/run-44920963462/e09c_negative.json), [E09d](resultados/run-44920963462/e09d_negative.json), [E09e](resultados/run-44920963462/e09e_stw_ltw.json). El job preserva ambos controles negativos sin alterar su criterio preregistrado; los tests se etiquetan `expectedFailure` para los resultados negativos conocidos, nunca aprobados como G09.
- **Genética neuroquímica C1:** [químicos49/50/51/52/53/70](E00_MAPA_NEUROQUIMICO_C1.md) verificados con nombres históricos; [reacciones de drive y refuerzo](E00_QUIMICA_REFUERZO_C1.md) decodificadas de `dad1.gen`; [lector de genes de reacción](../../experiments/neurolab/c1_reaction_inspector.py) y tests agregados. No se subieron archivos del juego.
- **Estado crítico:** una red pequeña con dos velocidades funciona en la tarea sintética, pero las tasas de relajación experimental NO son las de la máquina de 1996 verificadas; no se demostró una mente C1 fiel ni unificación E01–E08 en un solo sistema; crédito causal diferido E05 sigue fallando. **Siguiente E09.02f:** reproducción/supervisión de un tick sináptico C1 y comparación contra nuestro E09e; para equivalencia exacta se necesita inspección del ejecutable original del CD.



### 2026-11-21 — NL-LOG-0016 (Creatures.exe y fases f.1–f.4)

- **Binario original de usuario examinado estáticamente**: `Creatures.exe` PE32 GUI x86, 387072 bytes, SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`. Metadata PE: timestamp 1997-08-06 y versión 1.0.0.1. **No ejecutado ni subido a GitHub**.
- [Informe forense con offsets/direcciones](E09_02F_INFORME_EJECUTABLE.md).
- **f.1** `c1_runtime_math.py`: aritmética SVRule por operación con saturación byte, multiplicación y señal de dendrita `>>8`, salida `max(0,state-threshold)`, competencia WTA verificada; [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44929478194).
- **f.2** `c1_decay_math.py`: helpers decay/relax de VA0x419E40 y0x419E90, dos tablas de32 valores por rate y máscaras temporales, LTW cambia una unidad cuando tick%rate=0; [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44929737314).
- **f.3** `c1_dendrite_tick.py`: sus +4/wrap o decay, refuerzo STW según sus×chemical >>8, relajación STW hacia LTW, LTW ±1 con tasa genética. Test inicial con error de fixture de rate0, corregido sin modificar implementación; [CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44930063295).
- **f.4** `c1_strength.py`: ganancia de fortaleza según regla y tasa, pérdida decremental y reinicio de campos cuando se agota. [CI verde](https://github.com/mxlzz/Nilo_public/actions/runs/44930221183): 188 tests, 2 fallos experimentales **expectedFailure** correspondientes a E09c/d, sin otros errores.
- **Hallazgo f.5 preliminar**: en el mismo ejecutable las rutinas VA0x404A80 y0x404B90 gestionan migración/reconexión con criterios distintos (Decision-style y Concept-style), aún sin especificación/reimplementación. No suponer algoritmo de E07 equivalente.
- **Divergencia cuantitativa** respecto de E09e preservada: con STATE80+TYPE0 240−TYPE1 200, la convención vieja devuelve120 y la del binario55. El primer refuerzo con sus0/chemical255 en tick1 da STW3/LTW0 bajo dinámica parcial C1, contra STW26/LTW1 del modelo experimental E09e. **Sus resultados previos siguen válidos solo para el modelo anterior**.
- **Próximo E09.02f.5**: caracterizar migración desde los dos bloques x86 y diseñar test falsable. Después E09.02g microcerebro C1 con reglas numéricas/temporales corregidas; no saltar a 952 unidades sin justificación.
- G00-H (fidelidad completa), G05 (crédito causal) y G09 (mente mínima integrada) permanecen ABIERTAS.



### 2026-11-21 — NL-LOG-0017 (E09.02f.5 — mapeo preliminar de migración)

- [Mapa de migración](E09_02F_05_MIGRACION_ANALISIS.md) redactado a partir de inspección de las direcciones x86 **0x404A80** (tipo1, Decision-style) y **0x404B90** (tipo2, Concept-style).
- Tipo1 reutiliza slot con strength0 y elige fuente entre neuronas candidatas; evita fuentes duplicadas, reinicia LTW/STW y strength en rangos genéticos y puede no reconectar.
- Tipo2 reordena candidatos y verifica combinaciones de fuentes, con criterios internos de firmas suma/producto y reglas para evitar ciertas duplicaciones; en casos de fallo los pesos/fortaleza permanecen sin conexión.
- **No se implementaron aún esas rutas** porque falta reconstruir sus firmas, PRNG y condiciones específicas. No confundir esto con el recableado experimental E07, que no aventajó a LRU.
- Próxima subtarea f.5a: especificación completa verificada y oráculos; f.5b: implementación por tipo. Ninguna intervención del usuario requerida para continuar inspección estática.


### 2026-11-21 — NL-LOG-0018 (migración, SVRule y microred C1 de cinco unidades)
- Ruta de migración tipo1 Decision y tipo2 Concept analizadas, [preregistradas](E09_02F_05A_MIGRACION_PRE_REGISTRO.md), [implementadas con rand inyectado](../../experiments/neurolab/c1_migration.py), verificadas contra oráculos de duplicado, checksum, exclusividad y fuentes. No reproduce estado global CRT ni scheduler de Norn; [CI 202 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44932539848).
- [Intérprete SVRule](../../experiments/neurolab/c1_svrule_runtime.py) con snapshot previo, [CI](https://github.com/mxlzz/Nilo_public/actions/runs/44932796473). [Dendrita integrada](../../experiments/neurolab/c1_synapse_integrated.py) con parámetros exactos de genes Decision/Concept, [CI 223 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44933002373).
- [g.2/g.3 pruebas](E09_G_MICRORED_RESULTADOS.md): cinco unidades, 20 semillas, WTA y concepto del tick anterior; g.3 `random_tie` 20/20 aprende y revierte con control congelado0.4925; `first_index` no acredita ventaja inicial. [CI 246 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44933734902), [JSON](resultados/run-44933734902/e09g3.json).
- G00-H y G09 global abiertas, no hay emulación completa ni mente autónoma.

### 2026-11-21 — NL-LOG-0019 (robustez E09g.4)
- [Pre-registro](E09_02G_04_ROBUSTEZ_PRE_REGISTRO.md), [resultados exactos](E09_02G_04_RESULTADO_ROBUSTEZ.md), [JSON por semilla](resultados/run-44934175507/e09g4.json), [CI 256 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44934175507).
- Contrabalanceado D0→D1 y D1→D0: sin ruido, delay1/3, **20/20 semillas** cumplen ambas puertas. Con noise10%: **16/20** y **17/20** semillas cumplen, NO aprobadas. Delay3 sin distractores no resuelve el problema de crédito causal E05.

### 2026-11-21 — NL-LOG-0020 (discriminación contextual E09g.5)
- [Pre-registro](E09_02G_05_DOS_CONCEPTOS_PRE_REGISTRO.md), seis unidades con dos conceptos predefinidos y ocho dendritas de decisión, secuencias balanceadas de contextos mezclados. [CI 269 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44934616857), runner científico **passed=false**.
- [Informe](E09_02G_05_RESULTADO_DOS_CONCEPTOS.md) y [JSON](resultados/run-44934616857/e09g5.json). Precisión steady neuronal 0.9671875 A y0.9302083 B; frozen0.51927/0.51146, blind0.49948/0.49688, **tabular 1.0/1.0**. Solo **12/20 semillas** cumplen ambos umbrales de0.90, contra criterio≥18/20. **No ajustar retrospectivamente.**
- g.5a analiza por tick 8 semillas fallidas (0,2,3,4,8,16,17,19), especialmente errores cerca de transiciones de contexto. **Post hoc exploratorio, no hipótesis confirmatoria**.
- Siguiente después del diagnóstico: preregistrar comparación de crédito causal diferido entre contextos; criterio de utilidad debe reconocer que el modelo tabular sencillo ya vence a la red. Sin cambios en `main` ni integración en motor Nilo.

### 2026-11-21 — NL-LOG-0021 (diagnóstico E09g.5a y ablación g.6)
- [g.5a, informe post hoc](E09_02G_05A_DIAGNOSTICO_POSTHOC.md): precisión en primer tick tras cambio de contexto 0 (A) y 0.0111 (B); hay errores persistentes más allá de la latencia de 1 tick. [CI g.5a](https://github.com/mxlzz/Nilo_public/actions/runs/44934965506).
- [g.6, preregistro](E09_02G_06_ABLACIONES_TEMPORALES_PRE_REGISTRO.md), [resultado](E09_02G_06_RESULTADO_ABLACIONES_TEMPORALES.md), [CI #44938181968](https://github.com/mxlzz/Nilo_public/actions/runs/44938181968): reset neuronal N o precarga de Concept W mejoran parcialmente; ambos juntos NW logran 1.0 en A/B para 20/20 semillas. **NW es un oráculo artificial al inicio de cada bloque, NO una mente que se autorregula.** Paridad con E09g.5 preservada.
- Resultado: diagnóstico validado como descripción del banco; no se modifica gate de g.5, no se implementa mecanismo interno.

### 2026-11-21 — NL-LOG-0022 (auditoría de crédito E09g.7)
- [Preregistro](E09_02G_07_CREDITO_CAUSAL_PRE_REGISTRO.md), [informe](E09_02G_07_RESULTADO_LEDGER_CAUSAL.md), [CI #44938471293](https://github.com/mxlzz/Nilo_public/actions/runs/44938471293): 10.240 ticks de entrenamiento, 10.200 pulsos comparables; **652 discrepancias** entre Concept de decisión previa y Concept de plasticidad actual, 331 con cambio STW. Se concentran en posición1 tras cambio contextual; LTW no cambia en esas observaciones.
- Los estados finales por semilla/fase del entrenamiento instrumentado coinciden exactamente con E09g.5. Resultado: descripción temporal verificada, NO demostración de que cada peso cambiara por ese pulso ni cierre de G05.

### 2026-11-21 — NL-LOG-0023 (E09g.8, resultado desfavorable según regla)
- [Pre-registro g.8](E09_02G_08_PULSOS_PAREADOS_PRE_REGISTRO.md), [informe](E09_02G_08_RESULTADO_PULSOS_PAREADOS.md), [CI #44938791056](https://github.com/mxlzz/Nilo_public/actions/runs/44938791056): control original C, supresión dirigida G en tick1 de cambio, sham S en tick2. Omisiones emparejadas 319 (A) y333 (B) por brazo. Steady B C0.9302083, G0.9614583, S0.9322917. Puerta G−S B≥0.03 **FALLA**: diferencia +0.0291667; precisión temprana G empeora. Conteos conjuntos C12/20, G16/20, S13/20.
- Resultado: experimento ejecutado sin errores de software, **hipótesis práctica NO aprobada**. No ajustar parámetros ni retroaprobarlo.

### 2026-11-21 — NL-LOG-0024 (E09g.9, replicación fuera de muestra)
- [Pre-registro de 80 semillas 20..99](E09_02G_09_REPLICACION_NUEVAS_SEMILLAS_PRE_REGISTRO.md), código reutiliza g.8 sin cambios; [reporte y limitaciones](E09_02G_09_RESULTADO_REPLICACION.md), [JSON original por semilla versionado](resultados/run-44939075550/e09g9.json), [CI #44939075550](https://github.com/mxlzz/Nilo_public/actions/runs/44939075550), commit ensayado `fb31ad91079f0454a4b8ac730455832bbdea44c3`, **success, 292 tests y 2 expectedFailure históricos**.
- Media `steady_B(G-S)` +0.0319010, IC bootstrap pareado95% [0.0161458, 0.0500], umbral prospectivo cumplido; `steady_A(G-S)` +0.0311198. 46/80 C, 60/80 G, 44/80 S superan≥0.90 conjuntamente. B: 35 mejores, 13 peores y32 iguales; mediana0. `early` G empeora frente a C/S.
- Resultado: **replicación positiva del efecto medio de un filtro de feedback EXTERNO**, no solución autónoma, no restauración del gate g.8 ni cierre G05/G09. Prioridad siguiente: g.10 evaluar si una memoria de procedencia verdaderamente interna justifica complejidad frente a tabla Q2×2.
- Estado: PR #103 permanece **draft** y branch de NeuroLab aislada; `main` y motor Nilo 0.7 intactos. No se redistribuyeron archivos originales del juego.

### 2026-11-21 — NL-LOG-0025 (g.10a: compuerta intrínseca mínima, factibilidad)
- [Preregistro antes del código](E09_02G_10A_GATE_INTERNO_PRE_REGISTRO.md), [implementación](../../experiments/neurolab/e09_intrinsic_gate.py), [tests](../../experiments/neurolab/tests/test_e09_intrinsic_gate.py). IG recibe únicamente estado neuronal, memoria del Concept anterior, entrada sensorial y químico pendiente: **no conoce bloques ni respuestas correctas**.
- [CI #44939579597](https://github.com/mxlzz/Nilo_public/actions/runs/44939579597), commit probado `91a67678aeaf1be8b8356ac4a0441aaa0db93afd`, **success: 300 tests, dos expectedFailure históricos**. [Informe](E09_02G_10A_RESULTADO_GATE_INTERNO.md), [JSON por semilla100..119](resultados/run-44939579597/e09g10a.json) permanente.
- **20/20 paridades IG=G exactas:** estados neurales/sinápticos finales, pulsos químicos pendientes, supresiones y holdout A/B. A328 supresiones, B331. Steady B C0.9229167 vs IG/G0.965625; C12/20 e IG/G17/20 superan ≥0.90 en ambas; early de IG empeora.
- **No** es crédito causal general, ni puerta G05/G09 aprobada, ni un mecanismo observado en el genoma/ejecutable C1. El baseline Q2×2 sigue siendo más eficaz en la tarea de dos señales.
- **Siguiente estudio:** no seguir ajustando esta tarea simple; preregistrar test con distractores y feedback1–3 ticks y baseline de memoria causal. `main`, Nilo y PR draft sin merge.

### 2026-11-21 — NL-LOG-0026 (g.10b: recompensa diferida y distractores)
- [Preregistro](E09_02G_10B_DEMORA_DISTRACTORES_PRE_REGISTRO.md), [código](../../experiments/neurolab/e09_delayed_distractors_protocol.py), [resultado](E09_02G_10B_RESULTADO_DEMORA_DISTRACTORES.md), [JSON por semilla](resultados/run-44942700990/e09g10b.json), [CI 308 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44942700990), commit ensayado `738e002a85b4346eb44af0b83ebf889b5d6b8345`, success.
- 40 semillas120..159, dos fases con 60 entrenamiento/36 holdout, 4 ticks target, 1–3 distractores y feedback en el tick siguiente. C16/40 e IG6/40 cumplen ≥0.90 ambas fases vs Q40/40 y F0/40. **C/IG gates fallidas**, Q recibe procedencia explícita privilegiada. IG suprime exactamente 800/2400 pulsos por fase, pero su rendimiento cae. No recalibrar retrospectivamente.
- El criterio opcional de parada forzosa (ventaja media Q≥+0.15) NO se activó: +0.1316; se recomienda detener tunings por el costo de oportunidad, no falsear esa puerta.

### 2026-11-21 — NL-LOG-0027 (g.10c: susceptibilidad ya existe)
- [Preregistro post hoc explícito](E09_02G_10C_SUSCEPTIBILIDAD_PRE_REGISTRO.md), [auditoría](../../experiments/neurolab/e09_eligibility_audit.py), [informe](E09_02G_10C_RESULTADO_ELEGIBILIDAD.md), [resumen JSON](resultados/run-44943178871/e09g10c_summary.json), [CI 313 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44943178871), commit `7ec6fc0e0a8bef52886962dddad64350da0885a6`, success.
- 4800 eventos en 40 semillas, paridad exacta g.10b. Susceptibilidad de dendrita de contexto/acción originales >0 en el 100% de las llegadas. Frente a pulso ZERO en el mismo estado, con 3 distractores el efecto del pulso en STW objetivo disminuye y en distractor aumenta, comparado con 1 distractor. No significa atribución correcta exclusiva ni demuestra causa futura.
- [Evaluación de alternativas E09g.11](E09_02G_11_ALTERNATIVAS_Y_PRIORIDAD.md): C1 ya tiene elegibilidad local; tabla Q usa información causal privilegiada; TD(lambda) existe pero no se justifica agregar otra traza aún. Próxima prioridad: reloj/bioquímica C1 históricos E09h.1. Binario original no accesible en los archivos de este proyecto/chats actuales para ampliar inspección estática; no pedir hasta que se precise.
- PR #103 permanece draft, main/Nilo no modificados.

### 2026-11-21 — NL-LOG-0028 (E09h.1, orden de actualización histórico)
- Los originales EXE 387072 bytes SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7` y GEN10001 bytes SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4` fueron recibidos nuevamente y coincidieron con E09f/E00, inspeccionados localmente **sin subirlos a GitHub**.
- [Preregistro](E09_H_01_ORDEN_CEREBRO_QUIMICA_PRE_REGISTRO.md), [verificador](../../experiments/neurolab/e09_historical_timing_audit.py), [JSON de evidencia binaria local](resultados/e09h1_inspeccion_estatica_original.json), [informe](E09_H_01_RESULTADO_ORDEN_CEREBRO_QUIMICA.md), [CI 318 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44944783092) success, 2 expectedFailure históricos.
- 12 firmas de instrucción y 10 destinos E8 comprobados en EXE. Ruta regular criatura: cerebro→bioquímica→conducta; ruta alternativa invierte cerebro/química. Lóbulos1..5,0,6+ y etapas químicas emisor→receptor→reacción→decaimiento. **Orden estático verificado; frecuencia real del scheduler no.**
- Resultado: E09h.1 completada **solo** como verificación estática delimitada; G00-H/G05/G09 sin cerrar.

### 2026-11-21 — NL-LOG-0029 (E09h.2, cinética de reacciones C1)
- [Preregistro](E09_H_02_REACCIONES_QUIMICAS_PRE_REGISTRO.md), [código](../../experiments/neurolab/e09_historical_reaction_math.py), [tests](../../experiments/neurolab/tests/test_e09_historical_reaction_math.py), [informe](E09_H_02_RESULTADO_REACCIONES_QUIMICAS.md), [evidencia original](resultados/e09h2_reacciones_genoma_original.json), [CI325 success](https://github.com/mxlzz/Nilo_public/actions/runs/44945152541), 2 expectedFailure.
- 58 reacciones originales. Se verificó que el loader x86 reubica tasa de último byte serializado a offset+4 del registro runtime. Capacidad según reactivos, extent=capacidad-decay(capacidad,tasa,tick), consumo/generación saturados. **Orden de reacciones en el mismo tick importa:** gen71→111 genera Reinforcement51 y Echo54 desde Reward49 generado ese mismo tick; orden invertido no.
- Resultado: **aritmética de reacción aislada verificada con fixtures**, no bioquímica de Norn integrada.

### 2026-11-21 — NL-LOG-0030 (E09h.3, recepción química → locus)
- [Preregistro original](E09_H_03_RECEPTORES_QUIMICOS_PRE_REGISTRO.md), [código](../../experiments/neurolab/e09_historical_receptor.py), [tests](../../experiments/neurolab/tests/test_e09_historical_receptor.py), [resultado](E09_H_03_RESULTADO_RECEPTORES.md), [JSON original](resultados/e09h3_receptores_genoma_original.json), [CI success332 tests](https://github.com/mxlzz/Nilo_public/actions/runs/44945435224), dos expectedFailure.
- 43 receptores originales y seis cerebrales, incluido Reward49/Punishment50 de Decision. El efecto `(available*gain)>>8` produce para concentración12 y gain255 el byte11. **Errata**: prereg E09h.3 esperaba receptor126 output1 con pool52=5, pero el resultado correcto es0; [CI inicial fallida](https://github.com/mxlzz/Nilo_public/actions/runs/44945392755) detectó el error, se corrigió fixture sin alterar fórmula ni prereg.
- Resultado: etapa de transferencia de receptor verificada **sin probar aún que el locus esté correctamente vinculado a CHEM0..3**. Mantener E09h.4 como próximo paso, sin modificar Nilo ni fusionar PR#103.


### 2026-11-21 — NL-LOG-0031 (E09h.4, enlace de receptor a CHEM; PARCIAL)
- [Preregistro](E09_H_04_ENLACE_LOCI_PRE_REGISTRO.md) se guardó **antes** del código, commit `ed66c8ab482d3d55d342fd4a98671a784d82abb2`.
- Fuente [CDN/LCUS](https://lisdude.com/cdn/76.html) confirma receptor locus13–16 = CHEM0–3 por lóbulo; guía [C1 Brain](https://zenzoa.com/creatures/c1-brains.html) confirma operandos SVRule5–8 y carga de los cuatro CHEM de ese lóbulo.
- [Adaptador](../../experiments/neurolab/e09_historical_locus.py), [tests](../../experiments/neurolab/tests/test_e09_historical_locus.py), [resultado condicionado](E09_H_04_RESULTADO_ENLACE_LOCI.md), commit de tests `2ef85398502ff67b7a40f7106f6277394b989625`; [workflow](https://github.com/mxlzz/Nilo_public/actions/runs/44947076331) **success integral** (339 tests, 2 expectedFailure); únicamente pruebas de adaptador y regresión, no nuevos bytes de EXE.
- Oráculos del fixture CD h.3: Decision6 CHEM=(11,11,5,16), Concept8 CHEM=(0,0,0,0), con pool de ejemplo; controles de aislamiento, canales ausentes, duplicados y no mutación. Son verificaciones de **compatibilidad documental**, no memoria física C1.
- Acceso a binarios: Biblioteca localizó ambas copias originales por metadatos, pero falló la materialización de bytes. No se realizaron nuevas lecturas x86, y por eso la **puerta G-H4-X86 sigue abierta**. Siguiente tarea exacta: inspeccionar asignación de puntero receptor→lobe CHEM y su snapshot de SVRule cuando exista acceso real al ejecutable original.
- PR #103 sigue draft; main/Nilo 0.7/G00-H/G05/G09 intactos.


### 2026-11-21 — NL-LOG-0032 (E09h.4-X86, enlace verificado)
- Fuente directa: nueva copia del EXE enviada por usuario, 387.072 bytes, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7; inspeccionado localmente en estático. No ejecutado ni subido.
- [Evidencia x86 original](resultados/e09h4_inspeccion_estatica_original.json), [verificador](../../experiments/neurolab/e09_historical_locus_audit.py), [informe](E09_H_04_RESULTADO_ENLACE_LOCI.md) y tests: 31 instrucciones, vtable del resolver en 0x43302C→0x4030E0; locus13..16→+0xC3..+0xC6 en lóbulo 0xC8; código de receptor escribe mediante puntero guardado y la SVRule lee esos bytes como opcodes5..8.
- Hallazgo adicional: loader inicializa destino con nominal en 0x421ACF. Se añadió función de nominales aislada y controles sobre los seis genes previamente archivados de h.3. Los genes originales no fueron reanexados en esta intervención; no afirmar relectura de GEN.
- [CI final #44947923270](https://github.com/mxlzz/Nilo_public/actions/runs/44947923270): **success, 348 tests, 2 expectedFailure históricos**. CI solo usa fixtures y código, sin exe original; las firmas reales fueron verificadas localmente.
- **G-H4-X86 validada en alcance estático, E09h.4 cerrada**; G00-H/G05/G09 pendientes; no hay cerebro integrado ni conducta real certificada. PR #103 draft, main y Nilo 0.7 sin cambios.
- Siguiente **E09h.5**: preregistro de emisores y vinculación a concentraciones, desde EXE original; luego implementación aislada si la evidencia lo permite. No ampliar redes ni extrapolar resultados g.10.


### 2026-11-21 — NL-LOG-0033 (E09h.5, emisores y errata preregistrada)
- [Preregistro H5](E09_H_05_EMISORES_PRE_REGISTRO.md) escrito antes de codificar. Inspección estática del mismo EXE original SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7: **32 firmas de instrucciones**, método virtual 0x4030E0, emisor kind1, loci1/2→lobe+0xC1/C2, escritura al pool y reset de fuente.
- [Auditor reejecutable](../../experiments/neurolab/e09_historical_emitter_audit.py), [fixture x86 derivado](resultados/e09h5_inspeccion_estatica_original.json), [función aislada](../../experiments/neurolab/e09_historical_emitter.py), [tests](../../experiments/neurolab/tests/test_e09_historical_emitter.py), [resultado](E09_H_05_RESULTADO_EMISORES.md).
- **Errata preservada:** el preregistro supuso que chemical0 no consumiría origen, pero las ramas x86 0x421EEF y 0x421F24 saltan igualmente a reset por flag1 tras superar filtros. Test demuestra consumo sin pool. No se corrigió el preregistro retroactivamente.
- [CI #44948424321](https://github.com/mxlzz/Nilo_public/actions/runs/44948424321) **success: 362 tests, 2 expectedFailure históricos**. CI sintético y análisis estático original local, sin binarios en GitHub.
- Tres genes cerebrales 123/124/125 provienen del mapa de GEN extraído E00 anterior, **no** de relectura de bytes GEN en este chat. Valor fuente80→emisión79 es un ejemplo artificial, no una lectura de Norn real.
- **G-H5-X86 + G-H5-MATH cerradas en alcance acotado; G-H5-GEN con procedencia documental E00 y sin revalidación directa nueva; G00-H/G05/G09 abiertas**. PR #103 draft, main y Nilo 0.7 sin cambios. Siguiente **E09h.6 scheduler y reloj, previo preregistro**.


### 2026-11-21 — NL-LOG-0034 (E09h.6a/b, flujo y reloj nominal)
- [Preregistro global](E09_H_06_SCHEDULER_PRE_REGISTRO.md) y [preregistro de timer](E09_H_06B_CADENCIA_PRE_REGISTRO.md) conservados; **ambos se escribieron antes de sus respectivos auditores**.
- **h.6a:** inspección del EXE original, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7; **24 firmas x86 y 8 direct calls**. Rama Norn+0x2CBC separa ruta regular y alternativa; Norn+0x2CCC omite cerebro y conducta pero no química; contador Norn+0x2C20 compartido antes de incremento. Bucle mundial usa fases0..4 y stride4; index4,8,... aparece en más de una fase; observación estática, no diagnóstico de bug.
- [Informe h.6a](E09_H_06A_RESULTADO_FLUJO_SCHEDULER.md), [auditor](../../experiments/neurolab/e09_historical_scheduler_audit.py), [datos derivados](resultados/e09h6a_flujo_original.json).
- **h.6b:** en EXE original, **17 firmas + 7 llamadas + 6 campos MFC**; USER32.SetTimer ID1 de 90 ms en 0x411F63 y KillTimer en 0x411F7F, WM_TIMER 0x113→0x418960→world tick 0x4247B0. Otro SetTimer500ms en ventana distinta, NO confundir. [Informe h.6b](E09_H_06B_RESULTADO_CADENCIA.md), [auditor](../../experiments/neurolab/e09_historical_timer_audit.py), [fixture](resultados/e09h6b_cadencia_original.json).
- [CI #44949141624](https://github.com/mxlzz/Nilo_public/actions/runs/44949141624) **success integral: 374 tests, 2 expectedFailure históricos**. Los tests del auditor usan memoria/importaciones PE sintéticas; la verificación auténtica fue local sin publicar ni ejecutar juego.
- **Puertas:** G-H6-FLOW verificada solo en rutas directas; G-H6-CLOCK-NOMINAL verificada; **G-H6-CLOCK EFECTIVA / G00-H / G05 / G09 ABIERTAS**. No se ha medido un ritmo real de Norn. PR#103 permanece draft, main/Nilo 0.7 sin cambios.
- Próximo punto de decisión técnica: ¿es necesaria fidelidad temporal en segundos antes de montar tick de pruebas integrado, o alcanza tick lógico explícito sin afirmar equivalencia de C1? Si se exige fidelidad, ampliar trazas/medición en vez de extrapolar 90ms directamente.

### 2026-11-21 — NL-LOG-0035 (E09.02i-I1/I2/I1b; no nueva capacidad conductual)
- **Decisión metodológica N:** reloj lógico sin segundos para evaluar acoplamiento mínimo; no se altera G-H6-CLOCK efectiva. [Preregistro](E09_02I_INTEGRACION_QUIMICA_PRE_REGISTRO.md) commit b9c9c56e279f9bb442aaa09e5ac0b857f3ae4481.
- [I1](E09_02I_I1_I2_RESULTADOS.md): puente inmutable emisor→receptor→reacción; test con gen111 muestra que Reinforcement51 fabricado en reacción no llega a receptor hasta otra invocación; [CI success383 tests + 2 expectedFailure](https://github.com/mxlzz/Nilo_public/actions/runs/44951342148). No aprendizaje probado.
- [I2](E09_02I_I1_I2_RESULTADOS.md): seis unidades preexistentes acopladas unidireccionalmente a CHEM de Decision del tick previo, checkpoint conjunto reproducible, sin conexión inventada de winner-output a source loci, Concept CHEM trazado pero no consumido por plasticidad; [CI success391 + 2 expectedFailure](https://github.com/mxlzz/Nilo_public/actions/runs/44951467547).
- [I1b prereg](E09_02I_1B_POOL_DECAY_PRE_REGISTRO.md): bytes EXE originales SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7 verificaron **15 firmas x86 + call 0x4221ED→0x419E40**; bucle256 químico byte0/rate byte1, stride2. [Módulo y auditor](E09_02I_I1B_RESULTADO_POOL_DECAY.md), [CI401 success + 2 expectedFailure](https://github.com/mxlzz/Nilo_public/actions/runs/44951833784). Tasas genómicas de los 256 químicos NO recuperadas; módulo exige rates explícitos, tests sintéticos.
- **G-I1, G-I2, G-I1b-MATH/X86 cerradas solo técnicamente; G-I1b-RATES, G-H6-CLOCK efectiva, G00-H, G05, G09 ABIERTAS.** Ningún benchmark conductual I3 ejecutado, no afirmar victoria de aprendizaje. PR#103 draft, main/Nilo0.7 intactos.
- Próxima unidad preregistrada: I3 benchmark sobre tasas sintéticas explícitas con controles y no-fidelidad histórica, sin nuevas neuronas ni ajuste de pesos. Antes del experimento fijar cohortes, dosis, rates, fuentes y pruebas negativas.


### 2026-11-21 — NL-LOG-0036 (I3 no supera criterio, I3a en curso)
- [Preregistro I3](E09_02I_I3_BENCHMARK_PRE_REGISTRO.md) anterior al runner. 20 semillas nuevas200..219; 60 entrenamiento +36 holdout por fase A/B con reversión, retardo1–3, M química, F congelado químico, C pulsos directos no equivalentes, Q tabla con procedencia privilegiada.
- [Run I3 #44952276187](https://github.com/mxlzz/Nilo_public/actions/runs/44952276187) terminó success de **software**, NO la hipótesis. Media M primera0.513889 e invertida0.534722; F0.5125/0.534722; C0.890278/0.845833; Q1/1. M−F=0.00069444; 0/20 M≥.90 en ambas fases. **G-I3 científica FALLIDA**, conservar [informe negativo](E09_02I_I3_RESULTADO_NEGATIVO.md).
- [Resumen JSON](resultados/e09i3_resultado_resumen.json), artefacto I3 ID14725468833 con resultados completos por semilla y 90 días de retención, enlace al run. M tuvo 71 y75 decisiones objetivo no emitidas en entrenamiento de fases A/B respectivamente; no hubo concentraciones255 en los puntos finales de ensayo medidos (Reward/Punishment max25, Reinforcement max109). No inferir causalidad desde esto.
- La tasa40 en 256 químicos y dosis80 fueron **sintéticas y preregistradas**, no tasas GEN. No hubo ajuste posterior. Las referencias C y Q no igualan temporalidad o privilegios de información con M. No afirmar que C1 histórico fracasa.
- [I3a preregistrado posthoc](E09_02I_I3A_DIAGNOSTICO_POSTHOC_PRE_REGISTRO.md) para conteos read-only de susceptibilidad/CHEM/reinforcement_effect/STW, replay de mismos estados sin alterar neuronal; **todavía no declarar conclusión I3a** sin CI y JSON.
- Decisión: priorizar mecanismo y atribución antes de tunear hiperparámetros o sumar neuronas. G00-H/G05/G09 y tasas históricas abiertas. PR#103 draft, main/Nilo0.7 intactos.


### 2026-11-21 — NL-LOG-0037 (I3a diagnóstico completado, sin victoria conductual)
- [Preregistro observacional](E09_02I_I3A_DIAGNOSTICO_POSTHOC_PRE_REGISTRO.md) se escribió ANTES de ejecutar el observador. Se repitieron exactamente las 20 semillas I3, misma secuencia, recompensa, plasticidad y tasa40; para cada sinapsis/tick se llamó la función original update_c1_synapse sobre estado anterior y se exigió igualdad con la transición neural auténtica. Todos los snapshots de sinapsis y estados por fase coincidieron: **observación no perturbativa**.
- [Run específico #44952704490](https://github.com/mxlzz/Nilo_public/actions/runs/44952704490) success; [informe detallado](E09_02I_I3A_RESULTADO_DIAGNOSTICO.md), [resumen JSON](resultados/e09i3a_resumen.json). Artefacto per-seed 14726098025 preservado en run (retención hasta 2027-02-19).
- Primera fase sobre 67.200 evaluaciones sinápticas: 13.308 CHEM positivo, 9.850 CHEM y susceptibilidad positivos, **2.820 efectos reinforcement>0**, **94 cambios LTW**. Inversión 67.200: 13.500 CHEM+, 9.836 ambas+, **2.981 efectos>0**, **96 cambios LTW**; efecto máximo4. La química NO está cortada completamente, pero el refuerzo es pequeño e insuficiente para ventaja observada contra F.
- [CI general #44952785061](https://github.com/mxlzz/Nilo_public/actions/runs/44952785061) **success 410 tests, 2 expectedFailure históricos**, sin regresiones. La CI no contiene EXE/GEN propietarios.
- **I3a-OBSERVACIÓN validada; I3 aprendizaje continúa NEGATIVA y G05/G09 abiertas**. No elegir nueva dosis/tasa a partir del holdout 200..219. Diseñar I3b con hipótesis separadas (magnitud y distribución temporal de crédito), más tasas GEN históricas si están disponibles, y nuevas semillas confirmatorias. PR #103 draft; Nilo0.7/main intactos.

### 2026-11-21 — NL-LOG-0038 (I3b diseño, SIN ejecución)
- [Diseño comparativo I3b](E09_02I_I3B_DISENO_COMPARACION.md), commit fabb3c21a0e16065a30b2b0689aff419e581102e, posterior a diagnóstico I3a; **propuesta, no protocolo listo ni resultado**.
- Se distinguen hipótesis de amplitud química y crédito temporal a distractores. Se exige comparación equiparada de secuencias/dosis/ticks antes de ejecución, sin introducir verdad del evaluador en la red. Nuevas semillas independientes para un futuro ensayo confirmatorio, no reutilizar200..219.
- G-I3 sigue negativa; I3a observacional válida; G05/G09/G00-H abiertas. Continúan PR draft, main y motor Nilo intactos.


### 2026-11-21 — NL-LOG-0039 (I3b.1 amplitud y momento, diagnóstico pareado)
- [Preregistro](E09_02I_I3B1_RAMAS_QUIMICAS_PRE_REGISTRO.md) escrito antes del código. Primera [CI fallida #44956919841](https://github.com/mxlzz/Nilo_public/actions/runs/44956919841): test comparó etiqueta de acierto entre mappings invertidos, que necesariamente difiere aunque la rama neutra sea la misma. [Commit correctivo solo test](https://github.com/mxlzz/Nilo_public/commit/d40136ab8946eb39d9c56bda74e051dd1230c9ca). No cambios de modelo/umbral. [CI #44956959320 success](https://github.com/mxlzz/Nilo_public/actions/runs/44956959320), 7 tests específicos, artefacto ID14728625057.
- 20 semillas nuevas300..319, 240 episodios pareados 20×2×3×2. Ganancia artificial CHEM4 aumenta efecto candidato respecto a CHEM1 +7,575 (temprano) y +6,492 (tardío); adelantar aumenta proporción de efecto sobre conexiones de origen objetivo +0,17736 a ganancia1/+0,11202 a ganancia4 (intervalos por semilla en [informe](E09_02I_I3B1_RESULTADO_RAMAS.md)). Readout breve gain4 ≈65% vs control neutro50%, no aprendizaje acumulado.
- LTW ninguna porque la ventana termina t50–52 antes de primer tick128. No atribuir incapacidad de consolidar.

### 2026-11-21 — NL-LOG-0040 (I3b.2 ventana discreta de LTW)
- [Preregistro](E09_02I_I3B2_VENTANA_LTW_PRE_REGISTRO.md) anterior a código. Semillas nuevas400..419, 80 episodios, tronco común tick124, precursor temprano t125 vs tardío t128, mismo genoma reducido y químicos sintéticos. [CI #44957320048 success](https://github.com/mxlzz/Nilo_public/actions/runs/44957320048), artefacto ID14728127074. En t128 LTW E1 media+1,475, E4+3,925, L1/L4=0; no cambios en t127. [Resultado](E09_02I_I3B2_RESULTADO_VENTANA_LTW.md). LTW cae hasta t136 (E1 media0,050; E4 media3,375): requiere explicar pérdida sináptica, no proclamar memoria duradera.

### 2026-11-21 — NL-LOG-0041 (I3b.2a pérdida LTW atribuida a strength=0)
- [Preregistro observacional post hoc](E09_02I_I3B2A_FORTALEZA_PRE_REGISTRO.md) antes del auditor. [CI #44957588818 success](https://github.com/mxlzz/Nilo_public/actions/runs/44957588818), artefacto ID14728237546. Testigo por 8 dendritas cada tick en 80 episodios replica exactamente I3b.2.
- E1 LTW inicial118 t128:114 borradas por eventos lost_connection en t130 (98) y t135 (16), 4 restantes t136. E4:314 inicial,44 borradas t130 (14)/t135 (30), 270 conservadas. Reducciones extra-gate explicadas 100% por reset cuando fortaleza llega0. [Resultado](E09_02I_I3B2A_RESULTADO_FORTALEZA.md). Migración histórica posterior NO integrada; no equivalencia con Norn completo.

### 2026-11-21 — NL-LOG-0042 (I3b.3 disponibilidad de fuente migratoria)
- [Preregistro](E09_02I_I3B3_MIGRACION_VIABILIDAD_PRE_REGISTRO.md) anterior a tests. Reutilizó [c1_migration.py](../../experiments/neurolab/c1_migration.py) existente: dos fuentes Concept y dos contactos por clase Decision ocupan ambas; 8/8 rechazos duplicate_source; tercer origen libre solo en fixture sintético produjo 4/4 controles aceptados. [CI #44957812410 success](https://github.com/mxlzz/Nilo_public/actions/runs/44957812410), artefacto ID14728317633, [informe](E09_02I_I3B3_RESULTADO_MIGRACION.md).
- C1ContextBrain no guarda source_pointer dinámico y fija origen por índice: la migración no se integra solo llamando a función. [Alternativas I3c](E09_02I_I3C_ALTERNATIVAS_MINIMAS.md) proponen primero estudiar seis neuronas/cuatro contactos sin adicionar Concept, con controles.
- G-I3b.3-STRUCT cerrada SOLO en topología reducida. **I3 aprendizaje NEGATIVA; G00-H/G05/G09 abiertas; PR draft, main y Nilo0.7 sin cambios.**


### 2026-11-21 — NL-LOG-0043 (I3c.1 contrato, SIN desarrollo de arquitectura)
- [Contrato I3c.1](E09_02I_I3C1_CONTRATO_MIGRACION_DINAMICA.md): se especificaron identidades de fuente persistentes (C0/C1), 4 contactos tipados de la opción B, scheduler de reconexión aún sujeto a contraste histórico, RandStream/checkpoint y separación absoluta del evaluador.
- Comparación justa definida A(6/8 baseline), B(6/4 sin migración), B+(6/4 con migración Type1 existente) y D(6/8 reinicialización de misma fuente, ablación no histórica). **B+−B** aisla más directamente la contribución de migración, mientras A−B mide capacidad; B+−A no es comparación pura.
- Sin código nuevo de red; no se inventaron requisitos históricos del invocador de migración. **Siguiente I3c.2** revisar invocación Type1 y parámetros GEN o declarar convención N; recién entonces crear runtime y pruebas de checkpoint en branch experimental.
- G05/G09/G00-H siguen ABIERTAS, I3 continúa negativo. PR #103 borrador, main/Nilo0.7 intactos.


### 2026-11-21 — NL-LOG-0044 (I3c.2, invocación Type1/Type2 en EXE)
- [Preregistro I3c.2](E09_02I_I3C2_INVOCADOR_MIGRACION_PRE_REGISTRO.md) escrito antes del auditor. EXE original 387072 bytes, SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7; inspección estática en .text con 22 firmas x86 y dos llamadas directas confirmadas por lectura local. [Código auditor](../../experiments/neurolab/e09_i3c2_migration_callsite_audit.py), [informe](E09_02I_I3C2_RESULTADO_INVOCADOR_MIGRACION.md), [JSON](resultados/e09i3c2_invocador_migracion_original.json). La [CI general #44958386169](https://github.com/mxlzz/Nilo_public/actions/runs/44958386169) terminó SUCCESS: 435 tests ejecutados, 2 expectedFailure históricos; el test CI del auditor utiliza firmas sintéticas, no reabre EXE real.
- La actualización neuronal incluye WTA previo; tipo1 (0x40494c→0x404a80) solo para clase tipo1 y con output neuronal no-cero; tipo2 (0x4049c2→0x404b90) usa selección de destinatario y descarta índice -1, stride16. No es scheduler exhaustivo ni reconstrucción de PRNG/tiempo físico.
- **I3c.1/I3c.2 son acotados; la microred no se modificó y la migración no está integrada**. G05/G09/G00-H abiertas, PR draft y main/Nilo0.7 intactos. Siguiente I3c.3 preregistrar integrador dinámico con tests y checkpoint.


### 2026-11-21 — NL-LOG-0045 (I3c.3 adaptador nuevo, sin cambios Nilo)
- [Preregistro](E09_02I_I3C3_ADAPTADOR_DINAMICO_PRE_REGISTRO.md) antes del código, [módulo nuevo](../../experiments/neurolab/e09_i3c3_dynamic_context.py) aislado six units/four connections, source_pointer persistente, Type1 existente, RNG explícito, checkpoint/restore. [CI #44959655977](https://github.com/mxlzz/Nilo_public/actions/runs/44959655977) SUCCESS 9 tests; [CI general #44959661489](https://github.com/mxlzz/Nilo_public/actions/runs/44959661489) 444 tests, 2 expectedFailure, success. [Informe](E09_02I_I3C3_RESULTADO_ADAPTADOR.md). Scheduler/initial strength2/ltw0 convenciones N no históricas.

### 2026-11-21 — NL-LOG-0046 (I3c.3a, estimulación fija sin recompensa NEGATIVA)
- [Preregistro](E09_02I_I3C3A_TRAYECTORIA_PRE_REGISTRO.md), 20 nuevas semillas800..819×256 ticks, CHEM0/1 exógena alternada24, B vs B+ sin feedback. [Run #44959905616](https://github.com/mxlzz/Nilo_public/actions/runs/44959905616) success; [informe negativo](E09_02I_I3C3A_RESULTADO_TRAYECTORIA.md). **Cero conexiones agotadas, migración0, B=B+**, checkpoint128 replay exacto. No interpretar como inutilidad general de Type1.

### 2026-11-21 — NL-LOG-0047 (I3c.4, recableado activo sin aprendizaje)
- [Preregistro](E09_02I_I3C4_QUIMICA_APAREADA_PRE_REGISTRO.md) ANTES de código: semillas900..919, 2 fases60train/36holdout, 6 unidades/4 contactos, B sin migración y reward propio, Y migración con química apareada de B, P migración on-policy, F congelada con química B. Reacciones/receptores C1 de GEN con tasa40/dosis80 sintéticas. Química B/Y/F igual después de CADA tick.
- [Run inicial #44960312460](https://github.com/mxlzz/Nilo_public/actions/runs/44960312460) confundió ticks con alguna migración (2787 Y/P) con EVENTOS de conexiones aceptadas. Errata preservada; [commit b991dad4](https://github.com/mxlzz/Nilo_public/commit/b991dad4ee77bba0b8024acd3912d15a77f75c31) corrigió sólo contabilidad y se añadió test de dos migraciones mismo tick. [Run corregido #44960526007](https://github.com/mxlzz/Nilo_public/actions/runs/44960526007) SUCCESS 8 tests: **Y3377, P3379 eventos Type1**, 2787 ticks con alguna aceptación; B/F0. [Informe](E09_02I_I3C4_RESULTADO_QUIMICA_APAREADA.md).
- Accuracy holdout media primera B0.48472/Y0.48472/P0.48611/F0.49028, inversión B0.50417/Y0.50694/P0.50694/F0.50417. Y−B≈0 y+0.00278, CI incluye0. **G05 NEGATIVA/ABIERTA, G09 ABIERTA**; no extrapolar a Norn real ni confundir Y (recompensa ajena) con autonomía.

### 2026-11-21 — NL-LOG-0048 (I3c.4a, turnover con 20 SHA idénticos)
- [Preregistro post hoc](E09_02I_I3C4A_TURNOVER_PRE_REGISTRO.md), [hashes originales](resultados/e09i3c4_golden_seed_hashes.json) congelados ANTES de observador. Dos primeros runs del observador fallaron por nombres de fixture/workflow y falta de snapshot de F: [44960853419](https://github.com/mxlzz/Nilo_public/actions/runs/44960853419), [44960904099](https://github.com/mxlzz/Nilo_public/actions/runs/44960904099); se corrigió sólo el auditor. [CI final #44960961073](https://github.com/mxlzz/Nilo_public/actions/runs/44960961073) success, 4 tests, 20 SHA originales coincidentes, artefacto14728999464. [Informe I3c.4a](E09_02I_I3C4A_RESULTADO_TURNOVER.md).
- Y3377/P3379 migraciones, **0 conexiones con LTW positiva ANTES de cada migración**, STW previa positiva Y5/P4 eventos en total, y LTW al final de entrenamiento Y/P0. Mediana de intervalo por slot entre migraciones20 ticks, máximo45, frente gate128. No demuestra por sí sola causa única, ni cubre duraciones iniciales/finales.

### 2026-11-21 — NL-LOG-0049 (I3c.4b, testigo exacto de LTW128)
- [Preregistro observacional](E09_02I_I3C4B_GATE128_PRE_REGISTRO.md) antes del nuevo testigo, [CI #44961418723](https://github.com/mxlzz/Nilo_public/actions/runs/44961418723) SUCCESS 4 tests y20 hashes originales reproducidos; artefacto14729668186. [Resultado](E09_02I_I3C4B_RESULTADO_GATE128.md) y [resumen](resultados/e09i3c4b_resultado_resumen.json).
- Por fase: 60 gates×4 dendritas=240 evaluaciones. STW positiva/numeric LTW incrementos: B20/24, Y1/1, P1/2; NINGÚN borrado LTW en mismo tick gate. **12/20 B primera y12/24 B inversión** incrementos numéricos LTW partían de strength0: no equiparar con memoria de conexiones funcionales.
- [CI general #44961422627](https://github.com/mxlzz/Nilo_public/actions/runs/44961422627) **success 465 tests, 2 expectedFailure**. Resultado: disponibilidad de STW en momento de consolidación insuficiente en red migratoria; control B también fracasa conductualmente, luego no se puede culpar sólo a migración.
- [Siguiente plan I3c.5](E09_02I_I3C5_REENFOQUE_CREDITO_CAUSAL.md): volver a G05 causal-credit/retardo, verificar semántica de strength0 con x86 antes de modificar modelo, nuevas cohortes antes de pruebas confirmatorias. Nilo0.7/main intactos; PR#103 permanece draft.


### 2026-11-21 — NL-LOG-0050 (I3c.5a: retardo y crédito, nueva cohorte)
- Objetivo/subtarea: I3c.5a según [marco aprobado de investigación](E09_02I_I3C5_REENFOQUE_CREDITO_CAUSAL.md). Se creó [preregistro antes de código](E09_02I_I3C5A_CREDITO_DIFERIDO_PRE_REGISTRO.md), después runner/test/workflow independientes sobre cerebro de 8 conexiones ya existente (sin migración para aislar timing). Cero cambios a Nilo0.7, C1 original, tasa40/dosis80 sintéticas.
- [CI inicial #44963707697](https://github.com/mxlzz/Nilo_public/actions/runs/44963707697) success, [CI desglosada #44963833232](https://github.com/mxlzz/Nilo_public/actions/runs/44963833232) success **5/5 tests**, artefacto íntegro ID14730781039, 20 SHA por semilla. 20 seeds nuevas1200..1219, 80 troncos idénticos, 400 ramas N/D0..D3, 40 aciertos y40 fallos, ninguno sin acción.
- Hallazgos: fracción de refuerzo del origen objetivo D0=.56731, D1=.49146, D2=.43940, D3=.39946; D0−D3 +.16785, IC95% bootstrap por seed [.13609,.20074]. AUC medio CHEM0/CHEM1 por rama activa20.5 cada uno, pero NO misma exposición por tick. Readout todos .50, LTW diferencial tick256=0 y strength0 para8/8 contactos en dicha ventana.
- [Informe](E09_02I_I3C5A_RESULTADO_CREDITO_DIFERIDO.md). **Resultado: instrumentación y distribución temporal VALIDADAS; hipótesis de aprendizaje conductual/retención NO VALIDADA**. G05/G09/G00-H abiertas. Cohorte1200..1219 consumida y no confirmatoria para variantes posteriores.

### 2026-11-21 — NL-LOG-0051 (I3c.5b: fuerza0 en modelo N, C1 histórico bloqueado)
- Se elaboró [preregistro antes de tests](E09_02I_I3C5B_STRENGTH0_PRE_REGISTRO.md). [Observador aislado](../../experiments/neurolab/e09_i3c5b_strength0_audit.py) y [tests](../../experiments/neurolab/tests/test_e09_i3c5b_strength0_audit.py) sin modificar reglas. [CI #44963927561](https://github.com/mxlzz/Nilo_public/actions/runs/44963927561) **success 3/3**, artefacto14730781072.
- Fixture fuerza0/STW255 produce señal127 vs fuerza0/STW0 señal0, y score Decision207 vs80. Otro fixture de fuerza0 con CHEM0=255 produce STW+241 sin recuperar fuerza: una conexión agotada puede transmitir/plastificarse **en el modelo reducido N**.
- [Informe](E09_02I_I3C5B_RESULTADO_STRENGTH0.md). **I3c.5b-N VALIDADA; I3c.5b-H histórica ABIERTA/BLOQUEADA** por ausencia de EXE original en esta sesión; no extrapolar la semántica a C1 real. No cambiar código ni simular corrección, no fusionar PR. **Siguiente subtarea exacta**: reexaminar VA0x403F2F–0x403F8F y llamantes x86 de fuerza0 y borrado en el EXE SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`; después preregistro separado de intervención causal y test conductual en nuevas semillas.


### 2026-11-21 — NL-LOG-0052 (fuente binaria recuperada y local x86 validado)
- Tras archivo previo de la auditoría N, se localizaron en la carpeta Drive `neurolab` del usuario el mismo **Creatures.exe** SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7` y **dad1.gen** SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. Binarios originales no distribuidos.
- Auditoría estática GNU objdump + siete anclas SHA verificadas frente bytes originales: señal multiplica STW por salida de fuente sin guardia strength0; fuerza0 incrementa contador y cae en rama de susceptibilidad/plasticidad; fuerza al llegar a0 limpia STW/LTW/susceptibilidad; migración invocada tras WTA. [Informe](E09_02I_I3C5B_H_RESULTADO_X86.md), [evidencia JSON](resultados/e09i3c5b_h_strength0_x86_original.json), [script SHA-pin](../../experiments/neurolab/e09_i3c5b_exe_static_audit.py) y [CI tests sintéticos 44964349146](https://github.com/mxlzz/Nilo_public/actions/runs/44964349146) success.
- **I3c.5b-H-LOCAL VERIFIED_STATIC**; el bloqueo “EXE no disponible” del NL-LOG-0051 queda superado. **NO** implica ejecución dinámica ni cierre G00-H/G05/G09, que permanecen abiertos. Decisión: NO añadir gate fuerza0 inventada.

### 2026-11-21 — NL-LOG-0053 (relectura retrospectiva ZIP original I3c.5a)
- Descargado del workflow [44963833232](https://github.com/mxlzz/Nilo_public/actions/runs/44963833232) artefacto14730781039, 52.800 frames por tick: **las 400 ramas muestran strength0 en los ocho slots en tick125**, por lo que el estado común tick124 ya está agotado.
- Tras pulsos, hubo recuperación transitoria de alguna fuerza en algunos frames D0/D1/D3, **sin retención final**; ningún brazo mejora la precisión0.50. Se documentó en anexo [I3c.5a](E09_02I_I3C5A_RESULTADO_CREDITO_DIFERIDO.md). Contraste numérico de crédito temporal preservado como observación, no como aprendizaje. **No modificar diseño retrospectivamente**.

### 2026-11-21 — NL-LOG-0054 (I3c.5c read-only: causa temporal del agotamiento)
- [Preregistro antes del instrumento](E09_02I_I3C5C_DISPONIBILIDAD_TRONCO_PRE_REGISTRO.md), [40 SHA checkpoint](resultados/e09i3c5c_original_trunk_hashes.json) fijados desde artefacto I3c.5a, [CI #44964605558](https://github.com/mxlzz/Nilo_public/actions/runs/44964605558) **success 4 tests**, 40 replays/125 ticks con 40/40 SHA exactos, artefacto14731510008.
- Las ocho conexiones se agotan **exactamente en tick10 en todos los 40 troncos** y no recuperan fuerza sin recompensa hasta tick124. Explica por qué el refuerzo I3c.5a llega a una red sin conexiones de fortaleza positiva; tasas de pérdida genéticas Decision5 e inicio fuerza2, pero no extrapolar a Norn entero.
- [Informe](E09_02I_I3C5C_RESULTADO_DISPONIBILIDAD.md). **G-I3c5c-REPLAY/DIAG VALIDAS**, no G05. **Siguiente nodo**: preregistrar experimento independiente que mida aprendizaje con fuerza disponible y controles apareados o con migración real pertinente, sin ajustar múltiples factores ni reutilizar semillas para conclusión.


### 2026-11-21 — NL-LOG-0055 (I3c.5d anticipación de recompensa, aprendizaje NEGATIVO)
- [Preregistro](E09_02I_I3C5D_REFUERZO_PRECOZ_PRE_REGISTRO.md), [CI 44965370419](https://github.com/mxlzz/Nilo_public/actions/runs/44965370419) SUCCESS seis tests, artefacto14730837789, [informe](E09_02I_I3C5D_RESULTADO_VENTANA_PRECOZ.md).
- 20 seeds nuevas1300..1319, 80 coordenadas/240 brazos N/D0/D3. CHEM llega mientras fuerza positiva80/80 D0 y D3. Efectos unitarios D0 en16/80, D3 en48/80, pero **readout 0.50 y 0/80 elecciones cambiadas** frente control en ticks9,16,128. LTW retenida0. Puertas software/availability sí, **G05 NEGATIVA**.
- Causalidad/fuente y dosis sintética no equiparan rendimiento; no subir ganancia.

### 2026-11-21 — NL-LOG-0056 (I3c.5e umbral STW y borrado, CI inicial fallida preservada)
- [Preregistro](E09_02I_I3C5E_PUERTA_SENAL_PRE_REGISTRO.md), [CI inicial44965690554](https://github.com/mxlzz/Nilo_public/actions/runs/44965690554) FAILED por SHA seed1309 transcripto con59 caracteres; fixture corregido solo desde artefacto original commit bbdd3c17; [CI final44965764264](https://github.com/mxlzz/Nilo_public/actions/runs/44965764264) SUCCESS seis tests, artefacto14731856013.
- [Informe](E09_02I_I3C5E_RESULTADO_PUERTA_SENAL.md): output Concept126 y peso STW mínimo5 para señal Decision positiva; reward effect1 en D0 tick7 relax0 inmediato, fuerza pérdida D3 tick10 reset; testigos matemáticos, NO prueba Norn completo. G05 ABIERTA.

### 2026-11-21 — NL-LOG-0057 (I3c.5f auditoría GEN y línea base)
- [Informe GEN](E09_02I_I3C5F_AUDITORIA_BASAL_GEN_C1.md) coteja Decision4096 dendritas nominales, 128 por clase, strength2..4, CHEM2/3 nominal16, frente baseline8 con todas strength2, Concept sintético one-hot.
- Sin código nuevo, sin conclusión conductual: la escala y la realimentación no son equivalentes; no saltar a cerebro de952 neuronas por defecto.

### 2026-11-21 — NL-LOG-0058 (I3c.6a señal de agotamiento histórica)
- [Preregistro](E09_02I_I3C6A_REALIMENTACION_ATROFIA_PRE_REGISTRO.md), EXE auténtico SHA verificado localmente; **10 anclas x86 originales** [JSON](resultados/e09i3c6a_original_feedback_writer.json), [CI sintética44966344851](https://github.com/mxlzz/Nilo_public/actions/runs/44966344851) SUCCESS cuatro tests, [informe](E09_02I_I3C6A_RESULTADO_REALIMENTACION_ATROFIA.md).
- Type1 class-lobe writer usa MIN de recuentos de dendritas agotadas por neuron/clase procesada, Type2 incrementa1 por registro con alguna desconectada. GEN emisores124/125 químicos53/70, receptores127/128 nominal16 de CHEM2/3. Los brazos metabólicos N omiten los emisores y puertos. Verificación estática LOCAL, sin scheduler completo. G05/G09/G00-H abiertas.

### 2026-11-21 — NL-LOG-0059 (I3c.6b umbral químico, topología insuficiente)
- [Preregistro](E09_02I_I3C6B_UMBRAL_QUIMICO_PRE_REGISTRO.md), [CI44966495426](https://github.com/mxlzz/Nilo_public/actions/runs/44966495426) SUCCESS 4 tests, artefacto14731344539, [informe](E09_02I_I3C6B_RESULTADO_UMBRAL_QUIMICO.md).
- Mismo Emitter+Receptor originales: locus0/1 sin emisión efectiva, locus2 emite químico1 pero receptor sigue CHEM16, locus3 emite2→CHEM15. Microred fija2/dinámica1 enlaces por clase: aunque se agoten todos, **feedback aislado incapaz de cambiar CHEM**. Resultado de escala N, no del original128 por clase. No implementar emisores inútiles.

### 2026-11-21 — NL-LOG-0060 (I3c.6c preregistrada, ejecución en curso)
- [Preregistro](E09_02I_I3C6C_UMBRAL_ATROFIA_PRE_REGISTRO.md) antes del código; [runner](../../experiments/neurolab/e09_i3c6c_functional_loss_threshold.py), tests específicos y workflow independientes. Busca umbral REAL de fuerza inhibida (CHEM2/3=0) vs mero cambio del receptor, preservando original `update_c1_synapse` y los dos genes.
- Al escribir este estado **CI #44966668042 EN COLA**, no etiquetar validación científica ni mover puerta. Si sale bien actualizar marcador, informe y siguiente plan. G05/G09/G00-H abiertas, PR draft, main/Nilo0.7 sin cambios.


### 2026-11-21 — NL-LOG-0061 (I3c.6c resultado y distinción umbral receptor vs pérdida)
- [CI 44966668042](https://github.com/mxlzz/Nilo_public/actions/runs/44966668042) SUCCESS cuatro tests y artefacto14731529325, curva completo locus0..32 ambas parejas emisor/receptor/sinapsis del GEN; [informe](E09_02I_I3C6C_RESULTADO_UMBRAL_ATROFIA.md).
- CHEM2/3 baja de16 a15 en locus3, pero `lose_strength_rule_output=15>0` sigue reduciendo fuerza4→3 al tick5. Locus17 CHEM1 aún reduce; primer locus que da CHEM0 y evita pérdida es **18** en ambas clases. Fuente Type1 MIN obliga **capacidad ≥18 por clase/neuron** sólo como requisito posible, NO garantía de activación o aprendizaje. Red N 2/1 incapaz, G05/G09/G00-H ABIERTAS.
- Corrección de interpretación I3c.6b: cambio receptor≠autorregulación eficaz. No implementar 3 contactos ni aumentar ganancia a ciegas.

### 2026-11-21 — NL-LOG-0062 (I3c.7 alternativas evaluadas, SIN implementación)
- [Análisis de decisión](E09_02I_I3C7_OPCIONES_AUTORREGULACION.md) evalúa A restaurar ≥18 contactos por clase con fuentes originales no duplicadas (mínimo72 slots para dos decisiones más fuente conceptual amplia), B adaptar explícitamente señal N con controles, C aislar aprendizaje G05 usando baselines ya escritos sin nuevo motor. Incluye observación exploratoria sobre genes GEN de químicos53/70: sólo emisores124/125 y receptores127/128, ninguna de las58 reacciones genéticas utiliza esos químicos; no atribuir ausencia de otras fuentes del motor.
- Para investigación inmediata se prioriza **diseñar** el contraste con controles existentes (C) por menor complejidad antes de elegir nueva arquitectura. **No implica aprobación de adaptación N o escalado de lóbulos**, ni ejecución de nueva cohorte; `main` y Nilo0.7 permanecen intactos.


### 2026-11-21 — NL-LOG-0063 (I3c.7a comparabilidad y reutilización, SOLO DISEÑO)
- [Auditoría de código existente](E09_02I_I3C7A_REUSO_CONTROLES_Y_CONTRASTE.md): E03 (plasticidad propia), E09g.5 (C1 seis unidades, refuerzo directo y frozen/blind), E09g.10b (C/IG/F/Q y distractores), I3b.1 (clones N/E/L) e I3c.4 (química B/Y/F idéntica). No se creó motor ni entrenamiento, se recuperaron los contratos reales.
- Distinción crítica: Q tiene token explícito (contexto,acción) **privilegiado**; los efectos directos255 y metabolismo precursor80 tienen amplitudes no apareadas; yoking químico no prueba decisiones on-policy; un pulso no prueba LTW. Propuesta de fase mecanística de clon vs fase conductual independiente con controles, sin ajuste posterior de dosis.
- **I3c.7a documentación/controles AUDITADOS; G05/G09/G00-H abiertas**. Próxima unidad **I3c.7b preregistro antes de código**, semillas1400..1419 no consumidas, ninguna arquitectura aprobada. Estado en branch PR#103 draft, no merge.


### 2026-11-21 — NL-LOG-0064 (I3c.7b respuesta directa transitoria)
- [Preregistro](E09_02I_I3C7B_CONTRASTE_SENAL_PRE_REGISTRO.md) previo a código, [CI44968344691](https://github.com/mxlzz/Nilo_public/actions/runs/44968344691) success6 tests, artefacto14733055528 y [reporte](E09_02I_I3C7B_RESULTADO_CONTRASTE_SENAL.md). Seeds1500..1519, 80 acciones del tronco×4 brazos=320. Directo255 supera umbral STW5 en60/80, tipo/score en36/80 y cambia 22 acciones con net +18 aciertos: accuracy0.725 vs0.5 (IC seed-cluster +0.10,+0.35) a t7/9; t16/128 cero retención. M químico precursor80 no cambia decisiones; amplitudes no igualadas ni crédito puro (472/1196 efecto directo en fuente distractor). G05 abierta.

### 2026-11-21 — NL-LOG-0065 (I3c.7c extinción replay exacto)
- [Preregistro posterior a inspección](E09_02I_I3C7C_EXTINCION_PRE_REGISTRO.md), [CI44968676147](https://github.com/mxlzz/Nilo_public/actions/runs/44968676147) success6 tests, artefacto14732582942. 20 semillas reejecutadas, JSON 12.128.800 bytes **SHA original exacta** 2660ba63b866abfff469d754ff88cab8941b215b1078a652ddc52dfca0cce8a6; no nuevo holdout. C STW funcional t7–9, all8 fuerza0 t10 en C/M/N, señal pos-tick0 y no scores desde11; 20 mejoras2 perjuicios, no LTW. [Informe](E09_02I_I3C7C_RESULTADO_EXTINCION_REPLAY.md).

### 2026-11-21 — NL-LOG-0066 (I3c.7d confusor de atrofia directo vs metabólico)
- [Preregistro](E09_02I_I3C7D_COMPARABILIDAD_ATROFIA_PRE_REGISTRO.md), [CI44968836884](https://github.com/mxlzz/Nilo_public/actions/runs/44968836884) success4 tests, artefacto14732757592; [informe](E09_02I_I3C7D_RESULTADO_COMPARABILIDAD_ATROFIA.md).
- E09g5 DIRECT input CHEM2/3=0 desactiva loss original; I3 metabolito usa receptor nominal16 sin emisores, pierde fuerza tick5/tick10. Holdout `learn=False` congela también atrofia. Por tanto benchmark E09g5 no es comparación equivalente de química vs directo. No tocar reglas originales.

### 2026-11-21 — NL-LOG-0067 (I3c.7e preregistro factorial, ensayo en ejecución)
- [Preregistro](E09_02I_I3C7E_FACTORIAL_PERDIDA_REFUERZO_PRE_REGISTRO.md) ANTES del código. Nueva cohorte desarrollo1600..1619; 4 brazos plásticos D0,D16,M0,M16 y congelados FD/FM, estímulos EXACTOS E09g5 32×8 train y16×8 holdout por fase original/invertida; dos clones readout frozen vs active no nuevo feedback; ablation CHEM2/3 zero explícita en D0/M0 (NO histórica), dosis previas255/80.
- [Runner](../../experiments/neurolab/e09_i3c7e_loss_factorial.py), tests y workflow independientes, [CI44969153930](https://github.com/mxlzz/Nilo_public/actions/runs/44969153930) EN PROGRESO: validación pequeña de paridad D0 con `train_brain/evaluate_brain` de E09g5 aprobada, full20 semillas todavía pendiente al registrar. **G05/G09/G00-H abiertas**, no declarar resultados hasta leer artefacto. Main/Nilo0.7 intactos y PR103 draft.


### 2026-11-21 — NL-LOG-0068 (I3c.7e factorial preregistrado, RESULTADO CI)
- [Preregistro](E09_02I_I3C7E_FACTORIAL_PERDIDA_REFUERZO_PRE_REGISTRO.md) antes de código, [CI44969153930](https://github.com/mxlzz/Nilo_public/actions/runs/44969153930) SUCCESS7 tests, artefacto14733290218, JSON original39.359.911bytes SHA `193ef109e214d33b9779611f1757d3bf23781755d38a0212778ed4269748752c`; 20 seeds1600..1619×6 brazos D0/D16/M0/M16/FD/FM×2 fases A/B×2 readouts clones. [Informe](E09_02I_I3C7E_RESULTADO_FACTORIAL_ATROFIA.md).
- Fase B invertida ACTIVE steady D0.9417,D16.9406,M0.8177,M16.6500 vs FROZEN D0.9760,D16.9776,M0.9521,M16.9276. M0−M16 ACTIVE +.1677 IC95 seed-cluster [.1391,.1990]. M16 19/20 termina sin enlaces; M0 20/20 conserva8 pero pierde señal STW gradualmente. **G05 NEGATIVA bajo criterio 18/20 robustos: M16 0/20, M0 1/20.** D0 reprodujo E09g5 exactamente por estado y readout, no sólo promedio. Intensidad/timing direct255 vs químico80 NO equiparados.

### 2026-11-21 — NL-LOG-0069 (I3c.7e IC seed-cluster completo SIN modificar datos)
- Primera CI contenía sólo media frozen−active por brazo, no IC95 preregistrado. Corrección **exclusiva del análisis** en `_frozen_minus_active_ci`; [CI44969437429](https://github.com/mxlzz/Nilo_public/actions/runs/44969437429) SUCCESS7 tests, artefacto14732389870. SHA canónica `per_seed` de las20 trazas **idéntica** `311b387817b4f0d645cf191df99ae701641c11e9329758fe64f1f71701af8f8e`. M16 reversed frozen−active +.2776 IC95 [.2047,.3417], M0 +.1344 [.0901,.1802]. No se reclasificó resultado científico.

### 2026-11-21 — NL-LOG-0070 (I3c.7f auditoría post hoc y erratas de infraestructura)
- [Preregistro POSTHOC](E09_02I_I3C7F_PERSISTENCIA_PESOS_PRE_REGISTRO.md), [reporte provisional](E09_02I_I3C7F_RESULTADO_PERSISTENCIA.md), [runner read-only](../../experiments/neurolab/e09_i3c7f_weight_persistence_audit.py) con20 semillas originales sin cohortes nuevas. Matriz real **61.440 frames** = 20×2 fases×6 modos×2 readouts×128 ticks; primeros intentos [44969795285](https://github.com/mxlzz/Nilo_public/actions/runs/44969795285), [44969817536](https://github.com/mxlzz/Nilo_public/actions/runs/44969817536), [44969969795](https://github.com/mxlzz/Nilo_public/actions/runs/44969969795), [44970018562](https://github.com/mxlzz/Nilo_public/actions/runs/44970018562) FAILED por errores del propio auditor CLI/escape y aserción de volumen erronea30.720, **nunca por deriva neuronal**; replay original siempre SHA exacta donde ejecutó. [CI corregida44970236994](https://github.com/mxlzz/Nilo_public/actions/runs/44970236994) aún EN EJECUCIÓN al registrar; NO marcar G-I3c7f validada hasta SUCCESS.
- Observaciones posthoc de original: M0 active invertida mantiene8/8 strength pero STW≥5 promedio cae3.54→.61 entre primer/último cuarto; M16 strength promedio4.12→.17, 19/20 sin enlaces al terminar. Cota matemática rate128+LTW inicial0: solo4 oportunidades hasta tick512 (máxLTW4), siguiente tick640 tras última decisión de holdout; **LTW sola no puede sostener un tipo positivo en la ventana actual Concept126/umbral STW5**. No inferir eficacia histórica C1 ni causalidad del mismo tick. G05/G09/G00-H abiertas.


### 2026-11-21 — NL-LOG-0071 (I3c7f cierre final, reejecución hash exacta)
- [CI44970236994](https://github.com/mxlzz/Nilo_public/actions/runs/44970236994) **SUCCESS 5 tests**, artifact14733312090, 20 semillas I3c7e1600..1619 **mismas** SHA per_seed `311b387817b4f0d645cf191df99ae701641c11e9329758fe64f1f71701af8f8e`, **61.440 frames** completos auditados con contextos, STW/LTW/fuerza y ausencia de recompensas nuevas. [Informe con erratas](E09_02I_I3C7F_RESULTADO_PERSISTENCIA.md).
- M0 reversed ACTIVE conserva 8 links en20/20 pero promedio links con STW≥5 3.54→.61 por cuatro ventanas32 ticks; precisión global .836→.572, LTW viva media~2.49. M16 reversed ACTIVE fuerza viva4.12→.17 y19/20 terminan sin enlaces; precisión .642→.494. Se reportan por contexto los desequilibrios de cada ventana; correlación de peso no prueba causación por sí sola.
- Cota deductiva original `ltw_rate128`, inicial0: antes de holdout invertido tick512, LTW≤4 y último update tick640 ocurre después de última elección; bajo Concept126 se requiere STW≥5 para una contribución positiva. Congelar STW en readout mantiene respuesta pero no demuestra retención temporal. G05/G09/G00-H ABIERTAS.
- Intentos previos de auditor FALLARON por CLI sin main, escapes literales y assert CI de volumen30720 en vez de61440. Se preservaron, se corrigió sólo código de auditor/tests, nunca se alteraron datos de I3c7e. No nuevas semillas ni modificación del cerebro. Próximo I3c7g diseñado desde cota, sin tuning.


### 2026-11-21 — NL-LOG-0072 (I3c7g 20 nuevas seeds, horizonte LTW suficiente pero sin mejora)
- [Preregistro](E09_02I_I3C7G_HORIZONTE_CONSOLIDACION_PRE_REGISTRO.md) ANTES DE código, [CI44970705424](https://github.com/mxlzz/Nilo_public/actions/runs/44970705424) SUCCESS6 tests, artefacto14733194016. Archivo original49.164.278bytes SHA256 `128e92df48b749c046fb9e1b02fce3beb54f4c8b82ed814b067a7c8d0c215d78`, per_seed SHA `9343414af0f29260a0080dd950fbf3dab493633e2550669b999ec1f88e9783fb`. [Reporte](E09_02I_I3C7G_RESULTADO_HORIZONTE.md). Seeds1700..1719 nuevas (ya desarrollo consumido). SHORT32×8 invertido prefijo IDÉNTICO de LONG80×8, mismas fuentes de recompensa/código/genética. D0 SHORT exacto E09g5.
- M0 LONG tiene LTW≥5 en75 enlaces de20/20 semillas, contra0 SHORT, pero ACTIVE inverted accuracy .8599 SHORT→.8370 LONG, Δ−.0229 IC95[-.0828,+.0297]. M16 LONG LTW≥5 en35 enlaces18/20 seeds, ACTIVE .6490→.6729 Δ+.0240 IC95[-.0307,+.0792]. D0 LONG peor Δ−.0646; control sin plasticidad FM LONG mueve accuracy +.0469 por estado/tiempo, demuestra que más duración no aísla efecto de LTW. G05 robustez ambos ACTIVE: M0 3/20 SHORT y LONG, M16 0/20; ningún≥18/20.
- **Conclusión científica negativa**: horizonte era una condición limitante para LTW≥5 pero habilitarla no basta para robustez conductual; no seguir ampliando duración por ajuste.

### 2026-11-21 — NL-LOG-0073 (I3c7h alternativa causal, NO implementación)
- [Evaluación de reutilización](E09_02I_I3C7H_DECISION_CONTINGENCIA_CAUSAL.md): ya existe yoking química B/Y/F `e09_i3c4_yoked_metabolic.py` y controladores `run_phase` de I3c7e; reutilizar testigo de identidad de química, **no** portar migración/topología Type1 de I3c4. Objetivo próximo contrastar feedback químico ligado a decisión propia versus misma química de otro brazo no contingente, manteniendo contexto y fuerza con control F congelado; registrar divergencia B/Y, verdadero crédito de fuente no dado a neuron y política on-policy distinta. No usar seeds1400..1419 confirmatorias ni alterar parámetros para ganar; **I3c7h sólo evaluado como diseño, no preregistrado/ejecutado**. G05/G09/G00-H ABIERTAS.


### 2026-11-22 — NL-LOG-0074 (I3c7h invalidez de yoking idéntico, corrección ANTES de datos)
- [Fe de erratas en diseño](E09_02I_I3C7H_DECISION_CONTINGENCIA_CAUSAL.md): en circuito C1 determinista con idéntico estado inicial/inputs/química por tick, B e Y necesariamente realizan transiciones idénticas; por tanto B−Y no era prueba causal, ni siquiera si Y recibe tape offline. **No gastar semillas en contraste incapaz de divergir**.
- [Preregistro corregido](E09_02I_I3C7H_CONTINGENCIA_PERMUTADA_PRE_REGISTRO.md) antes de programar. Desarrollo semillas1800..1819, 4 brazos B propio, Y replay exacto control de software, P con permutación de signos por contexto mediante RNG fijo (igual número/posición de eventos y signos por contexto, distinta cinética), F sin plasticidad con cinta B. Criterio de manipulación≥16/20 seeds con≥10% permutación y B−P ACTIVE invertida como resultado exploratorio. **No se atribuye un peso sináptico individual a causalidad**, ni químicos idénticos para P. Sin cambios genoma/topología/gain/metabolismo, 1400..1419 intactos.
- [Runner](../../experiments/neurolab/e09_i3c7h_contingency_permutation.py), tests y workflow [CI44986258314](https://github.com/mxlzz/Nilo_public/actions/runs/44986258314) lanzados. Al guardar esta nota pasaron pruebas específicas iniciales y corría cohorte completa; **RESULTADOS aún pendientes**. G05/G09/G00-H ABIERTAS.


### 2026-11-22 — NL-LOG-0075 (I3c7h RESULTADO positivo de contingencia, no G05)
- [Fe de erratas pre-datos](E09_02I_I3C7H_DECISION_CONTINGENCIA_CAUSAL.md), [prereg antes código](E09_02I_I3C7H_CONTINGENCIA_PERMUTADA_PRE_REGISTRO.md), [CI44986258314](https://github.com/mxlzz/Nilo_public/actions/runs/44986258314) SUCCESS7, artifact14739997041, full JSON39.394.817bytes SHA `d723c4a590c0428e13b175c39cd9028c69ed5b714d000f46ada61717eebe925e`, per_seed SHA20 `dfb26799e560d072234224fd3075980fdd7a0104b3fc1486200731e556a10d41`, [manifest por seed](resultados/e09i3c7h_resumen_y_hashes.json), [informe](E09_02I_I3C7H_RESULTADO_CONTINGENCIA.md).
- 20 semillas1800..1819, B propio e Y tape exacto **identidad total** en cada tick (invalida un B−Y como prueba causal). P signs shuffle por contexto conservando dosis, ticks y recuento de valencias pero cinética DIFERENTE; F sin plasticidad. 20/20 seeds permutación efectiva (37.89% signos tras reversión), P valencia coincide con su propio resultado47.8%, B100%; B/P difieren en media127.45 acciones/256 en inversión. ACTIVE fase B B=.878125 P=.491667 F=.492708; B−P+.386458 IC95[+.296354,+.482292], señal de interés precomprometida POSITIVA pero P química no igual al original. B G05 robustez ambas fases 2/20 vs meta18/20; puertas G05/G09/G00-H abiertas.

### 2026-11-22 — NL-LOG-0076 (I3c7i auditoría causal de señal local, posthoc prereg)
- [Preregistro antes de microlesiones](E09_02I_I3C7I_ABLACION_LOCAL_PRE_REGISTRO.md): usar solo datos del mismo desarrollo1800..1819, reejecutar hash por seed I3c7h y reconstruir states B/P t256/512 exactos. Por estado/contexto,8 slots STW0 one-at-time, sham intacto y ALL_ZERO bajo microprobe8 ticks freeze/no química, 800 bloques (640 lesiones) con controles y script read-only. Semillas1400..1419 sin consumir, genoma/neurona/sensores intactos. Es una prueba de necesidad local en un estado, NO origen causal del refuerzo ni G05. [CI44986729926](https://github.com/mxlzz/Nilo_public/actions/runs/44986729926) en ejecución; resultados pendientes, no reclamar anticipadamente.


### 2026-11-22 — NL-LOG-0077 (I3c7i RESULTADO posthoc de necesidad local)
- [Preregistro anterior a microintervenciones](E09_02I_I3C7I_ABLACION_LOCAL_PRE_REGISTRO.md), [CI FINAL44987034290](https://github.com/mxlzz/Nilo_public/actions/runs/44987034290) SUCCESS7, artifact14739729195, fuente completa JSON1.041.852bytes SHA `e6a30b3c2271a87b7404e4c0a9544f41c5ba0d265f946c8ece188fcc93952b5d`, per_seed SHA20 `bed54546d4dbfba0f9fb55e5db6bbbc9b537708ae48f37f52bbb3ba8a76502e5` EXACTA primera simulación. [Reporte](E09_02I_I3C7I_RESULTADO_ABLACION_LOCAL.md), [manifest](resultados/e09i3c7i_proveniencia.json).
- Misma cohorte1800..1819 del I3c7h, sin nuevos datos de entrenamiento. Checkpoints B/P t256/512 SHA originales verificados. **1600 microbloques** (1280 lesiones STW0,160 sham,160 allzero),8 ticks sin learn/química. B inversión baseline congelado local.9667 vs P.5; allzero altera acción20/20 semillas B, P16/20. Local effect de slot alineado B net0.40 vs P0.26875; para noalineado B−0.00694 vs P−0.09722 (eliminar slots P puede mejorar). B−P net perdido entre todas lesiones +0.10052 IC95[+.06615,+.13229], no nueva mejora G05.
- CI primero falló por error de expectativa singleton40 vs80; siguiente por recuento completo800 vs1600, luego CI44986928497 PASS; post-lectura se agregaron agregados con IC por alignment a mismo raw `per_seed` SHA exacta, CI44987034290 PASS. Erratas explícitas en prereg/reporte, sin modificar cerebro, respuestas ni muestreo.
- **Qué NO demuestra:** ablación revela necesidad local en estado y tarea, no si el histórico refuerzo asignó crédito correcto ni retención ACTIVE. G05/G09/G00-H ABIERTAS, B del estudio original sólo2/20 cumplen ambas fases ACTIVE≥.90.

### 2026-11-22 — NL-LOG-0078 (decisión siguiente: NO otra optimización por inercia)
- I3c7e/f/g identifican pérdida de fuerza nominal y relajación STW; extender horizonte LTW cruza umbral sin robustez. I3c7h/i verifican efecto de contingencia y de señales sinápticas funcionales. **El obstáculo actual es memoria persistente bajo dinámica activa**, no ausencia total de aprendizaje. Próxima unidad I3c7j = *evaluar alternativas y meta de memoria* antes de más experimentos; 1400..1419 reservadas, PR103 draft, main/Nilo0.7 intactos.


### 2026-11-22 — NL-LOG-0079 (I3c7j análisis estratégico y LTW-only posthoc)
- [Estrategia y diagnóstico](E09_02I_I3C7J_MEMORIA_DIAGNOSTICO_ESTRATEGIA.md) sobre artefacto I3c7g original (20 seeds1700..1719, SHA fuente `128e92df48b749c046fb9e1b02fce3beb54f4c8b82ed814b067a7c8d0c215d78`), sin ejecutar nuevos cerebros. Contrafactual **MATEMÁTICO** de qué margen tendría cada owner si STW ya hubiera convergido a LTW, NO readout con neuronas/tiempo reales: M0 LONG75/160 LTW≥5 (42 aligned/33 no), 0/20 semillas con margen positivo en ambos contextos; D0 LONG160/160 pero margen0 en ambos20/20 por igualdad de señal; M0 LONG STW real tiene margen positivo ambos contextos18/20. Hipótesis de contenido diferencial de LTW, posthoc, no confirmatoria. Alternativas H reconstrucción histórica costosa, N capacidad mínima explícita, C evaluación ecológica secundaria y D congelar; recomendar una sola prueba de suficiencia antes de código nuevo.

### 2026-11-22 — NL-LOG-0080 (I3c7k capacidad oráculo INSUFICIENTE)
- [Preregistro posterior a observar fuente](E09_02I_I3C7K_TRANSFERENCIA_CONTENIDO_PRE_REGISTRO.md), [CI44987744410](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) **SUCCESS5 tests**, artifact14740013286; original I3c7g seeds1700..1719 SHA por seed exacta y frames640/checkpoints. Lectura 128 ticks ACTIVE original S=.836979, transferencia artificial instantánea LTW<-STW C=.885938, LTW owner-swapped misma magnitud X=.631250; frozen original/S/C/X=.927083 con acciones idénticas, demuestra efecto via dinámica y no input directo. C−S+.048958 IC95[+.008333,+.089063] **< pre-gate .10**, C−X+.254688. [Informe](E09_02I_I3C7K_RESULTADO_TRANSFERENCIA.md), [proveniencia](resultados/e09i3c7k_resultado_proveniencia.json), JSON82959bytes SHA `d67d77d09844ab6699d3e2d56434f21b91d56fb79fb05c882cdd5ea9f4b4fccf`; per_seed SHA `b87545a66e2811c20707f57c40417e092e19156058b26297aefd34846fa3fe5c`. G-I3c7k software validada; **puerta científica de suficiencia falla**, G05/G09/G00-H abiertas. No tuning ni nuevas semillas.

### 2026-11-22 — NL-LOG-0081 (DECISIÓN STOP/PIVOT, no se modifica motor)
- Con I3c7e–k se ha identificado capacidad de asociación y efecto causal local, pero fracasa la durabilidad bajo reglas activas. Incluso oráculo ideal limitado. **Se congela desarrollo incremental del mini C1 8 slots** y queda como referencia negativa, sin archivarlo/eliminarlo. Próxima I3c7l delimitar continuidad científica para metas H histórica y N mínima; elegir sólo alternativa con evidencia, costo acotado y beneficio pre-registrado. Seeds1400..1419 reservadas intactas. PR103 draft, main y Nilo0.7 sin cambios.


### 2026-11-22 — NL-LOG-0082 (I3c7l STOP/PIVOT estratégico formal)
- [Documento de decisión I3c7l](E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md): se revisaron pruebas I3c7e–k y alternativas externas sobre estabilidad/plasticidad, elegibilidad de tres factores y consolidación de pesos; no hay evidencia suficiente para invertir en otra corrección del mini C1 de8 slots. El oráculo I3c7k ya transfería contenido STW a LTW desde el propio checkpoint y falló puerta de suficiencia predefinida (+.04896 < +.10); usarlo como filtro de costos, no como invitación a buscar dosis.
- **Decisión aplicada: STOP** de tuning de tasa/horas/genética/tamaño/recompensa sobre este circuito. Conservar como baseline negativo con CI y reproducibilidad, no descartar trabajo ni fusionar con Nilo0.7.
- **Separación obligatoria** H fidelidad histórica del original C1 (receptor/emisor/scheduler/topología), N mente mínima con memoria autónoma (requiere propuesta local nueva explícita y evidencia de suficiencia); ninguna arquitectura nueva aprobada. Próximo I3c.8 investigación de mecanismos existentes/alternativas, NO implementación ni nuevas semillas hasta superar gate de justificación. Mantener seeds1400..1419 sin usar, G05/G09/G00-H ABIERTAS.


### 2026-11-22 — NL-LOG-0083 (I3c8 revisión de lo existente y límite de inversión)
- [Informe selectivo I3c8](E09_02I_I3C8_ALTERNATIVAS_EXISTENTES_MEMORIA.md) con antecedentes verificados: Gerstner/Frémaux tres factores/eligibilidad (crédito temporal, no retención por sí sola), Benna–Fusi multiescala (estabilidad, más variables/contacto), EWC/Synaptic Intelligence (gradientes/importancia, gran desvío para8 dendritas), Brian2 simulador STDP Python con licencia CeCILL2.1/compatibilidad Python>=3.12 y Nengo PES/BCM/Oja/Voja licencia GPLv2. Se comprobaron documentos primarios y fuentes oficiales de capacidades/licencias, NO se instaló software ni verificó rendimiento/plug-in original C1.
- **Resultado de investigación:** no se identificó una solución externa demostrada que sustituya de inmediato cerebro y memoria C1 mini bajo G05; ausencia de solución verificada no equivale a inexistencia. **NO IMPLEMENTAR** por ahora un nuevo stack, eligibilidad o slow/fast synapses sin antes demostrar suficiencia con hipótesis predefinida y control de costo. Se mantiene STOP del miniC1 como benchmark. G05/G09/G00-H abiertas, 1400..1419 reservadas, PR103 draft/main intactos.
