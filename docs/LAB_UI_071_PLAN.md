# Nilo 0.7.1 · Auditoría y depuración integral de la interfaz del laboratorio

**Base técnica:** rama `work/0.7.1-visor-contexto-llm`, pendiente de integración por PR #79.
**Trabajo visual:** `work/0.7.1-lab-ui-audit`, separado de motor, autonomía y release `0.7.0`.
**Principios:** conservar los cuerpos HTTP literales y los contratos de instrumentación; diferenciar datos reales, calculados, simulados e históricos; evitar referencias de código no verificadas.

| Etapa | Alcance | Criterio de cierre |
| --- | --- | --- |
| **01 · Correcciones funcionales y semánticas — validada** | Estados y etiquetas veraces; historial sin información vieja; enlaces precisos. | [Acta 01](LAB_UI_071_ETAPA_01.md) y [CI aprobado #42292210597](https://github.com/mxlzz/Nilo_public/actions/runs/42292210597). |
| **02 · Arquitectura de información — implementada, en validación** | Cuatro secciones globales; tres modalidades de Pruebas; vínculos y nombres consistentes, estados navegables sin cambiar la física. | [Acta 02](LAB_UI_071_ETAPA_02.md), tests de navegación y CI final. |
| **03 · Sistema de diseño — implementada, en validación** | Tokens, CSS compartido y controlador de tema sistema/claro/oscuro. Se preservan distribuciones y motores. | [Acta 03](LAB_UI_071_ETAPA_03.md); pruebas de CSS/JS, rutas HTTP y empaquetado; CI final. |
| **04 · Cinco subetapas por pantalla** | 04.1 Visor LLM (implementada, [acta](LAB_UI_071_ETAPA_041.md)); pendientes 04.2 Historial, 04.3 Escenarios, 04.4 Mundo interactivo y 04.5 Ajustes. | Pruebas de interacción por pantalla, literalidad y revisión visual diferida. |
| **05 · Auditoría final** | Accesibilidad, rendimiento, compatibilidad y regresiones transversales. | Validaciones finales, documentación y decisión de integración. |

La revisión visual por el usuario queda diferida; la etapa 01 no impone decisiones estéticas. Ninguna etapa autoriza cambios automáticos del motor o de prompts. No fusionar en `main` ni publicar una nueva versión hasta la revisión integral.
