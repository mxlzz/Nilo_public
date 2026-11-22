# Auditoría formal de gate — Etapa2 («reglas locales de intercambio»)

**Fecha:** 2026-11-22. **Dictamen:** **CERRAR PROVISIONALMENTE el gate de dos interacciones locales aisladas**, no el de un motor ambiental integrado. Cumple los criterios expresos de E2 en [BASES_Y_HOJA_DE_RUTA.md](BASES_Y_HOJA_DE_RUTA.md) §6, conservando límites y CI. La etapa3 comienza **solo** con protocolo de formación/persistencia estructural.

## Objetivo y selección de fenómenos

La etapa2 pide «una o dos interacciones primero», antes de tener ríos, mundos gráficos u organismos. Se eligen estas **dos** por evidencia previa y brechas medidas:

- **Gravedad y apoyo rígido** [H17](ETAPA_2_H17_RESULTADOS_GRAVEDAD_OWNER.md): PyBullet3.2.7 computa descenso y contacto de un cuerpo A, validando y publicando la nueva posición/velocidad a xarray en tres escenarios; no copiar integrador.
- **Transporte sedimentario fluvial por pendiente** [H9](ETAPA_1_H9_RESULTADOS_SEDIMENTO_OWNER.md) y [H18](ETAPA_2_H18_RESULTADOS_GRADIENTE_SEDIMENTO.md): Landlab2.11 gobierna erosión, deposición y exportación, publica saldo a xarray, con diferencia experimental de pendiente y control K=0; no copiar ley de erosión.

**Calor/latente** [H14–H16](ETAPA_1_H16_RESULTADOS_DOS_MATERIALES.md) se cita **solo** para el subcriterio «si se simula energía, balance térmico», ya probado con FiPy4.0.3 en laboratorio material. No imponer un tercer motor simultáneo como condición de E2; el acoplamiento ambiental se exige recién en E5.

## Matriz de los cuatro criterios previos

**E2(a), caída cuando hay espacio, detenida por bloqueo:** H17 [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45059850320), A2kg bajó1,5000m libre y0,5000m frente a B8kg fijo apoyado, mientras g0 impidió el movimiento; contactos positivos asociados al soporte. Posición y velocidad finales publicadas y checkpoint exacto. **CUMPLIDO** para cuerpo rígido y obstáculo prescrito, sin campo deformable.

**E2(b), flujo de acuerdo con gradiente:** H18 [CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45060100229), misma masa+K+outlet con bedrock inclinación1,0 o0,5. Exportación 472.551→288.318kg (caída39%) y redistribución de masa en nodos interiores por solver. **CUMPLIDO** para sedimentación fluvial2,5D, no flujo volumétrico3D.

**E2(c), balances:** H17 mantuvo10kg/2m³ en ambos arreglos con B fijo; H18 mantuvo masa inicial10.080.000kg con salida declarada y residuo0kg / −1,9e−9kg (tol0,1008kg). H14–H16 muestran balance de energía térmica en xarray, H16 máximo4,56e−8J frente0,02J. **CUMPLIDO** como balances de cada fenómeno aislado. **NO** prueba conservación conjunta de energía mecánica+termal durante colisiones ni entre Landlab/Bullet/FiPy.

**E2(d), variar solo gradiente:** H18 registró única variación: factor0,5 del bedrock, con K_sed/masa/condiciones idénticas; hubo transporte diferencial de39%. H16 mostró control sin gradiente térmico, sin cambio; H17 control sin gravedad. **CUMPLIDO**.

**Salida E2 («casos límite y reproducibilidad»):** H17 g0, libre/bloqueado, replay exacto y 18 corrupciones rechazadas; H18 K_sed=0, dos pendientes, replay y cinco corrupciones rechazadas, balances por paso; NetCDF íntegros. **CUMPLIDO en escenas pequeñas.**

## Límites y próximos gates

No confundir el cumplimiento de pruebas **locales separadas** con un mundo físico/ambiental simultáneo. Los casos H17 y H18 usan propiedades/geometrías y resoluciones diferentes, no un mismo espacio ni un reloj coordinado. La continuidad/recuperación **desde medio de simulación** corresponde a E6, y el acoplamiento por relieve/agua/calor a E5. No hay desaparición espontánea de colinas, geología calibrada, cavernas que se excaven solas, estructura duradera comprobada o explorador.

**Etapa1:** cerrada provisionalmente [ADR-0009](DECISIONES/ADR-0009_GATE_ETAPA_1_MINIMO.md).
**Etapa2:** **cerrada provisionalmente solo como dos reglas locales experimentales** tras H17/H18. **No** fusión a main ni motor general seleccionado.
**Etapa3:** abierta, falta patrón estructural persistente y control de azar/plantillas. H10 no formó pila, H12 falló por clamp inferior. La próxima prueba de mayor valor será **analizar estabilidad y organización del material depositado por la propia Landlab en H9/H18**, con componentes conectados, persistencia longitudinal y controles diferenciales. No integrar otra solución sin una brecha física demostrada.

**Reapertura E2** obligatoria si la futura coordinación de instancias produce dos propietarios de la materia, acumulaciones no contabilizadas, fallos de estado o contradicciones físicas. La falta de acoplamiento no se soluciona declarando falsamente que ya existe; se trata en E5.
