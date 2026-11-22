# ADR-0004 — Propiedad del estado material e integridad de actualizaciones

**Fecha:** 2026-11-22. **Estado:** DECISIÓN EXPERIMENTAL REVERSIBLE — válida solo para el laboratorio de estado de etapa 1. **No** es arquitectura final del mundo ni cierra E1. No modificar `main`, ni NeuroLab.
**Evidencia:** H1 https://github.com/mxlzz/Nilo_public/actions/runs/44959062997 ; H2/H2b https://github.com/mxlzz/Nilo_public/actions/runs/44986371590 ; H3 https://github.com/mxlzz/Nilo_public/actions/runs/44986576611 .
**Fuente de pruebas:** `ETAPA_1_H1_RESULTADOS_ESTADO_MATERIA.md`, `ETAPA_1_H2_RESULTADOS_PROPIEDAD_ESTADO.md`, `ETAPA_1_H3_RESULTADOS_VALIDACION_COMMIT.md`.
**Marco:** `BASES_Y_HOJA_DE_RUTA.md` / `DECISIONES/ADR-0003_CIERRE_ETAPA_0_BASES_MODULARES.md`.

## Necesidad
Un mundo persistente no puede tener dos inventarios inconsistentes de la misma materia al acoplar módulos. La primera prueba debe conservar cantidades y etiquetas en un estado que pueda ser observado, actualizado, persistido y reconstruido sin desarrollar física nueva.

## Alternativas examinadas
**A. Dos copias independientes Landlab/xarray con sincronización manual:** riesgo de actualización perdida y dos propietarios del mismo valor. H2 `copy=True` confirmó separación de memoria. **NO** como método predeterminado de intercambio; solo snapshots deliberados.

**B. Un tensor xarray/NumPy canónico para masa estructurada, con vistas Landlab `copy=False`:** H1 validó proyección exacta y niveles; H2 alias bidireccional y conservación; H2b demostró **pérdida de alias cuando se reemplaza la variable completa** y necesidad de `rebind`. H3 comprobó validación integral y commit de una copia de prueba con alias conservado. **SÍ, para los próximos ensayos limitados de materia.**

**C. Un objeto MatterGrid propio como motor/fuente autoritativa de toda materia:** 8 pruebas históricas pasan, pero agrega otro sistema de almacenamiento, no simula física, es bidimensional y mutable sin control de concurrencia. **NO** promoverlo a nuevo motor; conservar solo como oráculo y ensayo de invariantes.

**D. Pandera como validador existente de xarray:** versión 0.36.0 aprobada para dimensiones, metadatos, unidades, datos finitos y capacidad mediante `DatasetSchema` + checks, y balance de fuentes controlado fuera de schema. MIT, actualizado en 2026. **SÍ como validador opcional de frontera/candidatos**, NO como costo obligatorio de cada microtick.

**E. Interfaz estándar de acoplamiento BMI / PyMT:** presentes en revisión `REVISION_COMPARATIVA_42_ALTERNATIVAS_2026-11-21.md`, pero todavía NO ensayados con un estado de materia específico; BMI regula comunicación de variables/unidades/grillas/tiempo, no garantiza identidad de almacenamiento ni compatibilidad física. **Conservar como candidato antes de diseñar un orquestador propio.**

## Decisión para siguiente ensayo
1. **Owner de inventario en el laboratorio:** un `xarray.Dataset` (array NumPy subyacente), variable única `material_mass(material,level,y,x)` con unidades explícitas; densidad en `material_density`, ocupación derivada. En esta instancia las capas son índices de almacenamiento, **no volumen 3D simulado**.
2. **Lectores/módulos compatibles:** reciben vistas mapeadas y verificadas con `np.shares_memory`, no duplicados silenciosos. Landlab se usa para procesos ambientales en mallas propias y solo consume vistas si las topologías coinciden. **No se afirma que todos sus componentes trabajen in-place sin reasignar.**
3. **Escritura en un único escritor experimental:** preparar candidato separado; validar etiquetas, unidades, dimensiones, finitud, positividad, ocupación y balance de entradas/salidas para **todos los niveles**; publicar el bloque completo en el buffer existente mediante `np.copyto`. El hash del owner no cambia si se rechaza el candidato. El costo de validar y copiar se medirá a tamaños reales antes de uso.
4. **Reemplazo y restauración:** cualquier sustitución de variable o carga NetCDF **requiere rebinding explícito** de vistas y verificación de alias. No confiar en referencias a arrays obsoletos.
5. **Persistencia:** NetCDF válido para datos de inventario, metadatos y escalas del laboratorio; la serialización de instancias de solvers y reloj debe evaluarse por separado. Nunca cargar pickle externo.
6. **Limitación categórica:** `numpy.copyto` no es transacción atómica multiproceso ni protege de lectores durante escritura. Concurrency y gestión de acceso requieren diseño separado si se adoptan procesos simultáneos; ninguna garantía inventada.

## Pendiente de etapa 1 / puerta siguiente
**Etapa 1 continúa ABIERTA** porque aún no se decidió si el mundo requiere celdas volumétricas, partículas, mallas irregulares o una combinación; no se representaron fuerzas de contacto, apilamiento 3D, mezclas reales ni energía. Son decisiones de modelo y escala, no fallos de H1–H3.

**Próximo paso de alto valor:** antes de añadir nuevos solvers, verificar los requerimientos que distinguen realmente 2D/capas de volumen físico —cavidades, puentes/voladizos, erosión local tridimensional, estructuras durables— y comparar los formatos/motores existentes. Solo construir una prueba mínima si esos requisitos hacen que la elección de representación cambie; el prototipo actual NO tiene licencia para crecer por inercia.

## Gatillos de revisión
- Un solver Landlab recrea su campo y rompe la vista; un acoplamiento sin historial de unidades pierde masa; concurrencia exige aislamiento; necesidades tridimensionales superan el esquema de capas; Pandera deja de ser compatible o costea demasiado; BMI o un motor existente aporta interfaz más segura.
- En ese caso actualizar este ADR, conservar el baseline y volver al criterio de soluciones existentes antes de nueva física.

**No usar esta decisión experimental como autorización para crear un motor nuevo o fusionar código con `main`.**
