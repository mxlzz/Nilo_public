# Etapa 1 — H14. Conducción de calor conservativa entre regiones de materia

**2026-11-22. PROTOCOLO ANTES DE CÓDIGO.** Esta prueba se justifica por el apartado 5 y la etapa 1 de `BASES_Y_HOJA_DE_RUTA.md` (energía y transformaciones trazables). No implementa motores propios ni amplía 3D/GeoTaichi; mantiene el mundo aislado. **Etapa 1 continúa ABIERTA**.

## Pregunta física e hipótesis

¿Puede un componente ya existente redistribuir **energía térmica** entre regiones contiguas, con materia fija y un único inventario energético, sin crear calor ni mover masa? Es la capacidad material básica aún no comprobada, más necesaria para el objetivo que depurar una tercera dependencia de GeoTaichi. El resultado es falsable ante gradiente nulo, conductividad nula o balance roto.

**Reutilización:** **FiPy** del NIST, biblioteca Python de volumen finito con `TransientTerm` y `DiffusionTerm`, fronteras sin flujo por omisión, licencia verificable en upstream. Documentación https://pages.nist.gov/fipy/en/latest/USAGE.html y https://pages.nist.gov/fipy/en/latest/generated/examples.diffusion.mesh1D.html; no copiar sus ecuaciones.

## Modelo mínimo y unidades

- Caja unidimensional cerrada 8 celdas de volumen 1m³/área de frontera 1m², `dx=1m`. Todas contienen **2kg material A**, con `cp=500 J/(kg K)` ficticio pero dimensionalmente coherente; en cada celda `rho*cp=1000 J/(m³K)`. No hay movimiento ni transformación de materia.
- `xarray.Dataset` guarda dos variables autoritativas: `material_mass_kg(cell)` e `internal_thermal_energy_J(cell)`, con cp como parámetro estable en attrs. **Temperatura K se DERIVA** por `T=E/(m cp)`, no se almacena como stock duplicado. Fuente térmica externa y sumidero exterior nulos. El modo térmico de FiPy es un cálculo derivado temporal de esas energías; al final de cada paso se valida el candidato antes de publicar.
- Energía inicial en 4 celdas izquierdas `330000J` c/u (330K), en 4 derechas `270000J` c/u (270K). Total **2.400.000J** y materia **16kg**, por regla fija.
- Solver FiPy con `TransientTerm(coeff=1000) == DiffusionTerm(coeff=20)` en unidades SI y default no-flux; 100 pasos de `dt=0.1s`. Control con `k=0` y otra escena con temperatura uniforme300K y k20. FiPy determina flujo, no el arnés.
- La **temperatura absoluta se expresa en K**, no grados Celsius ni potencia. No hay calor latente, radiación, contacto con aire ni fuente.

## Criterios definidos antes de ejecutar

1. **Conservación:** durante cada paso, `sum(E)` cambia como máximo `0.01J` absoluto respecto2.400.000J, sin ningún término fuente ni sumidero; `sum(m)` siempre exactamente16kg. Ningún `E` negativo, nan o unidad equivocada. FiPy no debe almacenar un segundo inventario.
2. **Conducción activa:** temperatura de celda caliente junto a interfaz (índice3) baja `>0.1K`, la vecina fría (índice4) sube `>0.1K`, ambas siguen entre270 y330K, y amplitud térmica final estrictamente menor que60K. El efecto responde al gradiente, no a un ajuste arbitrario.
3. **Ablaciones:** `k=0` conserva cada energía celular dentro de `1e-7J`; estado inicialmente uniforme con k20 también permanece constante dentro de `1e-7J`. No sustituir controles que no pasan por un flujo de compensación.
4. **Integridad transaccional:** corrupción de una unidad J→kJ, energía negativa, materia negativa, alta de 1J sin fuente o cambio de cp deben rechazarse antes de publicar y dejar el owner original inalterado. Catálogo de propiedades reducido a las imprescindibles.
5. **Repetibilidad/persistencia:** segunda corrida activa con las mismas entradas reproduce exactamente las 8 energías finales; snapshot NetCDF de owner preserva masa, energía, cp, unidades y hash exactos. No almacenar temperaturas como material duplicado.
6. **Gate:** **APROBAR H14** solo con todos los puntos anteriores, con `WORLD_EVAL_JSON` que incluya versión FiPy/NumPy/xarray y salida del balance. Si fallan imports o conservación, registrar fallo y detener para diagnóstico, sin alterar umbrales retrospectivamente.

## Limitaciones explícitas

Un experimento 1D con cp y conductividad constantes no prueba física térmica 3D, mezclas, cambios de fase, calor producido en fricción, ni temperaturas naturales. El flujo de calor es **ley conocida ejecutada por FiPy**, no comportamiento emergente novedoso. No completa automáticamente etapa1 ni inicia etapas2–8. No introducir campo energético en H5/ROI sin demostrar necesidad e interoperabilidad posterior.

**Revisión de alternativas:** resolver por FiPy antes que implementar diferencias finitas propias; evitar bibliotecas geomecánicas para una ecuación térmica; no importar grafismo ni motores 3D. Condiciones y unidades siguen el modelo de difusión documentado por FiPy.
