# ADR-0012 — E3, segregar componentes mediante Cahn–Hilliard ya implementado en FiPy

**2026-11-22. Estado: ensayo H21 REVERSIBLE, NO adopción de física definitiva.**

## Requerimiento y evidencia

Etapa3 del [plan](../BASES_Y_HOJA_DE_RUTA.md): «patrones estructurales persistentes sin plantillas», cuya formación dependa de leyes y pueda distinguirse de distribución inicial y azar condicionado. **H19 falló**: los 50 nodos de deposición de H9 eran una componente conectada explicable por un nulo que preserva la topografía por filas ([resultado](../ETAPA_3_H19_RESULTADOS_DEPOSITO_CONEXO.md)). **H20A** confirmó [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45060886245) que pyDeltaRCM genera morfología reproducible, pero upstream advierte falta de conservación estricta de agua/sedimentos; por lo tanto queda **solo como referencia externa, no motor material**.

## Alternativa mejor reutilizable

El proyecto [FiPy4.0.3 de NIST](https://github.com/usnistgov/fipy/tree/4.0.3/examples/cahnHilliard) ya incluye el ejemplo **`examples/cahnHilliard/mesh2D.py`** de descomposición espinodal. Su ecuación Cahn–Hilliard es evolución difusiva conservativa de una fracción `phi` con energía libre de doble pozo y penalización de gradientes. Su documentación describe exactamente cómo pequeñas fluctuaciones aleatorias de una mezcla de composición `phi≈0.5` producen dominios segregados, sin necesidad de semillas/figuras prescritas. Los términos físicos, su discretización y solver 4º orden ya están implementados por FiPy; no programar nuevo integrador.

**Comparación de opciones:** Landlab+SPACE necesita una cuenca/forzante con patrón inicial y falló H19 frente a nulo; pyDeltaRCM más especializado en delta pero no estrictamente conservativo; MPM/GeoTaichi tiene problemas abiertos de suelo/clamp e import; FiPy ya se instaló para H14–H16, tiene API headless, permite 2D sin cambios de engine, y comparte `xarray` como owner. **Escoger Cahn–Hilliard como ensayo material nuevo, no reemplazar mecanísticamente erosión/gravedad.**

## Alcance y riesgo intelectual

**Material abstracto A/B en una capa 2D.** Cada celda tiene masa total constante, fracciones A/B pueden variar de forma difusiva; celdas pueden contener ambas especies (algo que H16 prohibía solo por su modelo térmico idealizado, no como ley universal). El efecto puede generar dominios de composición separados a partir de ruido, un tipo de organización diferente a la ramificación fluvial. No representa geología, roca/agua específicos ni formación de techos, cavidades o estructuras mecánicas. `phi` es composición **derivada** de masas canónicas; la energía libre es funcional del modelo, no un nuevo inventario de calor.

La prueba no podrá declarar «emergencia» solo por ver manchas: exigirá (a) conservación de masas A/B globales, (b) aumento de segregación frente al inicial, (c) organización espacial frente a nulos **condicionados por fila**, (d) persistencia entre dos momentos posteriores, (e) controles de movilidad y composición estable, (f) replay/NetCDF exacto, todo [preregistrado en H21](../ETAPA_3_H21_PROTOCOLO_CAHN_HILLIARD.md).

**Stop/go:** Si la implementación 2D no supera gates, registrar H21 no aprobada y no corregir física a posteriori. Si los pasa, **no cerrar automáticamente etapa3** sin auditar causalidad, sensibilidad de semillas/ruido y la duración de los dominios; no atribuir funciones espaciales de escala macroscópica a un patrón de composición.
