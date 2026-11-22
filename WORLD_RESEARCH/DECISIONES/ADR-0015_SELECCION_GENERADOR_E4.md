# ADR-0015 — E4: reutilizar WorldEngine como generador de condiciones iniciales, no como motor físico

**2026-11-22. Estado: decisión experimental reversible para H29, NO adopción de arquitectura definitiva.** Etapa3 cerrada provisionalmente en [ADR-0014](DECISIONES/ADR-0014_CIERRE_GATE_ETAPA_3.md); etapa4 pide generar estado inicial razonable/repetible, sujeto a reglas posteriores, sin «simular millones de años» para obtenerlo ni prefijar estructuras finales.

## Alternativas y evidencia existente

1. **WorldEngine** [Mindwerks/worldengine](https://github.com/Mindwerks/worldengine), **MIT**, revisión fijada `3b9113ecfad884cab4b32081d138a15e6262ada8` (2026-11-16), generador plate-tectonics/clima/relieve con Python≥3.11, NumPy/PyPlatec1.4.3. [Prueba anterior](../experiments/test_worldengine_candidate.py) y [bridge anterior](../experiments/probe_worldengine_to_landlab.py) con [CI histórica](https://github.com/mxlzz/Nilo_public/actions/runs/44949003747) mostraron terreno finito, reproductibilidad condicionada a resetear **también el RNG global NumPy**, exportaciónNPZ y evolución en Landlab. **Limitaciones verificadas:** no aporta altitudes originales en metros; el bridge viejo normaliza cada heightmap linealmente a0–50m sin calibración y trata muestras de celdas como nodos Landlab sin identificar el offset; solo prueba erosión técnica. **Candidato preferido para H29**: ya existe y no duplica desarrollo, pero debe declarar la convención métrica y geometría.
2. **Landlab2.11** como generador con campos de pendiente/ruido/fractales: gran compatibilidad nativa con el solver erosionador ya usado, pero el modelo anterior H9 tenía una cuenca prescrita manualmente y ningún paisaje de placas de WorldEngine. Repetir una fórmula inventada para generar terreno no aporta objetivo ni reduce complejidad si el bridge original WorldEngine funciona.
3. **Ruido procedimental independiente (OpenSimplex/FastNoiseLite)**: licencia/código abierto potencial, pero por sí solo no define geología, hidrología ni balance y añadiría un tercer proveedor sin necesidad. No seleccionarlo.
4. **Generación aprendida por IA, asset gráfico o malla a mano**: contradice intención de condiciones iniciales reproducibles, auditables y sujetas a física. No necesaria en E4.
5. **DEM real (USGS/IGN/GEBCO)**: proporciona relieve existente y unidades, útil como validación futura, pero no es generación procedimental por semillas ni objetivo del gate E4.

## Decisión de contrato espacial

Representar los samples 16×32 de WorldEngine como **muestras ubicadas en el centro de celdas horizontales** de 100m×100m. Landlab `RasterModelGrid(18,34,xy_spacing=100m)` utilizará **exactamente esas512 muestras en sus512 nodos core interiores**, y un halo de nodos de frontera alrededor generado por extensión de bordes para implementar condiciones del solver. Definir desplazamiento de origen de −50m en X/Y: nodo interior index(1,1) físicamente representa el centro original (50m,50m). **No afirmar equivalencia topológica a celdas con volumen** ni usar halo como materia original; su máscara de masa es0. Los datos centrales no se reinterpolan ni se cuantizan.

Alturas nativas de WorldEngine **no son metros**. Para una **prueba estrictamente de compatibilidad numérica**, declarar convenio explícito `z_m=50*(z_raw−min_raw)/(max_raw−min_raw)`; esto produce valores computacionales con unidad atribuida «m nominal» y no es calibración geológica. Los resultados de erosión de Landlab bajo esta convención no representan tasas/escala naturales. Conservar raw original y hashes para auditar traducción y evitar confundir categorías con elevación.

**Materia inicial**: suelo móvil A en cada nodo core con espesor nominal uniforme0,15m y densidad abstracta1200kg/m³, área nominal10.000m², almacena solo masa en xarray. Masa total512*0,15*10.000*1200=**921.600.000kg**. Bedrock inmóvil como geometría independiente. Simular con proveedor de H9 `PriorityFloodFlowRouter+SpaceLargeScaleEroder`, **no** reprogramar una ley de erosión, y publicar cambios con balance explícito de salida.

## Gate H29

Misma semilla WorldEngine y RNG global ⇒ hash de alturas igual; distinta semilla WorldEngine ⇒ terreno diferente, finito/no plano, dos runs independientes. H29 debe rechazar estados imposibles y comprobar que campo central y geo-coordenadas no se deforman; el owner de sedimento de Landlab tiene balance de materia por paso, control sin erosividad, replay y checkpoint, con tests por dos semillas. [Prerregistro E4 H29](../ETAPA_4_H29_PROTOCOLO_SEMILLAS_TERRITORIO.md). **No se considera E4 aprobada por escribir ADR o hacer una captura de mapa; solo por CI completa y auditoría.**

**Notas de gobernanza:** pyDeltaRCM H20A no se adopta por falta de conservación estricta de sedimento; ningún nuevo solver físico propio; la capa local Bullet no se acopla todavía a Landlab, un gate posterior E5. Main/NeuroLab intactos.
