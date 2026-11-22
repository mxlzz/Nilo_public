# Etapa3 — H21. Preregistro de segregación Cahn–Hilliard 2D con owner A/B y controles espaciales

**2026-11-22. ESTADO: PROTOCOLO ANTES DE CÓDIGO/CI.** [ADR-0012](DECISIONES/ADR-0012_CAHN_HILLIARD_E3.md); [etapa3 plan rector](BASES_Y_HOJA_DE_RUTA.md). Se usa **sin cambio de fórmulas** el ejemplo `examples/cahnHilliard/mesh2D.py` de [FiPy4.0.3](https://github.com/usnistgov/fipy/blob/4.0.3/examples/cahnHilliard/mesh2D.py), descomposición espinodal conservativa. NINGÚN solver nuevo, motor de mundo ni estructuras prefabricadas.

## Hipótesis y falsación

En una mezcla A/B casi uniforme (50%/50%) con fluctuaciones espaciales pequeñas, las interacciones locales codificadas en la **energía libre de doble pozo** del modelo Cahn–Hilliard generan dominios segregados, conectados y que sobreviven durante una ventana temporal; el promedio global de A/B se mantiene por conservación. Si desaparece movilidad `D`, el patrón inicial no debe cambiar. Si la fracción media comienza cerca de0,1 (fuera de régimen espinodal de esta función libre), no debería aparecer segregación binodal fuerte con la misma perturbación. El patrón final debe superar un nulo que preserva fracción espacial por filas, evitando el falso positivo H19.

**Hipótesis alternativa válida:** el solver 2D no desarrolla dominios observables en el intervalo, tiene overshoot/conservación deficiente, o la organización no supera el nulo condicionado. El experimento en ese caso **NO aprueba H21**, sin ajustes retroactivos.

## Parámetros fijos y propiedad material

- Malla `Grid2D(nx=20,ny=20,dx=dy=0.25)`, pared no-flux por defecto. Cada celda representa una lámina con total **1kg de materia A+B**; total400kg. La fracción `phi=m_A/(m_A+m_B)` es DERIVADA, no stock adicional. Un único `xarray.Dataset` contiene `material_mass_kg(material,y,x)` y metadatos del escenario. FiPy solo recibe `phi` como variable temporal, resuelve el PDE y devuelve **candidato de masas A/B**, validado antes de publicar. No definir energía térmica; la energía libre es funcional termodinámico del modelo, no la misma variable de calor H16.
- Condición inicial idéntica entre replay, movilidad0 y caso activo: `phi0=0.5+u` donde `u~Uniform(-0.07,+0.07)` con `np.random.default_rng(20261122)` (400 muestras), sin clipping; valores 0.43–0.57. **Control mezcla fuera de spinodal:** `phi0=0.1+u` con **los mismos u**; valores 0.03–0.17. No dibujar regiones ni semillas espaciales de forma.
- Proveedor FiPy4.0.3 `TransientTerm == DiffusionTerm(coeff=D*a²*(1−6PHI(1−PHI))) − DiffusionTerm(coeff=(D,epsilon²))` y `PHI=phi.arithmeticFaceValue`, como ejemplo NIST, `a=epsilon=1`, `D=1` salvo control `D=0`. Parámetros adimensionales, sin calibración química de una sustancia natural.
- Simular **400 pasos** con `dt=min(100,exp(−5+0.01*i))` i=0..399, solver `DefaultSolver` nativo; observar inicio, paso300 y paso400. Escenarios activos, D0, composición media0.1 y replay del activo; mismos pasos.
- Medir campo continuo y máscara estructural `phi>0.5`, 4-conexidad con scipy.ndimage, Jaccard entre pasos300 y400, varianza y cuantiles finales. Semillas estocásticas solo en inicial y nulos.

## Gates preregistrados

1. **Mass owner:** cada paso matriz20×20 con `m_A+m_B=1kg/celda` a tolerancia1e-12kg, `m_A,m_B≥0`, sin NaN, identidad y unidades correctas. `sum_mA` y `sum_mB` cambian respecto a su inicio **menos de 1e-4kg absoluto** en cada paso, sin correcciones de balance ni clipping de phi. Nótese que `phi` no es material libre adicional.
2. **Segregación espontánea:** al paso400 caso activo `q95(phi)>0.70`, `q05(phi)<0.30` y `Var(phi_400)>2*Var(phi_0)`; se exige además al menos8 nodos de cada grupo en máscara `phi>0.5` / contrario.
3. **Nulo por filas:** calcular proporción de parejas adyacentes de 4 vecinos con misma etiqueta `phi>0.5`, sobre la máscara20×20. Generar **512 permutaciones** uniformes condicionadas por fila con mismos conteos de celdas de alta concentración por fila, RNG fijo20261123. Gate: coherencia espacial activa final `same_neighbor_fraction_obs > P95_row_null + 0.08`; percentil95 por `numpy.quantile(method='higher')`. Reportar también coherencia inicial; no sustituirlo por nulo global si falla.
4. **Persistencia temporal:** Jaccard de máscara activa entre paso300 y400 ≥0,60. Mide solo persistencia de dominio segregado a lo largo de ese intervalo, **no** estabilidad mecánica o cronología geológica.
5. **Ablaciones:** movilidad `D=0` produce cambio máximo `<1e-8` en `phi`; control mean0.1 no debe alcanzar separación fuerte (`max(phi)<0.30`) y su varianza al final debe ser `<1,5*var0`. Si el control estable se separa o D0 cambia, no afirmar mecanismo causal diferencial.
6. **Repetibilidad:** repetir activo con mismos parámetros da matrices de masa A/B y `phi` idénticas bit a bit en mismo entorno CPU. NetCDF de owner final restaura inventarios, nombres, unidades, atributos y hash exacto; 7 corrupciones rechazadas antes de commit sin tocar owner: materia creada, negativa, kg→g, material nuevo, variable `phi` duplicada como stock, coordenada adulterada y exceso de capacidad.
7. **No licencia de interpretar morfología como mundo:** si estos gates pasan, H21 prueba **solo** segregación conservativa 2D en un material binario ideal, sin generar geometría sólida, cavidades ni función ecológica. **Etapa3 seguirá ABIERTA hasta auditoría de suficientes mecanismos y estabilidad, y no se promueve ningún motor a main.**

## Registro y cierre

Todo en `WORLD_RESEARCH/experiments/probe_e3_h21_spinodal_fipy.py` y GitHub Actions Python3.11, FiPy4.0.3/NumPy/xarray/SciPy. Emitir `WORLD_EVAL_JSON` completo con gates y métricas antes de fallar; si una condición falla, CI no-cero, no reescribir umbrales ni ruido a posteriori. El modelo proviene del ejemplo público del NIST y se usan condiciones de laboratorio inventadas, **no** predicciones sobre sustancias reales.
