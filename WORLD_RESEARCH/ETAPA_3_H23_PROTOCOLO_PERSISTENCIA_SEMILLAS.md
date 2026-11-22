# Etapa 3 — H23. Prerregistro de persistencia tardía y semillas independientes

**Fecha 2026-11-22 — registrado antes de escribir arnés/CI.** La [H22](ETAPA_3_H22_RESULTADOS_ESCALA_INTERFAZ.md) mostró segregación medible causada por `epsilon=0,5` (varianza ~1273 veces mayor que con epsilon1), conservando A/B, pero **NO aprobó** el umbral de estructura por filas (+0,08) ni Jaccard de pasos300/400 (0,578<0,60). H21/H22 permanecen intactas y no se «recuperan» a posteriori. Este diseño responde directamente a [Etapa3](BASES_Y_HOJA_DE_RUTA.md): patrones medibles entre condiciones iniciales, conectividad, tamaño, estabilidad, nulos y ablaciones.

## Pregunta falsable

¿La dinámica **ya segregadora** del modelo existente de FiPy Cahn–Hilliard a epsilon0,5 desarrolla durante una continuación temporal **dominios persistentes** que superan un nulo de estructura condicionada por fila, en más de una semilla independiente? Alternativa: el proceso continúa coarsening y los dominios no persisten a la escala temporal evaluada; las morfologías difieren pero los nulos por fila las explican; o hay sobreimpulsos/errores de masa.

No probar nuevos epsilon, tamaños de malla ni variantes de PDE. Se reutiliza la misma ecuación NIST4.0.3 y owner xarray del H21; **no** se implementan integrador ni física nueva.

## Diseño fijo previo

- **Modelo:** `Grid2D(nx=20,ny=20,dx=dy=0.25)`; `D=a=1`, `epsilon=0.5`, `TransientTerm()==DiffusionTerm(coeff=(1-6PHI(1-PHI)))-DiffusionTerm(coeff=(1,0.5²))`, FiPy `DefaultSolver`; Neumann sin flujo. Total400kg con1kg/celda, especie A `phi`, B `1-phi` derivadas de stocks, sin tercer owner, sin movilidad ni fase adicional. Condiciones iniciales `phi=0.5+U(-0.07,+0.07)` muestreadas **independientemente** con `np.random.default_rng` seeds **20261122, 20261123, 20261124**.
- **Tiempo:** 600 pasos físicos (no cronología geológica) con **el mismo calendario de H21/H22** `dt=min(100, exp(-5+0.01*i))`, `i=0..599`; tomar máscaras de concentración `phi>0.5` a **pasos500 y600**, sin elegir ventana posterior por las observaciones. Control `D=0` de seed20261122 hasta600; replay completo seed20261122 `D=1`.
- **Controles espaciales:** por cada seed al paso600 construir 512 nulos aleatorios `rng(20261123)` que preserven **exactamente el número de celdas con `phi>0.5` por fila**; mismo `same-edge score` de H21/H22, percentil95 con `method='higher'`.
- Registrar media, varianza, q05/q95, componentes de cuatro vecinos y mayor componente, Jaccard de paso500→600, score espacial y su diferencia frente P95 condicionado, cambios de máscara entre semillas, masa, NetCDF y hashes.

## Gates de H23

1. **Integridad de todos los casos:** en cada paso masa global A y B respecto a su propia semilla <1e-4kg, total400kg a tolerancia1e-9kg, masa por celda 1kg ±1e-12, `0<=phi<=1` (rechazar y no aplicar clipping si se viola), dimensiones/unidades/ids; sin inventarios duplicados. `D=0` permanece bit a bit sin cambio de composición hasta600.
2. **Segregación robusta:** las **tres semillas** deben tener `q05<0.30`, `q95>0.70` y varianza al paso600 >2×varianza inicial. Es un gate separado de conectividad/persistencia.
3. **Organización frente a nulo condicionado:** en **al menos2 de las3 semillas**, `same-edge-score_observado > P95_row_null+0.08`. No reemplazar el nulo condicionado con uno global; mantener el margen de H22 sin rebajarlo.
4. **Persistencia temporal:** en **al menos2 de3 semillas**, Jaccard de máscaras500→600 ≥0,60. Se exige además que **al menos2 semillas** pasen **ambos criterios3 y4 simultáneamente**, no sumar éxitos aislados de distintas semillas.
5. **Dependencia causal de condiciones iniciales:** para al menos un par entre las 3 semillas, diferencia (Hamming) de etiquetas A/B en paso600 ≥0,10 de las400 celdas, sin otra variación en física o dominio. Esto verifica diversidad reproducible, no «emergencia abierta».
6. **Reproducibilidad y antifraude:** seed20261122 se repite y produce estados A/B y máscaras paso500/600 bit a bit iguales; recuperar owner final NetCDF con hash e inventarios exactos; volver a rechazar las **siete corrupciones** del H21 sobre estado final; reportar dimensiones y versiones del proveedor.
7. **Criterio temporal no manipulable:** no ejecutar 700/800 pasos para «buscar cuándo pasa» dentro de H23 ni cambiar semillas, ventanas, proporción de éxitos, estadístico, epsilon o umbrales tras ver resultados. Se guardarán outputs incluso con FAIL. Si se detecta inestabilidad numérica, documentar el paso y detener sin corrección silenciosa.

## Decisión permitida

**H23 aprobada solo** si se cumplen todos los gates1–6; no transforma por sí sola una fase ideal 2D en roca, cuevas, agregados mecánicos o mundo persistente, ni cierra automáticamente Etapa3. Si fracasa, la **persistencia de patrones del mecanismo** sigue sin demostrarse; evaluar retorno científico de otra iteración antes de gastar tiempo en parámetros. Fuente física [FiPy ejemplo oficial Cahn–Hilliard](https://pages.nist.gov/fipy/en/stable/generated/examples.cahnHilliard.mesh2D.html). Conservar GitHub como fuente de hechos y Notion como índice; main y NeuroLab intactos.
