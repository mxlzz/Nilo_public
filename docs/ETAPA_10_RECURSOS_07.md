# Nilo 0.7 · Etapa 10 — Recursos e inventario

**Fecha:** 5 de noviembre de 2026. **Rama:** \`refactor/0.7\`.  
**Estado:** Implementación terminada. Cierre condicionado a CI integral del código final.  
[Plan de reestructuración](PLAN_REESTRUCTURACION_NILO_07.md) · [Seguimiento](ESTADO_REESTRUCTURACION_07.md) · [PR #77](https://github.com/mxlzz/Nilo_public/pull/77) · [Issue #74](https://github.com/mxlzz/Nilo_public/issues/74).

## 1. Reauditoría

El \`world.py\` heredado tenía \`gather_material\`, \`nearest_known\`, \`forage_source\`, la recolección de depósitos, la búsqueda de alimento y el corte de madera mezclados con navegación, experimentos y construcción. Algunos movimientos materiales operaban sobre pares de diccionarios mediante sumas/restas independientes. Se revisaron los consumidores en \`clockwork.py\`, \`vessels.py\`, \`structural_loads.py\`, \`world.py\`, \`island_planning.py\`, catálogos, pruebas de tiempo e importación de partidas.

**Hallazgos confirmados:**

1. La recolección remota tenía dos decisiones de origen: \`prepare_navigation\` escogía un depósito y lo almacenaba en \`navigation.resource_at\`, pero la fase física invocaba nuevamente \`nearest_known\` sin utilizar ese dato. Al finalizar el viaje podía cambiar silenciosamente a otra fuente accesible.
2. La extracción, el forraje y el corte modificaban depósitos/inventario directamente, sin un contrato único de transferencia y con validaciones dispersas. En un saldo inválido, las operaciones podían comportarse de manera inconsistente.
3. El rebrote de comida actualizaba los depósitos en recorrido; si una fuente posterior contenía datos corruptos, podía dejar acreditaciones parciales antes de fallar.
4. Los métodos \`guardar\`, \`retirar\`, \`transferir\` (sólidos) y \`depositar_carga\`/\`recuperar_carga\` tenían registros de inventario y reservas con implementación propia. Se conserva su física de capacidad y accesibilidad, pero se delega el balance.
5. La conservación de materiales en \`combine\`, \`craft\`, \`assemble\`, \`construction.apply_intervention\`, y conversiones por desmontaje pertenece a la futura revisión de objetos/interacciones (11–12). **Todavía hay gastos de materiales en esos handlers**; no se los declara unificados.

## 2. Contratos e implementación

\`nilo_runtime/worlds/resources.py\` es el dueño de fuentes/recursos de \`isla_v1\`; importa topología y navegación, nunca \`world.py\`, aplicación, HTTP o cognición.

- \`stock_units\`: exige saldo entero no negativo. Un save inconsistente queda visible para diagnóstico, sin normalizar cantidades retrospectivamente.
- \`transfer_units(source, source_key, destination, destination_key, quantity, maximum=None)\`: valida ambos extremos antes de modificar. Exige \`type(quantity) is int\` positivo, reserva suficiente, y capacidad opcional; devuelve \`StockTransfer\` inmutable con los saldos antes/después. La suma de unidades de los dos extremos se conserva. No se crea un registro de partida adicional ni se altera el RNG.
- \`consume_units\`: consume del inventario tras comprobar disponibilidad y deja saldo no negativo; \`eat\` conserva su regla corporal, mientras que el débito material se centraliza.
- \`gather_material\`, \`nearest_known\`: normalización de catálogo y búsqueda de depósito revelado, con ruta transitable y lugar físico de trabajo; reexportadas por \`world.py\` para compatibilidad.
- \`harvest_at\`: exige coordenada válida y revelada, mismo nivel, distancia de trabajo menor o igual a una casilla, símbolo/material compatibles y stock finito. Extrae hasta **dos unidades**, con el contrato de tiempo **12 + 5 por unidad** de trabajo y evidencia por variaciones reales.
- \`gather_action\`: dueño de la operación física única. El modo directo histórico conserva viaje/relato; el modo moderno programado recibe \`_resource_at\` desde la ruta efectivamente planeada. Si el depósito se agota, cambia o queda fuera de alcance, la acción falla **sin cambiarlo por otro**.
- \`forage_action\`, \`forage_source\`: stock vegetal local. Mantiene por compatibilidad la reserva inicial implícita de tres por celda apta, rebrote de una porción cada **2.880 minutos simulados** (48 h), máximo tres y límite voluntario de **12 porciones** en inventario. La maduración revisa todas las fuentes antes de acreditar rebrote y rechaza saldos inválidos sin efectos parciales.
- \`cut_wood\`: el corte con una herramienta válida consume una unidad de la reserva leñosa y acredita exactamente una en el inventario, sin obtener madera si el depósito está vacío.
- \`vessels.py\`: las transferencias de **sólidos enteros** entre recipientes y el inventario usan \`transfer_units\`. La flotación, la capacidad y los líquidos siguen con la física histórica, incluyendo agua fraccionaria y su propia procedencia de fuente ambiental.
- \`structural_loads.py\`: el depósito y la recuperación de lotes estructurales comparten \`transfer_units\`, manteniendo límites por masa, ensayos y carga instalada. Las muestras de un ensayo que no deja carga depositada no se debitan.

**Frontera temporal:** \`nilo_runtime/application/clockwork.py\` continúa aplicando viajes por casilla y fases \`viaje → trabajo\` de la etapa 05. En \`gather\`, el depósito se liga al \`navigation.resource_at\` seleccionado al inicio. Solo después de completar viaje y trabajo, y de verificar llegada no bloqueada, se ejecuta \`harvest_at\`; un fallo no produce inventario. Los replays históricos conservan su camino antiguo (sin pin), para evitar reescribir causalmente partidas anteriores.

**Compatibilidad:** API pública de \`world.py\` conservada; esquemas SQLite v5, \`VERSION\`, algoritmo generador, catálogos, necesidades, métodos LLM y semilla no cambian. Las lecturas de inventario o depósitos no inventan información de celdas ocultas.

## 3. Cambios intencionales frente a 0.6.4

- Fuente remota obligatoria: no cambiar de depósito cuando el original era distinto al final de la actividad. **Corrección física**.
- Rechazo de saldo negativo/no entero y de transferencias mayores al disponible, sin acreditación parcial. **Corrección de integridad**, no sanitización retroactiva de saves.
- Si no se especifica cantidad de sólido transferida a un recipiente, la selección automática usa una cantidad **entera** dentro de la capacidad real; ya no se truncan silenciosamente fracciones de sólido. **Corrección de integridad**.
- Forraje con maduración verificada antes de mutar. Mantiene cifras de rebrote, disponibilidad y límite de alimento previos.
- No se cambia el balance de agua con recipientes ni la física de nutrición/hidratación, que será auditada integralmente en etapa 13.

## 4. Pruebas y salida verificable

\`tests/test_recursos_10.py\` cubre 18 casos focalizados de: balance y registro antes/después, rechazo sin mutación de cantidades inválidas (incluidas \`bool\`, no enteros, NaN e infinito), capacidad, extracción de una/dos unidades, agotamiento, selección vinculada, no sustitución de origen, datos ocultos, distancia/capa, alimentos y rebrote, saldos corruptos, corte, consumo y dos integraciones de **viaje/trabajo reales con Simulation**.

\`tools/auditar_recursos_10.py\` verifica un único propietario de funciones, ausencia de imports invertidos, consumidor de alimentos y delegación de cargas. \`.github/workflows/validacion.yml\` ejecuta auditoría, pruebas focalizadas y suite completa antes de escenarios, continuidad de RNG, replay y ZIP. El empaquetador incluye \`nilo_runtime/worlds/resources.py\`, exigido en el ZIP extraído. El laboratorio registra la traza de \`resources.py\` y enlaza al archivo de la rama pública.

**Compatibilidad histórica:** los workflows públicos migran seis SQLite sintéticas (0.5.9.4.2, 0.6.0, 0.6.4, inicial/progresada) en copias, preservan el hash de cada original y comparan seis semillas; no se utilizan partidas personales. [CI histórica del cambio de balance estructural #42010458416](https://github.com/mxlzz/Nilo_public/actions/runs/42010458416): **success**. La CI integral del último código queda por vincular tras su finalización.

## 5. Alcances expresamente pendientes

- **11:** catálogos/materiales/objetos, contabilidad de conversiones, identidad y componentes físicos.
- **12:** debitar/acreditar materiales de \`combine\`, \`craft\`, \`assemble\`, \`build\`, \`modify\`, desmontaje y salvamento mediante transacciones completas; modelar capacidades físicas y no crear recursos desde un mensaje o nombre.
- **13:** metabolismo, comer/beber y evolución de reservas corporales, con efectos temporales independientes.
- **14:** proyecciones de percepción sin escritura accidental, incluida la visibilidad de materiales.
- **18/22:** estadísticas de SQLite, restauración completa y benchmarks generales de simulación.
- **23:** mejora o no mejora de comportamiento real con Gemini/Groq. Los tests sintéticos no demuestran cambios cognitivos.

**Cierre exigido:** CI del código final verde, 18 tests focalizados y suite completa, seis saves históricos, escenarios, ZIP portable, replay determinista y registro actualizado en #74/PR #77. No fusionar el PR ni publicar 0.7.0 hasta la etapa 24.
