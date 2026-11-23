# Auditoría estratégica E7 post-H36 — Retorno científico y criterio de continuación

**2026-11-22. Estado:** etapa7 ABIERTA; **H36 NO APROBADA** bajo soporte estable en ambas seeds. Este informe no cambia su protocolo ni selecciona un motor nuevo.

## Qué quedó demostrado y qué no

1. [H26](ETAPA_3_H26_RESULTADOS_DEPOSITO_GRADUAL.md) y [H28](ETAPA_3_H28_RESULTADOS_NULO_MCMC.md) verificaron que las leyes de gravedad/fricción/contacto generan un agregado granular conectado en suelo abierto, no la geometría de una «pila» dibujada como clase.
2. [H36](ETAPA_7_H36_RESULTADOS_FUNCION_PILA_IMPACTO.md) demostró **intercepción causal del proyectil** a alturas0,686/0,945m en dos seeds, frente a contacto del mismo proyectil con suelo a0,147m en la distribución sin fricción; las pilas permanecen conectadas bajo impacto. La geometría del montículo se formó antes, y el lanzamiento desde0,0,1,6m no se apuntó a su cima observada.
3. La **función fuerte preregistrada** era mantener la esfera a altura>0,30m y velocidad final<0,12m/s a720 pasos en ambas seeds. Seed20261123 terminó a z0,537m pero con **v0,341m/s**: H36 rechazada. Tampoco se cuantificó disipación de energía a velocidad de impacto igualada, por lo que **no** se puede afirmar «amortiguación superior» solo porque el pico de fuerza sea menor que la colisión con suelo: la velocidad de llegada difiere.
4. H33–H35 reinician subsistemas exactamente pero **no** crean un reloj mundial común ni interacciones físicas simultáneas. E5 solo demostró Landlab→Bullet secuencial. E7 exige **funciones de estructuras en un mundo**, no una colección de bancos cada vez más específicos.

## ¿Conviene un H37 de más tiempo en la misma pila?

**No por ahora.** Prolongar720→1440/2160 pasos podría contestar si la esfera seed2 se asienta o se desliza, pero:
- el H36 original seguiría fallido y la condición de soporte (duración) sería otra hipótesis;
- un resultado favorable agregaría muy poca capacidad nueva al sistema general y no demostraría nuevos tipos de organización ni robustez ecológica;
- hay antecedentes H24→H25 donde más tiempo logró quietud **pero destruyó parte de la estructura**; el signo de resultado no está garantizado y no debe buscarse selectivamente.
No se recomienda alterar fricción, altura de lanzamiento o masa para «aprobar», ni añadir otra ecuación material nueva. Conservar H36 como **evidencia parcial y negativa fuerte**.

## Selección justificada de próxima inversión

**Prioridad 1: condición habilitante para E7, no más pruebas locales de la misma función.** Verificar si los componentes E5/E6 **que ya existen** pueden avanzar causalmente en un mismo estado y reloj de simulación con *al menos un ciclo físico completo* WorldEngine→Landlab suelo mutable→Bullet contacto, con checkpoint/continuación y saldos materiales. Actualmente esas conexiones se han validado por separado, pero no existe un mundo único operable. El paso selectivo puede ser una prueba de **orquestación longitudinal mínima**, reutilizando herramientas y artefactos de H31/H33/H34, sin backend nuevo, UI, agente ni motor personalizado.

**Prioridad 2: después de ese requisito, diseñar prueba E7 de función sin ontologías especiales:** una interacción material que modifique condiciones de acceso, soporte, paso de agua o contacto para **un segundo cuerpo** por efecto de una configuración realmente formada. Comparar múltiples condiciones/semillas, ablación física y un nulo espacial condicionado, además de funcionalidad y estabilidad; evitar métricas meramente visuales o una sola sonda. Si no existe ninguna función distinguible, registrar el negativo.

**Decisión reversible de método:** **pausar nuevas variantes de impacto granular** y preparar un [prerregistro de integración causal longitudinal] solo después de inspeccionar si los scripts H31/H33/H34 pueden encadenarse sin duplicar owner y sin reejecutar pasos ya simulados. No modificar las etapas0–6 ni volver a empezar; no sobreproducir PRs preparatorios. El valor marginal debe provenir de que opere una nueva capacidad real —evolución del estado combinado—, no de añadir formatos o infraestructura.

**Límite documental:** el cierre E6 fue **solo mínimo de subsistemas**. Hasta que un ciclo combinado realmente se ejecute y sea reanudable, no declarar «el mundo funciona». Etapa7 sigue ABIERTA, no evolución abierta. No se solicita autorización para investigaciones reversibles sobre la rama aislada, pero cualquier rediseño de arquitectura o merge a `main` requiere decisión explícita según el gobierno del proyecto.
