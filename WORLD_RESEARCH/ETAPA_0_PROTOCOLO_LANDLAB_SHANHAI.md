# ETAPA 0 — protocolo experimental de selección ambiental (antes de implementar)

**Propósito:** decidir si los componentes abiertos Landlab y Shanhai cubren procesos requeridos y si es viable compartir relieve sin incoherencias. **No se evalúa arquitectura definitiva ni se incorpora NeuroLab.**

## Contrato de evidencia

Se clonan *upstream* en directorios temporales de CI, se registra commit externo, se instala cada entorno separado y se ejecuta un ensayo de caja blanca mínimo junto con sus tests existentes. No se copian motores al proyecto. Registrar explícitamente casos no comprobados. Las pruebas se ejecutan sin navegador.

## H1 Landlab — relieve mutable y escorrentía calculada

**Hipótesis:** Landlab permite una evolución topográfica autónoma que depende de hidrología simplificada y coeficiente de erosión. **Control negativo:** con erosionador inactivo, la topografía se mantiene idéntica.

**Pruebas diseñadas:** (L1) flujo de descarga positiva con aporte no nulo y descarga nula con aporte nulo en mismo relieve; (L2) 12 pasos con erosión activa producen descenso finito en algún nodo interior, sin valores NaN; (L3) misma escena sin erosión no cambia topografía; (L4) restaurar estado explícito de altura a mitad de secuencia reproduce altura final y descarga; (L5) registrar tiempo por 12 pasos, condiciones de borde, dimensiones y versión; (L6) identificar si el componente conserva sedimento o solo excava.

**Criterio de aceptación:** L1–L4 pasan, con límites explícitos: descargar caudal no equivale a almacenamiento dinámico de agua, y stream power incision puede remover masa sin deposición en dominio. El ensayo NO aprueba por sí solo simulación ambiental integral ni conservación de sólidos.

## H2 Shanhai — hidrología, vegetación, estado y barrera geológica

**Hipótesis:** el modelo ecológico responde a fuentes hídricas y conserva un relieve estático durante la evolución.

**Pruebas diseñadas:** (S1) ejecutar batería de tests upstream y compilar, sin modificar su código; (S2) comparar entrada de agua y humedad en escenario con fuentes frente a fuentes desactivadas; (S3) evolución no cambia matrices de relieve, aunque cambien hidrología/biomasa; (S4) misma escena+parámetros = estado reproducible en horizonte de 100 pasos; (S5) comprobar si `getSnapshot` produce copia o referencia viva; registrar, no presuponer; (S6) registrar tiempos, número de tests y dependencias. No forzar un efecto de biomasa que tenga otras causas sin establecer control.

**Criterio de aceptación:** suite upstream sin fallas y S2–S4 verificables. Se conserva evidencia de limitación S3 y posible snapshot por referencia. Una ecología con relieve fijo no puede considerarse solución de erosión.

## H3 Integración de terreno (gate bloqueante)

**Hipótesis:** conectar alturas flotantes modificadas por Landlab con `heightMap` Uint8 discreto 0–4 de Shanhai **no preserva** diferencias de erosión si se cuantiza ingenuamente. Deben auditarse semántica de celdas/nodos, escala y propiedad del estado.

**Prueba de diseño:** calcular cuantos niveles y cuánto error introduce la conversión de una malla continua a 5 categorías y de vuelta. **No implementar un acoplamiento operativo** hasta demostrar un contrato físico de unidades, resolución, elevación, actualizaciones, retención de detalle y acople climático. Evitar anunciar integración por copiar arrays.

## Decisión de paso

- Si L1–L4 fallan: diagnosticar error de arnés contra documentación; no inventar nueva física.
- Si S1–S4 fallan: documentar qué precondición faltó y reevaluar adopción.
- Si ambos pasan: **no implica que puedan acoplarse**. Preparar ADR sobre elección de base (Landlab, Shanhai, ambos mediante adaptador o ninguna) con evidencia y costos; o ampliar pruebas si H3 bloquea.
- Prohibido desarrollar motor propio por resultados positivos de pruebas aisladas.

## Extensión planificada E0.2 — ¿Landlab puede sustituir una integración heterogénea?

Motivo: las primeras pruebas documentales y ejecutadas muestran que Shanhai usa relieve categórico estático y que Landlab también tiene `Space`, `SoilMoisture`, `Vegetation` y `VegCA`. Antes de escoger dos motores en lenguajes diferentes, **probar reutilización de componentes ya existentes en un solo framework**. No es ampliación de producto.

**H4: sedimentación en Landlab.** Con `FlowAccumulator` + `Space` (modelo científicamente publicado), observar `soil__depth`, `bedrock__elevation`, `sediment__influx/outflux`. Comparar escenario de erosión con un control de erosividad nula y medir si los campos son finitos y los cambios/flujo tienen signo plausible. Registrar fuentes y salida al borde; **no declarar conservación de sedimento sin comprobar balance incluidas fronteras, densidad y aporte de roca madre**.

**H5: humedad y vegetación dentro de Landlab.** Probar `SoilMoisture` y `Vegetation` sobre la misma rejilla de celdas con inputs documentados. Control de suelo seco frente a aporte de lluvia; medir variación de saturación, estrés hídrico y biomasa, reproducibilidad y costo. No se exige que un solo paso produzca bosque; la prueba valida acople técnico y diferencia causal mínima.

**Salida:** si H4 y H5 funcionan, es prioritario un experimento integral **solo Landlab** antes de adoptar Shanhai o construir adaptadores interlingüísticos. Si fallan, registrar estado de componente y contrastar documentación sin cambiar automáticamente arquitectura. Las unidades y los campos Node/Cell requieren contrato antes de unir agua, erosión y vegetación. En ningún caso esta prueba implica empezar el desarrollo final.
