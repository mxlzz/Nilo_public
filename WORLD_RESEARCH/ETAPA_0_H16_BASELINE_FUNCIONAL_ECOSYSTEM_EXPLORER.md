# Etapa 0 — Ecosystem Explorer como benchmark funcional (evaluación documental)

**Fecha:** 2026-11-21. **Alcance:** mundo físico generativo, separado de NeuroLab. Registro de declaraciones publicadas del autor, NO validación de física ni reutilización de código.
**Fuente primaria:** https://www.ethanjhulbert.org/ecosystem-explorer/about/ (sitio oficial 2026).
**Interfaz pública:** https://www.ethanjhulbert.org/ecosystem-explorer/ .
**Condiciones legales:** https://www.ethanjhulbert.org/privacy-legal/ (revisadas 10-oct-2026).

## Capacidad declarada vs objetivo confirmado
1. **Reglas híbridas y variables del ambiente:** el autor describe elevación, temperatura, lluvia, humedad, superficie de agua, agua subterránea, nieve, suelo, tipos de vegetación y perturbaciones, con relaciones simplificadas. Relevante como **baseline funcional integrado**; NO como prueba de buena conservación/precisión científica. El propio autor niega que sea un modelo terrestre calibrado o un pronóstico.
2. **Mundo inicial + evolución:** generación por semillas, presets de costa/islas/deltas/cadenas, ejecución por días/estaciones/años y tiempo acelerable. Se presenta como componente central.
3. **Organización no prediseñada:** hábitats se interpretan del estado cambiante, algunas formas y patrones aparecen por reglas, pero la fuente NO demuestra nuevas reglas ni evolución abierta de estructuras/materiales fuera del catálogo del motor. No confundir emergencia de un pantano con abiogénesis u organización ilimitada.
4. **Territorio pequeño inicial:** mapas por tiles y 2D/3D, selección de tamaño y seed. La interfaz pública expone un ejemplo WORLD 384², área 369km², pero eso es estado visible, no medida de precisión física.
5. **Autonomía sin observador:** declara avance sin acciones del jugador mientras la sesión está activa; ejecuta localmente en el navegador, con guardado en browser/export. **NO se identificó evidencia de que el mundo avance realmente mientras el navegador está cerrado o cuando no existe proceso activo**. La persistencia del estado y el avance offline son cosas distintas y la documentación no lo confirma.
6. **Experimentación/auditoría:** inspector de tiles con elevación, agua superficial, humedad, vegetación, lluvia local, nieve, manantial, agua subterránea y dirección de flujo; se pueden observar regiones. No se encontraron archivos de pruebas causales oficiales o datos de calibración que justifiquen reproducibilidad física más allá de la semilla inicial.
7. **Intervención controlada:** subir/bajar relieve, añadir/retirar agua, plantar/despejar, fuego, manantiales, volcanes y cambios de clima; adecuados para caja negra y ablaciones, si una sesión de navegador permite registrar estados.
8. **Reutilización:** no se encontró distribución de fuente con licencia libre. Los términos del sitio mantienen copyright de código original salvo licencia separada. **No copiar motor ni reproducir gran parte del código**; sí usar como referencia legítima de requisitos de producto y casos de prueba.

## Protocolo H16
`ETAPA_0_H16_PROTOCOLO_ECOSYSTEM_EXPLORER.md` preregistra un smoke con Playwright de una sola sesión pública: controles visibles y reloj de simulación. No requiere descargar ni leer la implementación interna. El primer resultado de CI debe interpretarse como **evidencia de UI**, no evidencia de física. H16B (no ejecutado) requerirá pruebas controladas de mapa por seed/guardado/ambiente y seguimiento de tiles.

## Evaluación relativa al resto
- Frente a WorldEngine: Ecosystem Explorer declara integración temporal/ambiental y edición; WorldEngine aporta código reutilizable del estado inicial, pero no pretende evolución prolongada.
- Frente a Landlab: Ecosystem Explorer gana como **funcionalidad visible de mundo completo**, Landlab gana como código científico disponible con pruebas, ecuaciones documentadas y componentes reutilizables. No confundir producto y biblioteca.
- Frente a Sandspiel/TPT: Ecosystem Explorer desarrolla macroambiente, los otros materiales locales con fenómenos granulados y contacto. Compiten por el caso de uso, no necesariamente por ocupar exactamente el mismo componente del motor.

## Dictamen de documentación
**Ecosystem Explorer es benchmark funcional prioritario para nuestra visión; no es un núcleo reutilizable comprobado**, ni prueba automática de evolución abierta. No se descartará de la comparación por inconveniencia técnica. Estado: inspección documental completa; prueba H16 pendiente y no autorizada inferencia de dinámica real sin datos.
