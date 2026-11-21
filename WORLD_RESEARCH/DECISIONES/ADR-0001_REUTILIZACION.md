# ADR-0001 — Reutilizar primero; suspender desarrollo de motor propio

**Fecha:** 2026-11-21  
**Estado:** DECISIÓN DE PROCESO ADOPTADA; ELECCIÓN DE MOTOR NO RESUELTA  
**Ámbito:** generación inicial y procesos ambientales del Mundo autónomo; ningún componente cognitivo.

## Problema

¿El proyecto necesita implementar desde cero su propio modelo de materia/física/terreno o puede aprovechar motores y bibliotecas de código abierto? El primer prototipo `matter_v0.py` se escribió antes de resolver esta cuestión.

## Criterios

- Mundo autónomo pequeño, originado por reglas y luego persistente.
- Regla híbrida: procesos conocidos aproximados + espacio para nuevas organizaciones.
- Propiedades e interacciones compartidas que afecten el mismo estado del mundo.
- Sin catálogo cerrado de formas finales; posible control de condiciones y mutaciones en el futuro.
- Separación entre núcleo y visualización, determinismo, reproducibilidad y guardado.
- Licencia clara y compatible, madurez, actividad, costo de adaptación y posibilidad de ejecución sin interfaz.
- No aceptar promesas de README como capacidad verificada sin ejecutar tests propios.

## Candidatos con fuentes primarias verificadas (21/11/2026)

### Sandspiel
- Repositorio: https://github.com/MaxBittker/sandspiel
- Juego celular 2D con reglas materiales, construido en Rust/WASM/WebGL.
- Licencia verificada: MIT. Último push consultado: 2026-09-10; más de 3.000 estrellas (indicador indirecto, no calidad).
- **A favor:** dinámica local, código adaptable, interacciones procedurales, costo de entrada relativamente acotado para sandbox 2D.
- **En contra / no comprobado:** persistencia prolongada sin navegador, simulación headless, conservación rigurosa, exportación a un esquema de materiales general, escala 3D, física cuantitativa y facilidad de acoplar un generador externo.
- **Uso candidato:** motor experimental de interacción local, no creador directo de paisajes geológicos.

### Sandspiel Studio
- Repositorio: https://github.com/MaxBittker/sandspiel-studio
- Editor de reglas de elementos mediante bloques para crear simulaciones. Licencia MIT, push consultado 2026-10-11.
- **A favor:** exploración de reglas sin reescribir un motor cada vez.
- **Pendiente:** comprobar accesibilidad y ejecución sin interfaz, su API/serialización, y hasta qué punto exporta una simulación autónoma.
- **Uso candidato:** laboratorio de reglas y experimentación; no dar por hecho que es motor extensible del mundo final.

### The Powder Toy
- Repositorio: https://github.com/The-Powder-Toy/The-Powder-Toy
- Física celular/partículas, temperatura, gravedad, presión, líquidos, gases y muchos materiales; Lua API. Proyecto establecido y con actividad reciente (push 2026-11-19).
- **Licencia:** GPL-3.0, obliga a analizar obligaciones de distribución si se integra/adapta código; no equiparable sin más a MIT.
- **A favor:** interacciones ya resueltas y amplitud de fenómenos.
- **Limitación:** enfocado a sandbox 2D y materiales programados; no garantiza generación abierta de nuevas organizaciones. Acoplamiento y control externo sin interfaz pendientes de demostrar.
- **Uso candidato:** baseline de comportamientos físicos y posible motor si la licencia y arquitectura encajan.

### WorldEngine
- Repositorio: https://github.com/Mindwerks/worldengine
- Genera elevación, placas, precipitación, erosión y biomas; Python, MIT, salida reutilizable (incluyendo protobuf y HDF5 según documentación). Push consultado: 2026-11-16.
- **A favor:** útil para el estado inicial sin simular millones de años, con interfaz de datos.
- **Limitación:** generador de condiciones iniciales, no dinámica física continua de un mismo mundo.
- **Uso candidato:** primera generación geográfica. Debe probarse si la salida puede transformarse sin contradicciones al estado de otro motor.

