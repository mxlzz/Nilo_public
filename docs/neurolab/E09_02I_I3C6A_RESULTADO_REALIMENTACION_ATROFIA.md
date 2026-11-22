# E09.02i–I3c.6a — circuito original de realimentación de la atrofia

**21/11/2026. Resultado de auditoría ESTÁTICA original, NO ejecución C1 ni integración al motor.** [Preregistro antes del auditor](E09_02I_I3C6A_REALIMENTACION_ATROFIA_PRE_REGISTRO.md), [auditor SHA y bloques](../../experiments/neurolab/e09_i3c6a_atrophy_feedback_audit.py), [10 anclas/hashes de EXE auténtico](resultados/e09i3c6a_original_feedback_writer.json), [CI con PE sintético #44966344851](https://github.com/mxlzz/Nilo_public/actions/runs/44966344851) **SUCCESS, 4 tests**. La comprobación de las diez firmas contra bytes del ejecutable **sí se realizó localmente**, SHA256 fuente `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`, sin publicar EXE.

## Cómo se genera realmente el origen del emisor

- En `0x403E76–0x403EA5`, al iniciar el procesamiento cerebral, el motor limpia los dos bytes de loci `lobe+0xC1/+0xC2` y, si la clase configura **migration_type=1**, inicializa el correspondiente a **255** como centinela para cálculo de mínimo.
- La variable local de conexiones agotadas (`[esp+0x30]`) se reinicia por clase/neuron `0x40416A–0x40417A`. Suma una unidad si una dendrita *ya* está en `strength0` al entrar al bucle `0x4041A1–0x4041B8`, y si una dendrita pierde fuerza hasta0 en ese tick `0x4047C6–0x4047DE`. No cuenta sólo los eventos nuevos ni un contador único de todo el lóbulo.
- En `0x404803–0x404829`, para clases **Type1**, el programa compara el contador local con el byte del lóbulo y escribe el **mínimo** de ambos. Por eso la variable del emisor refleja un **mínimo entre los registros neuronales/clase recorridos**, no el total de atrofias. Si uno de los registros procesados tiene cero conexiones agotadas, el valor de salida puede quedar0.
- Para clases no-Type1, `0x40482B–0x40484F` verifica que el contador local sea positivo y entonces incrementa el byte del lóbulo en **1 por registro procesado**, saturando en255. No suma directamente cada dendrita agotada. Esta diferencia de Type1/Type2 es verificable sin asumir la semántica del mundo.
- Las rutas [E09h.5](E09_H_05_RESULTADO_EMISORES.md) y [E09h.4](E09_H_04_RESULTADO_ENLACE_LOCI.md) previamente verificadas completan la cadena: locus1/2 produce químicos **53/70** mediante emisores gen124/125, que actúan por receptores127/128 sobre **CHEM2/CHEM3** de Decision, inicialmente `(16,16)` y con inversión. CHEM2/CHEM3 son precisamente las reglas de pérdida de fortaleza en los genes Decision.

**Interpretación técnica:** existe un lazo de retroalimentación endógena de señales de agotamiento y atrofia. **No equivale a emitir automáticamente la cantidad de conexiones perdidas**, porque el agregador Type1 usa un mínimo y el emisor/receptor cuantiza. No se ha demostrado su eficacia conductual en una partida ni el total de callbacks/tiempos/selección neuronal que pueden afectar qué registros se recorren.

## Diferencia exacta respecto del laboratorio

En `e09_i3c4_yoked_metabolic.py` y `e09_i3_metabolic_protocol.py`, el puente químico de laboratorio se llama con **tupla vacía de emisores** y **sin puertos de origen de lóbulo**, por lo que químico53/70 no se genera por esta ruta. El cerebro reducido tampoco tiene agregación original de conexiones agotadas por clase/neuron a `lobe+0xC1/C2`. Reutilizar `Emitter` por sí solo no daría la información de origen adecuada.

**Conclusión:** G-I3c6a-X86-LOCAL verificada estáticamente; G05/G09/G00-H abiertas. El siguiente paso no es conectar emisores por intuición, sino [I3c.6b](E09_02I_I3C6B_UMBRAL_QUIMICO_PRE_REGISTRO.md): comprobar si los contadores máximos de las topologías reducidas **alcanzan el umbral mínimo que cambia un receptor** con los genes originales, antes de programar integración. PR#103 draft, Nilo0.7 y main intactos.
