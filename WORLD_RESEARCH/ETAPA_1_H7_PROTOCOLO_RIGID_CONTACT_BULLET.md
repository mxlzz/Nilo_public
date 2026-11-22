# Etapa 1 — H7. Preparación de la primera interacción mecánica con motor EXISTENTE

**Fecha:** 2026-11-22. **Estado:** PROTOCOLO PREREGISTRADO antes de programar. Etapa 1 **ABIERTA**; pruebas de E2 solo como selección de proveedor de física, sin declarar cerrada etapa 1 ni empezar un motor nuevo. Objetivo y procedimiento: `BASES_Y_HOJA_DE_RUTA.md`, `PROCEDIMIENTO_Y_AUDITORIA.md` y `DECISIONES/ADR-0005_REPRESENTACION_ESPACIAL_HIBRIDA.md`.

## Pregunta científica y por qué importa
Los ensayos H1–H6 conservaron representación de masa, material, cavidades, superficies y regiones volumétricas, pero **ninguna materia se movió ni tuvo soporte por una ley de mecánica**. Para avanzar hacia dinámica autónoma hace falta comprobar que un solver existente recibe cantidades desde el owner material y devuelve estado cinemático sin inventar materia o mezclar la propiedad de variables.

Una **interacción de contacto de cuerpo rígido** no es una prueba de fluido ni arena, y un cubo rígido no constituye organización emergente. Se busca solo disminuir incertidumbre de integración antes de seleccionar material mechanics para etapas 2/3.

## Alternativas revisadas y rechazo de reinventar
- **Bullet / PyBullet** https://github.com/bulletphysics/bullet3 , licencia zlib (excepto archivos de terceros indicados): física y contacto rígido 3D con modo `DIRECT`; ejemplo y manual upstream https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstart_guide/PyBulletQuickstartGuide.md.html . **Elección para este ensayo**: API Python simple, modo sin UI, objeto cubo en metros con masa explícita, contacto consultable, sin escribir integrador propio.
- **The Powder Toy** (GPL3): prueba H15 ya confirmó caída y bloqueo de partícula 2D https://github.com/mxlzz/Nilo_public/actions/runs/44958258840 ; excelente comparación para granularidad, pero sus píxeles/elementos no están en metros ni resuelve mecánica rígida volumétrica general como el caso actual.
- **Sandspiel** (MIT): prueba 2D de granos/paredes, sin cuerpos rígidos 3D. No repetir H15 ni convertir arena a rígidos.
- **Taichi/GeoTaichi**: permiten simulación granular o MPM 3D, pero introducen infraestructura de GPU/solvers y complejidad mayor para una sola caja con gravedad. Conservar como candidatos si aparece requisito de deformación, sedimento o agregación.
- **MuJoCo** Apache-2.0 https://github.com/google-deepmind/mujoco alternativa con contacto rígido 3D, más preparación XML/configuración de modelos en este caso pequeño. No hay razón verificada para reemplazar Bullet en este primer control.
- **Estado de materiales:** xarray+NumPy ya validados para inventario H1–H6. `pybullet` 3.2.7 dispone de wheels oficiales CPython hasta 3.11 para Linux en PyPI (según catálogo al 22-11-2026) y se solicitaron wheels 3.12+ en https://github.com/bulletphysics/bullet3/issues/4789. Usar **Python 3.11 aislado** en CI y registrar versión/ABI; no declarar compatibilidad 3.13 no probada.

## Hipótesis H7 falsable
Un cuerpo cúbico de lado **1.0m** y masa **2.0kg** proveniente de un inventario `xarray.Dataset` con composición A (densidad 2kg/m³) caerá bajo gravedad `g=-9.81m/s²` y se apoyará sobre una frontera plana rígida fija (sin material modelado). **Las posiciones y contactos los calcula Bullet; el arnés no debe escribir una ley de fuerza o movimiento.**

