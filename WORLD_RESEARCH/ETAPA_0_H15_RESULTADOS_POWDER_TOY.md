# Etapa 0 — H15: The Powder Toy material headless, revisión crítica completa

Fecha 2026-11-21. **Estado:** prueba H15 ACEPTADA en caída, barrera y replay. NO aprobado como núcleo del mundo ni como modelo de materiales abiertos.
Plan preregistrado: `ETAPA_0_H15_PROTOCOLO_POWDER_TOY.md`.
Fuente oficial GPL-3: https://github.com/The-Powder-Toy/The-Powder-Toy ; SHA upstream fijado por CI de primera compilación `44dd77e36084215021cea16dea3e1a49ac53fe94`. Versionado del upstream verificado por `git clone` con hash visible.

## Procedimiento
- GitHub Actions en Ubuntu 24.04, build Meson `-Dstatic=prebuilt -Dbuild_powder=false -Dbuild_render=true -Dhttp=false -Dlua=none`, renderer-only **sin GUI**.
- Instrumentación pequeña de `src/PowderToyRenderer.cpp` **solo en checkout temporal**; llama APIs nativas `Simulation::Factory`, `create_part`, `BeforeSim(true)`, `UpdateParticles(0,NPART)`, `AfterSim`. No se copió código GPL-3 a nuestro repositorio ni se publicó derivado binario.
- 15 cuadros con `PT_DUST` en x=XRES/2, y=YRES/3=128, RNG 7321. Escenario sin obstáculo y repetición fija.
- Control de bloqueo con `PT_DMND` horizontal de 101 px en y=131, interior al recorrido libre observado. Criterio: libre debe cruzar y=131, bloqueada debe permanecer por encima, y ambas mantienen tipo de partícula.

## Secuencia de auditoría
1. Primera compilación H15.1 falló en nuestra sonda por carecer de `#include "simulation/ElementClasses.h"`; libsimulation y 259/260 tareas compilaron. No confundir con defecto upstream. https://github.com/mxlzz/Nilo_public/actions/runs/44957866318
2. Segunda CI H15.2 pasó asserts, con libre y=134 y barrera situada en y=140; bloqueada y=134, de modo que **NUNCA alcanzó la pared**. Se detectó **falso positivo del diseño experimental**; su resultado NO prueba colisión, aunque sí caída y replay. https://github.com/mxlzz/Nilo_public/actions/runs/44958070491
3. Se preregistró enmienda para poner barrera en y=131 y exigir atravesar esa coordenada en el control libre y no atravesarla en el intervenido. **Tercera CI validada:** https://github.com/mxlzz/Nilo_public/actions/runs/44958258840 (**SUCCESS**).
   - polvo Y inicial **128**, Y libre final **134**; x libre **306**.
   - pared Y **131**; polvo bloqueado Y final **130**, x **306**.
   - polvo mantuvo tipo y hay un polvo en ambas escenas. `seeded_replay_equal=true`. 15 frames ejecutados.
- La corrección del arnés no modificó la física original; ambos fallos previos conservados.

## Interpretación
- **Demostrado** que el ejecutable renderer de TPT puede compilarse y exponer el núcleo de la simulación sin GUI, y que arena/polvo cae, es bloqueado y es reproducible bajo nuestro escenario.
- **No demostrado:** un protocolo público de motor incrustable sin instrumentación, materiales abiertos definidos por propiedades, balance de masa/energía de reacciones, integración con Landlab, altitudes geológicas en m, evolución ecológica real o comportamiento comparable a un mundo 3D.
- **Fricción**: proyecto C++20 grande, dependencias Meson/prebuilt, licencia GPL-3 frente a otras partes MIT; las combinaciones de licencia deben analizarse antes de distribución de código derivado. Sandspiel (MIT) tiene reglas más acotadas e inicialización de viento anómala en uso headless; TPT tiene catálogos de elementos rígidos y API de simulación interna accesible en checkout temporal. Ambos son motores de materia local 2D, no sustitutos de un solver ecohidrológico.

## Dictamen del gate
**H15 ACEPTADA como segundo candidato material ejecutado.** No recomendar **ninguno** como motor ambiental principal únicamente a partir de 15 ticks. Mantener ambos como referencias de modelo de materiales locales. Etapa 0 abierta mientras faltan benchmark funcional Ecosystem Explorer, prueba mínima de autoorganización y decisión de encaje del sustrato híbrido.
