# Etapa 0 — H15: segunda base material, The Powder Toy frente a Sandspiel

Fecha: 2026-11-21 · **Estado: protocolo previo a compilación y experimento**. Documento rector: `BASES_Y_HOJA_DE_RUTA.md` (etapa 0), `PROCEDIMIENTO_Y_AUDITORIA.md`, ADR-0001. Este es un ensayo de *comparación de soluciones existentes*; no se desarrollará otro motor físico.

## Por qué
El benchmark de Sandspiel (CI https://github.com/mxlzz/Nilo_public/actions/runs/44944136887) probó caída de una partícula, barrera e igualdad entre ejecuciones, con inicialización de viento neutral. Falta el segundo candidato material, según el plan; no corresponde continuar experimentos hidrológicos sin cerrar esta puerta.

## Fuente y condiciones de uso
- Upstream `https://github.com/The-Powder-Toy/The-Powder-Toy`, GPL-3.0; uso de una copia temporal de Git para evaluación, sin copiar/republicar el motor en nuestro repositorio. Se registrará el SHA upstream. No asumir compatibilidad GPL con un motor futuro de licencia diferente.
- Los archivos `src/simulation/Simulation.h` y `Simulation.cpp` exponen `create_part`, `BeforeSim`, `UpdateParticles`, `AfterSim`, `Save`/`Load`. El renderizador independiente `src/PowderToyRenderer.cpp` ya construye `SimulationData` y `Simulation` sin GUI; `meson_options.txt` permite `-Dbuild_powder=false -Dbuild_render=true`.
- Construir el ejecutable upstream del renderizador en GitHub Actions Linux, sin ninguna modificación persistente en upstream ni en nuestro main; se permite inyectar un pequeño **harness** en el checkout efímero antes de compilar el renderer para exponer `Simulation::Factory` y llamar sus APIs.
- Preferir dependencia `-Dstatic=prebuilt` upstream (si se puede descargar); no copiar binarios, plugins o artefactos de terceros al repositorio.

## Pruebas diseñadas ANTES del código
1. **Baseline físico:** generar partícula `PT_DUST` en posición `(XRES/2,YRES/3)` (en motor upstream, con semilla RNG 7321); 15 cuadros con `BeforeSim(true)`, `UpdateParticles(0,NPART)`, `AfterSim()`. Probar que mantiene tipo y que su Y aumenta (coordenadas de pantalla; caída).
2. **Barrera:** repetir desde idéntica semilla, creando barrera horizontal de `PT_DMND` de ancho ≥101 px en `y0+12`; después de 15 pasos la partícula no debería atravesar la barrera. Si el movimiento lateral se dispersa más de lo supuesto, registrar trayecto en vez de ampliar barrera ad hoc sin documentar.
3. **Repetibilidad:** dos mundos independientes con semilla RNG 7321 y condiciones iniciales idénticas deben producir tipo, Y y X iguales al final de 15 pasos.
4. **Estado válido:** `currentTick=15`, partículas activas con índices válidos, sin crash, resultado JSON de variables y versión/commit. Al fallar alguna regla, no cambiar criterio silenciosamente.
5. **Integración/costo:** medir si se logra compilar TPT renderer upstream y duración del experimento. Si no compila, registrar error exacto y *no afirmar* que el motor no puede producir caída; reevaluar condiciones de build y costo de dependencias.

## Criterio
H15 aceptada como segunda prueba ejecutada de un motor material **si** el ejecutable se compila y cumple caída, barrera y replay. Aún no demuestra materiales definibles por propiedades, evolución abierta, conservación multi-especie, integración con Landlab o APIs públicas de embedding. Se preserva Sandspiel como baseline y Ecosystem Explorer como benchmark funcional distinto (caja negra). El gate de etapa 0 sigue abierto hasta auditar también esos aspectos.

## Riesgos/costos a medir
- Potencialmente cientos de unidades C++20 + librerías pesadas, GPL-3, renderer diseñado para miniaturas, simulación estructurada en elementos enumerados (`PT_NUM`), posible ausencia de API pública simple. Puede ser una referencia de materia local sin ser apropiado como núcleo principal del mundo 3D/ambiental.

## Fallo instrumental H15.1 detectado y registrado antes de corregir
CI inicial https://github.com/mxlzz/Nilo_public/actions/runs/44957866318 (**FAIL**). Meson consiguió resolver dependencias y compilar **259 de 260 tareas** del renderer, por lo que el núcleo upstream se compiló casi completamente, incluyendo `libsimulation.a` y `libcommon.a`. El único fallo fue en el **arnés de prueba**, que referenciaba `PT_DUST` y `PT_DMND` sin incluir `simulation/ElementClasses.h` (donde se definen las constantes a partir del `ElementNumbers.h` generado por Meson). El error en `Result` dependía de esos identificadores ausentes. **No es un defecto de TPT**, ni una falla de su física.
**Corrección acotada:** agregar solo `#include "simulation/ElementClasses.h"` a la fuente temporal de instrumentación. No alterar 15 pasos, misma semilla, ley física, barrera, ni criterios. Si el ensayo arranca pero falla caída/bloqueo, registrar el comportamiento físico sin retocar umbrales.