## Estado y propiedad de variables
- `xarray.Dataset` es el **owner de cantidad material, identidad, volumen geométrico y densidad derivada**. Solo 1 cuerpo material A, masa2kg, volumen1m³, densidad calculada2kg/m³. El piso de prueba es una **condición de borde cinemática geométrica sin inventario material**; su masa estática en Bullet es cero. No proclamar conservación de materia del mundo real si se quisiera contar el suelo como sustancia.
- PyBullet recibe masa y geometría desde el dataset; internamente mantiene una copia de parámetros de fuerza/cuerpo como cualquier solver, pero **no es una segunda autoridad de inventario**. Requerir la misma masa en la consulta `getDynamicsInfo` y no recalcular el inventario global sumando `getDynamicsInfo`. Si el ensayo encontrara una diferencia de masa, informar fallo de intercambio.
- Las posiciones/velocidades de PyBullet son el **owner cinemático del ensayo** mientras avanza. Se registran observaciones temporales `(time,z,vz)` en xarray (lectura, no segundo integrador). No se actualizan voxeles discretos, porque mapear un sólido rígido rotado a celdas discretas requiere otro contrato aún no ensayado.

## Experimentos prefijados y criterios, antes del arnés
Cada ejecución en DIRECT, dt=1/240s, 480 pasos (=2s), shape GEOM_BOX mitad[.5,.5,.5] y altura central inicial 3m, sin velocidad inicial. Tres escenarios:

1. **Con gravedad y piso** (plano z=0). Predicción: z final del centro entre **0.45 y 0.60m**, descenso >2m, contacto cubo↔piso `getContactPoints` positivo al finalizar, velocidad vertical absoluta <0.1m/s. El cuerpo debe tener masa Bullet2kg y masa del owner2kg al final; el piso es límite rígido fijo, sin inventario de material.
2. **Gravedad anulada con el mismo piso**: z final igual a inicial dentro de **1e-9m**, sin contactos, velocidad vertical0 dentro de tolerancia.
3. **Gravedad activa sin piso**: z final < **-10m** (tras 2s, caída ideal aprox. 19.6m sin resistencia, menos amortiguación interna), sin contactos de piso. No debe inventarse una ley de freno por debajo del plano ausente.
4. **Replay** completo del escenario con gravedad+piso en una segunda instancia `DIRECT` con los mismos parámetros y pasos: posiciones/velocidades observadas iguales byte a byte dentro del mismo runner/versión, así como contacto final. Si no lo son, registrar desviación, no inventar causalidad ni reducir controles.
5. **Prueba de contrato**: antes de crear Bullet, rechazar mediante validador externo una masa negativa, densidad inválida y dos materiales que exceden capacidad de volumen; usar solamente campos xarray/NumPy, no un nuevo motor de validación. Comprobar que el estado válido no cambia durante una corrida y roundtrip de datos NetCDF recupera valores/unidades. La energía térmica **no** se almacena: este caso no resuelve disipación a calor; no declarar la etapa 1 completada bajo el apartado energía.
6. **Rendimiento informativo**: medir tiempo de 480 steps, versión Bullet y Python; no inferir rendimiento de mundo volumétrico o configuraciones emergentes.

## Gate después de ejecución
**Aprobación H7** solo si todos los casos/corrupciones y replay cumplen los criterios predefinidos. Significa **que un solver rígido existente puede tomar masa/composición declaradas y resolver gravedad/contacto con observación sin inventar fuerzas**. NO significa que Bullet soporte cavidades de material granular deformable, que sea adecuado para celdas individuales a escala de territorio, que dé emergencia o masa/energía global conservadas, ni que sea motor definitivo.

**Si falla por instalación**: documentar wheel/runtime y elegir alternativa o versión de Python compatible, sin diagnosticar física inexistente. **Si falla numéricamente**: conservar logs, comparar posición/tiempo y no alterar tolerancias sin registrarlo. No modificar main ni NeuroLab.
