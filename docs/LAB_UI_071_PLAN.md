# Nilo 0.7.1 · Auditoría y depuración integral de la interfaz del laboratorio

**Base técnica:** rama `work/0.7.1-visor-contexto-llm`, pendiente de integración por PR #79.
**Trabajo visual:** `work/0.7.1-lab-ui-audit`, separado de motor, autonomía y release `0.7.0`.
**Principios:** conservar los cuerpos HTTP literales y los contratos de instrumentación; diferenciar datos reales, calculados, simulados e históricos; evitar referencias de código no verificadas.

| Etapa | Alcance | Criterio de cierre |
| --- | --- | --- |
| **01 · Correcciones funcionales y semánticas** | Estados y etiquetas veraces; historial sin información vieja ante cargas asíncronas; eliminar enlaces engañosos. Sin cambiar layout ni estilos. | Tests de regresión, JS validado, revisión CI Linux/Windows y acta de cambios. |
| **02 · Arquitectura de información** | Navegación común, nomenclatura, organización de los dos sandboxes y jerarquía de contenidos. | Contrato de rutas y estados navegables, sin pérdidas funcionales. |
| **03 · Sistema de diseño** | CSS y componentes comunes, tokens, claro/oscuro, tipografía y responsive. | Paridad funcional de todas las páginas y tests de componentes. |
| **04 · Cinco subetapas por pantalla** | Visor LLM, Historial, Escenarios, Sandbox, Ajustes; revisar una pantalla por subetapa. | Pruebas de interacción y revisión visual por pantalla; preservar el texto crudo. |
| **05 · Auditoría final** | Accesibilidad, rendimiento, compatibilidad y regresiones transversales. | Validaciones finales, documentación y decisión de integración. |

La revisión visual por el usuario queda diferida; la etapa 01 no impone decisiones estéticas. Ninguna etapa autoriza cambios automáticos del motor o de prompts. No fusionar en `main` ni publicar una nueva versión hasta la revisión integral.
