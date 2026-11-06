# Nilo 0.7.1 · Visor literal de solicitudes LLM (7 etapas)

**Objetivo de usuario:** observar el contenido crudo de cada petición real del LLM, dividido en bloques desplegables por campos/roles, con **título original**, **subtítulo explicativo mínimo** y acceso al origen de cada variable. La vista técnica usa los mismos datos y añade diagnósticos de motor. La interfaz del laboratorio es independiente de la interfaz principal de Nilo y de la instrumentación.

**Rama de trabajo:** `work/0.7.1-visor-contexto-llm`. **Base:** `v0.7.0`. **Estado:** etapa 01 validada en CI; etapa 02 implementada, CI pendiente; etapas 03–07 pendientes. Se mantiene el PR de correcciones funcionales [#78](https://github.com/mxlzz/Nilo_public/pull/78) por separado. No actualizar `VERSION` ni publicar `0.7.1` solo por completar el visor.

| Etapa | Alcance | Evidencia exigida |
| --- | --- | --- |
| **01 · Auditoría y contratos** | Mapear percepción → proyección → presupuesto → proveedor → cuerpo HTTP; revisar código existente, persistencia y fallback; fijar fidelidad literal y alcance. | [Auditoría y contrato de diseño](VISOR_CONTEXTO_LLM_071_ETAPA_01.md) y test de frontera sin red. |
| **02 · Captura por intento** | **Implementada, pendiente de CI:** sidecar por mundo con cuerpo UTF-8 literal, IDs y estados por intento de deliberación/chat/fallback/reintento. | [Implementación y pruebas](VISOR_CONTEXTO_LLM_071_ETAPA_02.md) · igualdad contra transporte, fallos no bloqueantes y no contaminación del mundo. |
| **03 · Segmentación literal** | Crear índice de texto por rol y claves JSON **sobre contenido original**, sin reformularlo. Definir títulos originales y subtítulos independientes. | Reconstrucción exacta del texto de partida, incluso comillas/escapes/Unicode, y pruebas de ausencia de resúmenes. |
| **04 · Procedencia por campo** | Rastrear fuentes y transformaciones (estado, proyección, perfil, compactación y recorte); indicar origen no disponible cuando corresponda. | Rutas verificables, sin atribuciones adivinadas; revisión de campos anidados y omitidos. |
| **05 · API de consulta** | Acceso local de solo lectura a intentos, segmentos y trazas; selección por sesión, modelo y fecha. | Contratos, límites, seguridad, compatibilidad de partidas y nula modificación del mundo. |
| **06 · Visor inicial** | Interfaz simple (bloques literales y subtítulos) y técnica (diagnósticos), navegación por intentos. | Usabilidad a probar con el usuario; sin modificar el motor para cambiar presentación. |
| **07 · Cierre de integración** | CI total, Windows portable, privacidad, sesiones largas, retrocompatibilidad y validación de datos verdaderos. | Reporte técnico y decisión de integrar a una versión sin afirmar que el visor mejora la conducta. |

**Regla entre etapas:** auditar dependencias/contratos del tramo, implementar el propietario real, añadir pruebas positivas/negativas y documentar evidencias. No crear un segundo constructor de requests ni un segundo motor.

**Lo que permanece fuera:** editor genérico de Python, física parametrizable, ejecución de deliberaciones pagas desde el visor y correcciones conductuales (objetivos compuestos, exploración). Son trabajos independientes.
