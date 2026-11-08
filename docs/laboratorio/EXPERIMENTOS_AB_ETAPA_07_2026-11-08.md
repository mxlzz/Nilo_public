# Laboratorio Nilo 0.7.1 · Etapa 07 — experimentación aislada y A/B

**Fecha:** 2026-11-08. Implementado en la rama `work/0.7.1-lab-stage07-ab`, dependiente de la etapa 06 (PR #90).

## Necesidad y decisión de diseño

Observar cómo respondería el motor o el LLM bajo condiciones alternativas **sin intervenir la partida original**. Separar hechos experimentales de las inferencias que se hagan sobre la calidad de una decisión; una única consulta de LLM nunca demuestra superioridad de un prompt. El laboratorio conserva su uso central: experimentar sin convertir Nilo en un sistema de objetivos impuestos.

Se incorpora una página `/experimentos` en el laboratorio y un servicio local `POST /api/lab/experiment` con modalidades explícitas. Reutiliza `SimulationSandbox` y `Simulation.plan_ready / tick` del motor: no se implementó otra física.

## Modalidades

| Modalidad | A y B | Qué se verifica | Qué NO demuestra |
|---|---|---|---|
| **Contexto calculado A/B** | Misma percepción congelada en SQLite temporal. A: perfil baseline; B: variante validada con campos opcionales y nota adicional. | SHA de misma referencia y SHA de ambas solicitudes, cambios de campos, bytes, mensajes literales. **0 consultas reales.** | No conocemos ninguna decisión del LLM; menos bytes no equivale a mejor comportamiento. |
| **Guiones físicos A/B** | Dos mundos SQLite temporales creados desde semilla idéntica o backup readonly de partida. El usuario elige hasta seis acciones por rama. | Hash del mismo estado inicial, resultados reales de `Simulation.plan_ready / tick`, diagnósticos físicos y estado final por paso. **0 consultas reales.** | Si difieren las acciones, sus consecuencias no son un efecto del contexto LLM. Son secuencias guionadas, no decisiones autónomas de Nilo. |
| **Deliberación LLM A/B** | Dos clones idénticos; igual proveedor/estado inicial, A baseline y B variante. **Solo bajo confirmación expresa**, exactamente 2 consultas. | Solicitud literal usada, respuesta cruda, parseo, normalización/errores, tokens que devuelve el proveedor. | No se ejecuta el plan. La temperatura/no determinismo impiden atribuir con certeza la diferencia al perfil. |
| **Evolución LLM A/B (2 rondas)** | Mismas dos copias iniciales; cada ronda pide una deliberación con su perfil, normaliza y ejecuta el plan en **su propia copia**. **Solo bajo confirmación expresa**, máximo 4 consultas totales; se deja de consultar una rama si tiene un plan sin terminar. | Contextos construidos antes de cada consulta, decisiones y resultados físicos observados en cada copia, estados y eventos, tiempos. | Desde la segunda ronda los contextos pueden ser distintos por la trayectoria previa. No es evidencia causal controlada de mejora; no se completan runs largos ni se garantiza comportamiento reproducible de la API. |

## Contratos de reproducibilidad

- La semilla es válida entre 0 y 1.000.000.000.
- En estado **nuevo**, las dos copias usan la misma semilla, el mismo generador de aleatoriedad y el mismo indicador de kit. En estado **guardado**, ambas se crean por `sqlite3.backup` **desde el archivo seleccionado en el servidor**. La UI no suministra una ruta y no se aceptan rutas arbitrarias.
- El sandbox despeja planes y acciones pendientes al iniciar el experimento (esto es parte del contrato de comparación: **no equivale a continuar exactamente el reloj autónomo de la partida original**). La partida fuente no se escribe.
- La huella de referencia proviene de una proyección canónica de estado físico/perceptible, **no** del contenido binario de SQLite.
- Las previsualizaciones usan el constructor real de prompt/presupuesto para el proveedor elegido y su serializador. La llamada real utiliza el payload calculado sin reconstruir otro mensaje.
- El resultado de una acción sin medición física se trata como falta de prueba de ejecución, nunca como éxito.
- El modo live no utiliza una ruta arbitraria ni acepta credenciales del navegador; las lee del archivo local de configuración instalado. Se ejecuta con bloqueo para evitar **dos runs live simultáneos**, sin reintentos automáticos. Se aplica al menos 15 segundos de separación entre consultas al mismo proveedor.
- No se modifica el perfil activo, la configuración persistida, el estado original, los archivos Python ni ninguna ley física.

## Interfaz y exportación

En `/experimentos` se elige modalidad, semilla, referencia nueva o copia guardada, proveedor y campos opcionales de la variante. El modo físico ofrece guiones de acciones JSON con ejemplos. El ensayo sin red es el predeterminado.

Para un ensayo con LLM, el botón solicita confirmación informando **2 o 4 llamadas** y la posible cuota/costo. No se permite iniciar llamadas de prueba simplemente al abrir la página, cambiar un checkbox o construir contexto.

La respuesta distingue el estado de referencia, huellas, llamadas efectivamente realizadas, resultado físico por rama y límites de interpretación. Puede copiarse y descargarse como archivo JSON para análisis posterior. No se usan resúmenes generados por IA para reemplazar los hechos literales.

## Limitaciones y validación necesaria

- Las solicitudes reales dependen de las credenciales del usuario y se prueban con **respuestas sintéticas** en CI; los tests automáticos no hacen consultas pagas.
- El modo multivuelta solo hace hasta dos deliberaciones reales por rama, no una simulación de varios días.
- El modelo puede producir un plan que el motor rechace; se muestra ese resultado y se detiene la rama si queda una acción pendiente.
- Las divergencias entre dos ejecuciones de modelo pueden provenir de muestreo; las comparaciones concluyentes exigirán múltiples muestras y criterios en la etapa 11.
- Una copia desde partida guardada se inicia en modo laboratorio, sin continuar decisiones que estaban pendientes; se debe advertir al observador cuando elija esa referencia.
- La prueba manual visual con un run real y la integración de PRs previos son tareas pendientes.

### Aceptación de etapa

1. Ambos contextos A/B calculados desde el mismo estado y resultados con SHA reproducible.
2. Guiones físicos iguales desde el mismo estado: mismas consecuencias, sin API, sin modificar save.
3. Guiones diferentes: conservar resultados originales, sin atribuir causalidad al contexto.
4. Claves/proveedores ausentes o sin consentimiento: **cero llamadas**.
5. Una deliberación real sintética: respuesta original, normalización y tokens, **sin ejecución**.
6. Dos rondas reales sintéticas: resultado físico de cada plan y estado disponible siguiente, con límites explícitos.
7. No aceptar rutas de archivo, URLs de proveedor ni campos de configuración arbitrarios en HTTP.
8. Página navega desde el laboratorio, modo inicial sin red y confirmación explícita para proveedor.
9. Suite de regresión completa, pruebas HTTP, sintaxis JS y empaquetado/migración Windows.

**Próxima etapa 08:** análisis transversal y QA de experiencia/navegación, matriz campo × turno, seguimiento de memoria y patrones, y prueba con una partida real antes de fusionar la cadena.