### Ecosystem Explorer — referencia funcional prioritaria (incorporado tras auditoría de omisión)
- Sitio: https://www.ethanjhulbert.org/ecosystem-explorer/
- Descripción del autor: https://www.ethanjhulbert.org/ecosystem-explorer/about/
- Condiciones de software/copyright: https://www.ethanjhulbert.org/privacy-legal/
- **Encaje conceptual muy alto:** generación inicial coherente, evolución temporal, relieve, agua, erosión, sedimentos, clima, temporadas, vegetación y fuego interactúan sobre celdas; inspección del estado, guardado local y exportable; visualización 2D/3D.
- **Evidencia disponible:** documentación y aplicación pública; capacidades descritas por el autor. No se ejecutó una batería controlada de pruebas ni se auditó su motor interno.
- **Límite frente al objetivo de investigación:** comportamientos ambientales simplificados y hábitats construidos con reglas conocidas. No hay evidencia de generación abierta de nuevas leyes o mecanismos de organización.
- **Reutilización de código NO acreditada:** en búsqueda pública por nombre/autor no se identificó repositorio oficial ni licencia de código para este proyecto. Las condiciones generales del sitio impiden presumir derecho de copia/adaptación. No equivale a afirmar que el código es inaccesible o que el autor no otorgaría permiso.
- **Papel propuesto:** **baseline funcional de mayor prioridad** para el acoplamiento ambiental y para criterios observables de intervención, persistencia, inspectabilidad y evolución; no copiar ni integrar su código sin autorización expresa.
- **Acción de etapa 0:** ensayar escenarios comparables en la aplicación si se dispone de acceso interactivo, registrando estado inicial, semilla, intervención, evolución y exportación. Una prueba de caja negra puede validar comportamiento, pero no arquitectura ni licencia.

### GeoTaichi
- Repositorio: https://github.com/Yihao-Shi/GeoTaichi
- Modelos geofísicos MPM/DEM y acoplados; Python y Taichi, GPL-3.0; push consultado: 2026-11-18.
- **A favor:** física avanzada de material granular, deformación, fluidos.
- **En contra:** mayor costo de integración, requisitos numéricos y carga computacional potencial; 3D y física avanzada no son todavía requisitos validados.
- **Uso candidato:** referencia o módulo especializado futuro, no núcleo por defecto.

### SoilMachine (complementario)
- https://github.com/weigert/SoilMachine
- Erosión hidráulica/eólica y terreno multicapas con materiales de suelo; README declara MIT; último push observado 2023-06-11; dependencia TinyEngine.
- **A favor:** buen antecedente de materiales y sedimentación acoplados con terreno.
- **Pendiente:** situación exacta del archivo de licencia, integración y mantenimiento.
- **Uso candidato:** estudiar su representación multicapas antes de elegir una cuadrícula de material universal.

### Otros exploratorios (sin decisión)
- https://github.com/Gravitas40E/WorldSmith — motor de generación planetaria orientado a determinismo y procesos; Apache-2.0; nuevo y con madurez no demostrada.
- https://github.com/Bradorez/evo_plants_3d — simulación ambiental en TypeScript con terreno/agua/erosión/plantas; pequeño, sin licencia verificada en los metadatos del repo. No asumir que el código es reutilizable.

## Hallazgo crítico

**No se justifica crear un motor desde cero ahora.** Distintas capacidades centrales ya están resueltas en proyectos que admiten evaluación de código y extensiones. Tampoco se justifica comprometerse ya con un único motor: las piezas pueden pertenecer a modelos matemáticos incompatibles y la integración puede costar más que adaptar un módulo pequeño.

El spike propio `matter_v0.py` tiene utilidad como **especificación ejecutable de algunas invariantes**, no como prueba de necesidad de implementar física original. En particular representa masa por material en celdas con volumen aditivo y no admite aún dinámica natural; no hay justificación demostrada para usar esa representación como sustrato universal.

