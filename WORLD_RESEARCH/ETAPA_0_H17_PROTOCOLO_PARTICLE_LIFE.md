# Etapa 0 — H17: ¿hay organización local no prediseñada en motores existentes?

**Fecha:** 2026-11-21. **Estado:** preregistro anterior a experimento. Requisito 3B confirmado y `BASES_Y_HOJA_DE_RUTA.md` etapa 0. **Esta prueba NO propone un núcleo nuevo ni modifica leyes del mundo propio.**

## Fuente reutilizable
`https://github.com/hunar4321/particle-life` (MIT; código Python original `particle_life.py`, 2024) simula un conjunto de partículas con interacción de alcance local y fuerzas de atracción/repulsión según grupo. El código usa pygame para visualización, pero las reglas de fuerza no dependen de la visualización. La fuente **no** implementa física de suelo, volumen, conservación termodinámica ni organismos; es un laboratorio de patrones por reglas, precisamente una línea de referencia del corpus de 42 alternativas.

## H17 — prueba de una capacidad, sin atribuir vida
**Hipótesis:** con la misma posición inicial de 100 partículas amarillas y 100 rojas (seed Python `7321`), conservar la fuerza de **autoatracción amarilla** `g=-0.1` del código upstream produce mayor proximidad espacial de las amarillas después de **80 frames** que poner *solo ese parámetro* a `g=0`. Este contraste permite atribuir cierta agregación a interacción local y no a una plantilla de agrupación dibujada.

**Instrumentación del código upstream solo en checkout efímero**:
- Ejecutar `particle_life.py` con `SDL_VIDEODRIVER=dummy`, pygame instalado; añadir seed fija antes de llamar `create` y detener bucle en 80 cuadros, imprimir JSON con métricas y hash de posiciones. No copiar el archivo original a nuestro repositorio.
- Variar únicamente el argumento de `rule(yellow,yellow,-0.1)` mediante variable de ambiente `H17_YELLOW_SELF_G` con valores -0.1 (original) y 0.0 (ablación). Resto de reglas intactas, mismos 80 cuadros.
- Tres corridas independientes (baseline, control sin autoatracción, replay baseline) deben partir del **mismo hash de posiciones iniciales**.
- Medir (a) distancia media al vecino amarillo más cercano; (b) cantidad de pares amarillos a menos de 8 px; (c) porcentaje de partículas con coordenadas finitas; (d) hash final de todas las posiciones. Definir distancia euclídea directa en el mismo espacio que el original, sin modificar su física.
- **Criterio H17:** hash inicial igual, baseline final igual bit a bit, estados finitos y cuenta de átomos constante; distancia media al vecino menor en baseline que en ablación, y mayor número de pares próximos en baseline; si alguna magnitud no muestra esa dirección, **hipótesis no demostrada** (no retocar seeds o frames a posteriori para aprobar), conservar resultado y evaluar mecanismos alternativos existentes.
- No pretender que proximidad implica un organismo nuevo, organismo vivo, masa conservada en términos físicos, autoorganización abierta, estabilidad a largo plazo ni patrón que sobreviva perturbaciones.

## Gates
H17 puede fundamentar un experimento específico de organizaciones no predefinidas en futuras etapas, pero **no sustituye un núcleo ambiental** ni requiere incluir un motor de partículas en etapa 1. Ponderar su costo/licencia con Sandspiel/TPT, Landlab y Ecosystem Explorer. Etapa 0 sigue abierta hasta decisión auditable.
