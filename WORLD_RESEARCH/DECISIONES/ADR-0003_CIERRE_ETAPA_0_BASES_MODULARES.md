# ADR-0003 — Cerrar el gate de selección de alternativas de etapa 0; adoptar base experimental modular, NO motor definitivo

**Fecha:** 2026-11-21
**Estado:** **DECISIÓN TÉCNICA EXPERIMENTAL REVERSIBLE**. Stage 0 cerrada **solo para el gate de comparación/reutilización** definido en `BASES_Y_HOJA_DE_RUTA.md`. Ningún motor propio aprobado, ninguna de las etapas 1–8 se considera completada. No es aprobación de arquitectura final ni de producto.

## Pregunta original
¿Debemos desarrollar un motor universal desde cero o reutilizar soluciones existentes para un mundo inicialmente generado, pequeño, continuo y autónomo, con modelos físicos híbridos, reglas comunes y configuraciones estructurales no predefinidas?

## Criterio de gate de la hoja de ruta
Entregables obligatorios en etapa 0: (a) elegir 2–3 fenómenos iniciales con invariantes y pruebas explícitas, (b) ejecutar alternativas existentes **incluidas Sandspiel, The Powder Toy y WorldEngine**, (c) registrar licencias, costo e integración, (d) no desarrollar nueva física antes del gate. Los protocolos y pruebas se conservan en GitHub Actions. **No se exige** seleccionar un único producto o demostrar todas las etapas 5–8 para cerrar solo la evaluación de bases.

## Evidencia propia por capacidad y fenómeno
1. **Movimiento/captura de materia local:** Sandspiel (MIT) y The Powder Toy (GPL-3) **ambos ensayados**. Sandspiel control de viento neutral y 4 escenarios https://github.com/mxlzz/Nilo_public/actions/runs/44944136887 ; TPT motor original C++20 headless con polvo, obstáculo **efectivamente alcanzado** y replay https://github.com/mxlzz/Nilo_public/actions/runs/44958258840 . En TPT existió un falso positivo anterior por pared fuera de alcance; fue invalidado y corregido con hipótesis más estricta, sin ocultarlo. **Invariantes seleccionados para futuros módulos:** no atravesar sólido excluyente, identidad/material tras movimiento si no hay transformación, replay exacto, no introducir materia por un evento sin fuente.
2. **Transporte conservativo de agua y sólidos:** Landlab 2.11 MIT. `SpaceLargeScaleEroder` conservó volumen de sedimentos y produjo acreción en 50 nodos receptores, H7 https://github.com/mxlzz/Nilo_public/actions/runs/44951204189 . `OverlandFlow`+Green-Ampt en cuenca cerrada cerró balance lluvia→superficie+infiltración y pasó control sin lluvia, H11c https://github.com/mxlzz/Nilo_public/actions/runs/44956883575 . **Invariantes:** volumen/massa inicial + entradas - salidas = final dentro de tolerancia física declarada; campos no negativos/finite; unidades m/seg vs mm/h explícitas, fronteras y doble contabilización prohibida.
3. **Patrones por interacción sin plantilla:** Particle Life MIT, 200 partículas, seed 7321 y 80 cuadros; cambiando solo autoatracción g=-0.1 a g=0, pares amarillos <8px 1043→11, distancia al vecino 0.366→14.079px; replay exacto https://github.com/mxlzz/Nilo_public/actions/runs/44958620534 . **Invariantes/criterios de futuro:** diferencia causal bajo ablación, densidad y conectividad de agregados, persistencia tras perturbación; no atribuir vida a un agregado en 80 frames.
4. **Generación inicial:** WorldEngine MIT produciendo elevaciones reproducibles al fijar RNG global y transferibles a Landlab con archivo NPZ; ensayo H6 https://github.com/mxlzz/Nilo_public/actions/runs/44949003747 . **Límite:** alturas y áreas no son unidades del terreno calibradas; el smoke importador impuso escala 0–50m artificial. WorldEngine sigue como posible inicializador, no dinámica.
5. **Referencia de mundo como experiencia:** Ecosystem Explorer es un producto funcional accesible con UI, semilla, guardar/export, reloj acelerable; pruebas H16A https://github.com/mxlzz/Nilo_public/actions/runs/44958493004 . **No se verificó código abierto**; condiciones de uso reservan copyright, modelo declarado simplificado no calibrado. Es **benchmark funcional**, NO candidato de integración de código libre.
6. **Estado/continuidad experimental:** H9 eco-geofísica 90 días, H10b realimentación radiativa, H13/H14 checkpoint entre procesos https://github.com/mxlzz/Nilo_public/actions/runs/44957517450 . Son *ensayos de encaje* que exploran etapas 5/6, NO cierran ni sustituyen los gates formales de dichas etapas.
7. **Modelo integrado alternativo:** DRYP 2.0 Zenodo (2025) auditado estáticamente con hash y 46 módulos Python; requiere CUWALID y binarios CPython 3.10/3.11, no probado runtime Python3.13, autoridad del archivo de licencia ZIP no resuelta. H12a/b https://github.com/mxlzz/Nilo_public/actions/runs/44957301049 . No descartado, pero no dependemos de él.
8. **42 antecedentes heterogéneos** documentados en `REVISION_COMPARATIVA_42_ALTERNATIVAS_2026-11-21.md`. No son 42 pruebas ni 42 motores equivalentes.

