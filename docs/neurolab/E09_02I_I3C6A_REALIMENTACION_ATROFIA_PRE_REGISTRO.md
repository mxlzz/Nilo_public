# NeuroLab E09.02i–I3c.6a — preregistro forense del circuito de retroalimentación antiatrofia

**21/11/2026 · Fase de verificación ESTÁTICA, antes de desarrollar nuevo adaptador o probar conducta.** Continúa la auditoría basal [I3c.5f](E09_02I_I3C5F_AUDITORIA_BASAL_GEN_C1.md), sin variar tasa, dosis, tamaño, pesos ni el modo de aprendizaje de la microred.

## Motivo y pregunta acotada

El GEN original contiene emisores cerebrales **124: Decision6/locus1→químico53** y **125: Decision6/locus2→químico70** (tipo1, sampling1, gain255, flags1), y receptores Decision **127 (químico53→CHEM2)** y **128 (químico70→CHEM3)** con nominal16, inversión analógica. **CHEM2/CHEM3 alimentan las reglas de pérdida de fortaleza**. Los módulos [E09h.4](E09_H_04_RESULTADO_ENLACE_LOCI.md) y [E09h.5](E09_H_05_RESULTADO_EMISORES.md) ya validan localmente el vínculo **loci1/2 de emisión→pool** y **pool→CHEM2/3**, pero **no establecen** qué escribe los byte origen `lobe+0xC1/+0xC2` en la actualización del cerebro.

**Pregunta falsable:** ¿de dónde proceden esos valores en el código x86 original, qué relación exacta tienen con recuentos de sinapsis agotadas por clase, y en qué orden se escriben respecto de winner/migración y del muestreo químico? Si no puede determinarse, dejar semántica ABIERTA, no conectar emisores a valores inventados.

## Fuente, método y anclas ANTES del auditor

- Sólo `Creatures.exe` auténtico con SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7` y `dad1.gen` SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. Ningún binario de terceros al repositorio; usar `objdump` local estático y verificador de firmas al estilo E09h.4/h.5.
- Anclas a contrastar: inicialización de `lobe+0xC1/+0xC2` en **0x403E76–0x403EA5**, incremento del contador local de agotadas en **0x4041A1–0x4041BC**, selección/escritura de `lobe+0xC1` indexado por clase en **0x404803–0x404872**, y bucle de neuronas/clases que alimenta ese contador. Contrastar destinos de salto, lecturas, writes y la relación con `esp+0x30`; usar direcciones y hashes de bloques sin publicar bytes completos.
- Verificar en GEN los seis genes 88/89/124/125/127/128 y su cabecera real, y cotejar con [E09h.5](E09_H_05_RESULTADO_EMISORES.md). **No confundir** fuente `locus1/2` con CHEM0/1 (`locus13/14`) ni receptor con emisor.
- Contrastar el orden x86 de rama regular C1 `brain tick→emitter→receptor→reactions` de [E09h.6a](E09_H_06A_RESULTADO_FLUJO_SCHEDULER.md), sin afirmar que todas las rutas del runtime siguen ese orden.
- Revisar explícitamente [e09_i3c4_yoked_metabolic.py](../../experiments/neurolab/e09_i3c4_yoked_metabolic.py) y [e09_chemical_bridge.py](../../experiments/neurolab/e09_chemical_bridge.py): comprobar si el ensayo histórico comparado pasa puertos/carga emisores en cada tick. Documentar la diferencia exacta respecto del bucle C1 sin corregirla todavía.

## Contratos y condiciones de cierre

- **G-I3c6a-GEN**: fuente original verificada, dirección de emisión53/70, receptor que llega a CHEM2/3, nominal e inversión; listar fórmulas sin asignar significados no demostrados.
- **G-I3c6a-X86**: firmas de instrucción comprobadas en EXE auténtico, flujo local de escritura de loci sustentado por registros y condición; verificar por qué el mismo contador no es simplemente el total global de conexiones perdidas. Una interpretación ambigua se marca parcial.
- **G-I3c6a-MISSING**: localizar exactamente qué registro/cadena carece de implementación en N y qué pregunta científica falsea. No concluir que toda atrofia se deba sólo a esta ausencia.
- **G05/G09/G00-H ABIERTAS**, independientemente del resultado. Tests sintéticos de parser no reemplazan lectura del EXE original. No implementar por ahora emisores neuronales ni fuente artificial para `lobe+0xC1/+0xC2`. Primero publicar informe/evidencia, decidir siguiente hipótesis y preregistrar ensayo nuevo con grupos y controles.

**Entregables:** verificador estático con pruebas adversariales, registro JSON de direcciones/hashes, informe de incertidumbre y actualización canónica. PR #103 permanece draft, `main`/Nilo0.7 intactos.
