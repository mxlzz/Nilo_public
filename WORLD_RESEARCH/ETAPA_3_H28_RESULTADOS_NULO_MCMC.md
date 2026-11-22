# Etapa 3 — H28. Nulo de esferas casi excluyentes mediante MCMC: comparación APROBADA

**Fecha:** 2026-11-22. **Dictamen:** **H28 APROBADA exactamente bajo protocolo preregistrado**, como contraste de organización geométrica de pilas H26 frente a distribuciones de materia aleatorias con restricciones espaciales, **no** como prueba estadística idealmente independiente ni de roca/cavidades/funcionalidad. [Protocolo H28](ETAPA_3_H28_PROTOCOLO_NULO_MCMC.md), [código](experiments/probe_e3_h28_mcmc_spatial_null.py), [CI 45085820365 SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45085820365), commit `059aa2850eb82318fd8916c540a3bb7e37ab0ba5`. Mantener H27 en estado FAIL no concluyente: su muestreador secuencial no era viable; no alterado ni borrado.

## Método y diagnósticos preregistrados

**Fuente:** reproducir directamente las dos escenas H26 de gravedad/fricción con mismos SHAs físicos publicados, sin modificar PyBullet, material ni código. Solo análisis espacial posterior.

**Red homogénea para comparación:** componentes de grafo geométrico entre granos cuyos centros están separados por ≤`2R+0,015m=0,165m`; suelo excluido; no equivale al grafo de contactos con fuerza positiva de H26. Nulos: **dos cadenas MCMC independientes por semilla física**,128 muestras por cadena,256 por semilla; partir del estado material real, mantener **z EXACTA por grano** y pertenencia a dos bandas radiales según su radio inicial (interior/exterior del radio mediano), cada propuesta aleatoria XY local80% o nuevo radio/azimut de misma banda20%, aceptar si mantiene separación centro–centro **≥0,148m** (tolerancia de2mm frente diámetro nominal0,150m).20.000 propuestas de calentamiento y2.000 entre muestras por cadena; no se cambió diseño después de resultados.

Las muestras **no** son materia en equilibrio mecánico ni exactamente independientes, aunque el nulo respeta exclusión casi rígida, distribución por alturas y conteos radiales. Las dos cadenas superaron movilidad y consistencia predefinidas, no un análisis de tiempos de autocorrelación de todos los estadísticos.

## Observaciones por semilla

**Seed20261122 (H26 real mismo SHA `ac1dd51b214ede889328a672237a07a850ba7e183b0fa4ed4ffbf73b4e223697`):**
- Red geométrica real **107** granos mayor componente,140 aristas; red H26 **de fuerzas**73 granos, 106 contactos.
- 256 nulos hard-core (mínima distancia verificada≥0,148000146m), componente media**16,9258**, percentil95 **31**, máximo de todas las muestras**42**. Margen real−P95 = **76 granos** (>10).
- `p_emp=(1+0)/(256+1)=0,00389105` (0 de256 nulos≥107; aproximación de rango de muestras correlacionadas, no significancia estrictamente iid).
- Dos cadenas: tasas de aceptación**49,83% / 50,03%**, fracción de granos desplazados más de un radio **98,4% / 98,4%**, medianas de desplazamiento horizontal**0,615/0,657m**. Medias componentes17,422 y16,430 (diferencia0,992<10) ⇒ gates de movimiento/acuerdo superados.

**Seed20261123 (H26 real mismo SHA `b364de5794470a7677eed42d5e544fcfbfa0fb282db2dc6cbecf2c651391ab4d`):**
- Red geométrica real **101** granos mayor componente,150 aristas; red de fuerzas H26 **92** granos,106 contactos.
- 256 nulos hard-core (mínima distancia≥0,14800380m), componente media**17,8828**, percentil95 **33**, máximo**44**. Margen**68 granos**.
- Empírico `p_emp=0,00389105` (ninguno de256 nulos≥101).
- Dos cadenas: aceptación **50,30%/50,12%**, fracción de granos desplazados >R **96,8%/100%**, medianas XY finales**0,575/0,613m**; medias componentes17,930/17,836, diferencia0,094<10. Gates de mezcla operacional superados.

**Resultado de CI:** `failed_preregistered_gates=[]`, todos los SHA/owner H26 exactos, estructura observada supera P95 por≥10 y p emp≤.05 **para ambas semillas**, dos cadenas por escenario con aceptación>0,01, movilidad>50%, acuerdo de medias<10. No se implementaron fuerzas, no se redujo el umbral de proximidad ni se recalibró Bullet. Nulo más realista que un simple azar sin exclusión, pero **no es un ensemble thermodynamically equilibrated**.

## Interpretación y límites

**Demostrado:** en este banco abstracto de esferas rígidas, la concentración y red de proximidad final de un agregado sostenido físicamente por fricción/gravedad **excede ampliamente** las redes de azar espacial bajo un nulo que condiciona alturas, mitad interior/exterior de distribución radial y exclusión casi rígida. Combinado con [H26](ETAPA_3_H26_RESULTADOS_DEPOSITO_GRADUAL.md) —dos seeds, reposo, contactos con fuerza, ablación de μ→0 y masa conservada— cubre el contraste espacial exigido por **gate mínimo de Etapa3**.

**NO demostrado:** distribución idéntica de radios dentro de cada banda, independencia plena MCMC/ESS, equilibrio de fuerzas en nulos, sostenimiento de cavidades3D, cohesión de roca, fricción geológica calibrada, evolución durante meses/años, estado reanudable de reservorio o acoplamiento de sedimento/calor. No atribuir ese alcance a un p empírico pequeño.

**Paso obligatorio:** efectuar [auditoría formal de gate Etapa3](AUDITORIA_CIERRE_ETAPA_3_2026-11-22.md) contrastando sus criterios originales y dictaminar cierre provisional solo en laboratorio rígido, sin mezclar con Etapa7 «organización no prediseñada funcional y longitudinal». Etapas4–8 no están aprobadas por H28.