## Decisión de proceso

1. **Congelar expansión del spike propio.** Mantener código/tests como referencia experimental histórica.
2. **Adoptar principio reutilización-primero.**
3. **Usar Ecosystem Explorer como baseline funcional prioritario** del ambiente integrado (sin copiar código sin permiso). **Probar Sandspiel/Sandspiel Studio** como laboratorio local de interacción de materia y **WorldEngine** para generar condiciones iniciales. Contrastar The Powder Toy como motor de materiales más completo. No implica unir inmediatamente sus códigos.
4. Si uno satisface el contrato, preferir adaptarlo o conectarlo frente a implementar lo mismo. Solo construir el mínimo no cubierto por alternativas verificadas.
5. **La elección de engine sigue abierta hasta una prueba de encaje técnico ejecutada y documentada.** Decisión distinta a dejar el trabajo sin rumbo: el siguiente paso es un benchmark acotado, no otro módulo de física propia.

## Plan de prueba de encaje (etapa 0, aún NO ejecutado)

### Caso A: masa y movilidad
- Misma configuración pequeña de dos materiales abstractos (uno móvil, uno inmóvil) en una región cerrada.
- Medir masas por material antes y después de N pasos; caída, reposo, colisiones y estabilidad.
- Control: gravedad deshabilitada o equivalente, manteniendo todas las demás condiciones.

### Caso B: transportes y patrones
- Pendiente simple y material móvil; observar acumulación y transporte sin función especial «construir monte».
- Medir distribución final, variabilidad por semilla y sesgos de actualización.
- Sin concluir «emergencia» solo por formarse un patrón.

### Caso C: interoperabilidad futura
- Crear/guardar/reabrir estado, reproducir al menos una continuación; observar/leer estado sin modificarlo; modificar material o regla y volver a correr.
- Documentar qué es reutilizable sin cambio, qué requiere adaptador y qué exige alterar arquitectura.
- Una generación WorldEngine pequeña servirá como dato de entrada **solo si** puede representarse honestamente en el simulador candidato.

### Comparación
Candidatos mínimos: Sandspiel y The Powder Toy para reglas físicas; WorldEngine se evalúa por separado como generador, no se le exige simular flujo en tiempo real. Sandspiel Studio es variante para edición de reglas.

Registrar:
- versión/commit upstream, sistema, dependencias, licencia, parámetros y semilla;
- resultados medidos de casos A/B/C, pass/fail;
- facilidad de modificar reglas, acceder al estado, continuar sin UI;
- consumo de tiempo, CPU y RAM al mismo tamaño/resolución;
- riesgos, cambios necesarios y costo estimado de integración.

**Gate de elección:** si no se ejecutaron al menos dos candidatos de materiales con pruebas comparables, no aprobar adopción de motor ni continuación del spike como núcleo. Si uno no se puede ejecutar en entorno disponible, registrar bloqueo y evidencia de revisión técnica, sin sustituirlo por una afirmación de capacidad.

## Resultado provisional

- **Se decidió evitar desarrollo desde cero sin necesidad demostrada.**
- **No se decidió aún integrar ningún proyecto ni copiar código externo.**
- **No hay pruebas comparativas ejecutadas** hasta este ADR.
- La etapa 0 permanece abierta. Al cerrarla, registrar un ADR-0002 con adopción, descarte o combinación fundamentada y actualizar el plan versionado.

## Nota de corrección de cobertura — 2026-11-21

Ecosystem Explorer había sido identificado previamente en la conversación como un proyecto muy pertinente, pero se omitió de la comparación inicial: incumplimiento del principio de cobertura de antecedentes. Se añade expresamente como candidato de referencia ambiental y se obliga a comprobar si el candidato relevante ya está en el registro antes de decidir qué examinar a continuación. Esta actualización **no constituye prueba de reutilización del código ni adopción de un motor**.