## Alternativas consideradas
**A. Landlab como motor universal de materia y estructura:** **NO**. Representación predominantemente geomorfológica con grillas 2/2.5D y campos continuos, sin resolver volumen arbitrario de objetos, contacto tridimensional y estructuras apiladas/voladizos. Es adecuado para procesos de cuenca, no prueba de sustrato de todo el universo.
**B. Sandspiel como todo el mundo:** **NO por ahora**. Motor local fácil de probar y MIT, pero catálogo de especies, escala celular, sin geología ecohidrológica consistente.
**C. The Powder Toy como todo el mundo:** **NO por ahora**. Física local rica, C++/dependencias y GPL-3; sus interacciones son de partículas de tipos predefinidos, no un contrato físico universal y no hay aún integración nativa con campos geológicos reales.
**D. WorldEngine / Ecosystem Explorer como único motor:** **NO**. Uno es generador inicial; el otro es software de usuario final sin licencia pública de código y con reglas simplificadas no verificadas científicamente.
**E. Motor físico propio desde cero:** **NO JUSTIFICADO** hasta demostrar una capacidad faltante con un ensayo y que otras soluciones no la resuelven.
**F. Estrategia experimental modular de reutilización:** **SELECCIONADA PARA ETAPAS SIGUIENTES**: Landlab como proveedor de procesos de terreno/hidrología ya probados; WorldEngine solo inicializador por datos; un motor material local **todavía sin adoptar** (Sandspiel y TPT como benchmarks comparables); Particle Life como caso mínimo de formación por reglas (no físico); Ecosystem Explorer como objetivo funcional externo. No significa integrar simultáneamente todos estos proyectos. Evitar doble propietario de agua/suelo y superponer grillas sin unidades.

## Especificación de tres mecanismos iniciales para validar representación
1. **Material móvil y obstáculo**: una cantidad material con posición y exclusión puede descender/cambiar celda solo si hay espacio. Se medirá con capacidades existentes antes de nueva ley.
2. **Transporte con fuente/borde**: cantidad de material acuoso o sedimentario se redistribuye, conservando inventario + entradas/salidas y unidades. Usar solvers existentes.
3. **Interacción→agregación**: sin plano de estructura final, cambios de interacción local alteran conectividad/compacidad/persistencia según controles. Usar benchmark Particle Life.
La energía térmica y propiedades mecánicas adicionales quedan **por especificar con test físico y función** antes de incorporarlas; no añadir campos por mero afán de universalidad.

## Gate de entrada a etapa 1
Se autoriza **solo una prueba de contrato de estado compartido**, no nuevo solver. Comparar representación discreta/de campos existentes para una caja cerrada mínima con materiales y cantidad; especificar unidad, conservación, espacio disponible, identidad de región y propagación del estado. **No** adoptar una grilla superficial de Landlab como universo volumétrico definitivo: la hipótesis de materia general sigue abierta.

Una decisión futura sobre soporte 2D/3D, datos volumétricos, materialización/estructura, capa gráfica y frecuencia temporal se mantiene pendiente. Antes de simular una ley nueva, evaluar función equivalente en Sandspiel, TPT, Landlab u otros motores (Flow-Lenia/ALIEN/GeoTaichi), y probar que la opción elegida cumple su necesidad.

## Riesgos y revisión
- No comparar distancias en píxeles de Particle Life con metros de Landlab.
- No confundir conservación de columna Green-Ampt con saturación radicular.
- No adoptar soluciones GPL en un programa distribuido sin análisis de obligaciones.
- No considerar avance del reloj del navegador como mundo que continúa cuando navegador está cerrado.
- En pruebas de paisaje, no inferir fenómenos grandes de diferencias de micrómetros.
- Reabrir esta ADR si un motor/estándar nuevo ofrece mejor costo y evidencia, o si las pruebas de materia compartida muestran incompatibilidad fundamental.

**Dictamen:** **ETAPA 0 (gate de selección) SUPERADA con arquitectura modular provisional y capacidades aún no resueltas. ETAPA 1 PUEDE COMENZAR CON PRUEBA DE REPRESENTACIÓN, sin desarrollar física.** No fusionar a `main`; Neon/NeuroLab fuera de alcance. La ubicación de esta documentación en `Nilo_public` es expresamente provisional, con traslado a repositorio específico pendiente.
