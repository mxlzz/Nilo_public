# E09h.5 — preregistro: emisor genético → pool C1

**Fecha:** 2026-11-21. **Estado:** preregistrado ANTES de implementar simulación aislada. No amplía el cerebro ni supone resolución de G05/G09.

## Motivación y dependencia

E09h.1 verificó el orden emisor→receptor→reacción→decaimiento dentro de una llamada química. E09h.4 verificó directamente los bytes de loci de receptor en el EXE. Falta reconstruir el eslabón inverso: qué lectura neuronal produce químicos en el pool, bajo qué restricciones, y si consume la señal de origen.

## Datos identificados anteriormente, aún a revalidar en EXE

- El mapa [E00](E00_MAPA_NEUROQUIMICO_C1.md) registra **27 genes de emisores** y tres cerebrales del GEN original: 123 Concept/lóbulo8/locus1→ConASH52, 124 Decision/lóbulo6/locus1→DecASH1=53, 125 Decision/lóbulo6/locus2→DecASH2=70. Tienen umbral0, sample_rate1, gain255, flags1; **los bytes del GEN no están adjuntos de nuevo** y no se fingirá relectura.
- En el mismo EXE de E09h.4 (SHA256 548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7), inspección exploratoria indica loader emisor 0x421AE8..0x421C7E y tick 0x421E83..0x421F77, con salida hacia químico y potencial puesta en cero del locus origen.

## Hipótesis preregistradas con controles falsables

1. **Enlace de origen:** el emisor cerebral debe invocar el resolver de CBrain en modo distinto del receptor (kind=1), con loci1/2 señalando bytes de salida/estado del lóbulo; verificar tabla de salto exacta, estructura y puntero almacenado, no asumir por nombre.
2. **Orden de lectura/emisión:** un emisor lee la fuente (o su complemento 255−x si flag&4), filtra x>0, ejecuta solo cuando tick modulo sample_rate=0, y requiere x>threshold.
3. **Valor emitido:** si flags&2, cantidad = gain (señal presente); de otro modo cantidad = ((x−threshold)*gain)>>8; sumar al químico indicado con techo255; chemical=0 no debe alterar el pool.
4. **Consumo de fuente:** si flags&1, resetear el byte fuente a0 **solo tras una emisión válida según código**; si falla filtro, periodicidad, umbral o chemical=0, conservarlo. Verificar las rutas reales, en especial chemical=0.
5. **Secuencia:** emisores operan antes de receptores y reacciones; una sustancia emitida antes del receptor puede ser muestreada en esa misma llamada química, a diferencia de una sintetizada luego por reacción.
6. **Caso numérico:** source=80, gain255, threshold0, sample_rate1, chemical52/53/70 y tick0 → cantidad=(80*255)>>8=79; source queda0 con flags1. Repetir mismo tick con source ya0 no vuelve a emitir. Para source255, gain255, resultado254.
7. **Controles adversariales:** sample_rate2 y tick1 no emite/no borra fuente; source=threshold conserva; pool245 + emisión79 se satura255; flag4 invierte; flag2 usa gain; flags1 apagado conserva fuente; source/chemical0 y combinaciones inválidas no se arreglan por conveniencia.

## Puertas separadas

- **G-H5-X86:** evidencia reproducible con offsets, huellas y rutas de código del EXE original verificadas, incluyendo resolver de emisor y flags. Sin esto, NO implementar como equivalente histórico.
- **G-H5-MATH:** después de G-H5-X86, implementación aislada, oráculos y CI sintético; contar como cinética parcial y no prueba de un Norn vivo.
- **G-H5-GEN:** los genes 123–125 se basan en la procedencia documental E00; si no están los bytes originales nuevamente disponibles, reportar fixture histórico anterior y no afirmar que se releyeron.
- **G00-H/G05/G09:** siguen ABIERTAS.

Secuencia: preregistro → verificar EXE estáticamente → auditor reproducible y fixture derivado → función aislada + tests → CI y resultado con límites → actualizar estado canónico. Nada en main/Nilo 0.7, sin correr Creatures ni redistribuir ejecutable.
