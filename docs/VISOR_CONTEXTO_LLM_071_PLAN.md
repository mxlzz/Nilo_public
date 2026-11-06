# Nilo 0.7.1 · Visor literal de solicitudes LLM (7 etapas)

**Objetivo de usuario:** observar el contenido crudo de cada petición real del LLM, dividido en bloques desplegables por campos/roles, con **título original**, **subtítulo explicativo mínimo** y acceso al origen de cada variable. La vista técnica usa los mismos datos y añade diagnósticos de motor. La interfaz del laboratorio es independiente de la interfaz principal de Nilo y de la instrumentación.

**Rama de trabajo:** `work/0.7.1-visor-contexto-llm`. **Base:** `v0.7.0`. **Estado:** etapas 01–03 validadas en CI; etapa 04 implementada, CI pendiente; etapas 05–07 pendientes. Se mantiene el PR de correcciones funcionales [#78](https://github.com/mxlzz/Nilo_public/pull/78) por separado. No actualizar `VERSION` ni publicar `0.7.1` solo por completar el visor.

| Etapa | Alcance | Evidencia exigida |
| --- | --- | --- |
| **01 · Auditoría y contratos** | Mapear percepción → proyección → presupuesto → proveedor → cuerpo HTTP; revisar código existente, persistencia y fallback; fijar fidelidad literal y alcance. | [Auditoría y contrato de diseño](VISOR_CONTEXTO_LLM_071_ETAPA_01.md) y test de frontera sin red. |
| **02 · Captura por intento** | **Validada:** sidecar por mundo con cuerpo UTF-8 literal, IDs y estados por intento de deliberación/chat/fallback/reintento. | [Implementación y pruebas](VISOR_CONTEXTO_LLM_071_ETAPA_02.md) · CI [#42247337129](https://github.com/mxlzz/Nilo_public/actions/runs/42247337129), Linux y Windows: success. |
| **03 · Segmentación literal** | **Validada en CI:** índice literal por rol/campos JSON, títulos originales, subtítulos externos, rutas anidadas. | [Acta y pruebas](VISOR_CONTEXTO_LLM_071_ETAPA_03.md) · [CI #42249871479](https://github.com/mxlzz/Nilo_public/actions/runs/42249871479), Linux/Windows success. |
| **04 · Procedencia por campo** | **Implementada, pendiente de CI:** rastreo de cambios reales por etapa y referencias AST de origen por campo, sin valores ocultos persistidos. | [Acta y pruebas](VISOR_CONTEXTO_LLM_071_ETAPA_04.md) · coincidencia con BLOB HTTP, privacidad, fallback y migración. |
| **05 · API de consulta** | Acceso local de solo lectura a intentos, segmentos y trazas; selección por sesión, modelo y fecha. | Contratos, límites, seguridad, compatibilidad de partidas y nula modificación del mundo. |
| **06 · Visor inicial** | Interfaz simple (bloques literales y subtítulos) y técnica (diagnósticos), navegación por intentos. | Usabilidad a probar con el usuario; sin modificar el motor para cambiar presentación. |
| **07 · Cierre de integración** | CI total, Windows portable, privacidad, sesiones largas, retrocompatibilidad y validación de datos verdaderos. | Reporte técnico y decisión de integrar a una versión sin afirmar que el visor mejora la conducta. |

**Regla entre etapas:** auditar dependencias/contratos del tramo, implementar el propietario real, añadir pruebas positivas/negativas y documentar evidencias. No crear un segundo constructor de requests ni un segundo motor.

**Lo que permanece fuera:** editor genérico de Python, física parametrizable, ejecución de deliberaciones pagas desde el visor y correcciones conductuales (objetivos compuestos, exploración). Son trabajos independientes.
