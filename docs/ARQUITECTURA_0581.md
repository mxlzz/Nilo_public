# Arquitectura modular: segunda etapa (0.5.8.1)

## Responsabilidades actuales

| Módulo | Propiedad principal | Dependencias permitidas |
| --- | --- | --- |
| `agent.py` | Estado inicial e identidad del agente | Tipos básicos; ninguna topología |
| `scenarios.py` | Configuración del inicio; inventario y perfil | Ningún modelo físico |
| `environments.py` | Contrato entre simulación y mundo | Adaptadores concretos, `brain.context_for` y `island_views` |
| `island_views.py` | Proyección visible del mapa y condiciones locales | `world.py` y reglas exclusivas de isla_v1 |
| `world.py` | Generación y consecuencias físicas del entorno actual | Física, construcción y mecánica |
| `nilo.py` | Coordinación del ciclo temporal, deliberación, persistencia y API | Contrato de entorno; subsisten dependencias legadas |
| `survival.py` | Evolución de necesidades según condiciones recibidas | Datos de persona, sin consultar topología |

## Contratos incorporados

- `Environment.surroundings(world, agent) -> (sheltered, near_water)`: traduce topología física en dos condiciones para supervivencia. La función devuelve información interna que afecta tasas y rutinas; **no es un canal nuevo para revelar terrenos desconocidos al LLM**.
- `Environment.render_map(world, agent) -> dict`: construye mapa, capas, símbolos y rastro para la interfaz. La estructura de salida permanece igual que en 0.5.8; la lógica de presentación es específica de cada adaptador.
- `Simulation.tick` llama al entorno para obtener condiciones; `Simulation.public_state` delega la proyección. Ninguna regla de avance temporal, movimiento, materiales o pruebas físicas ha cambiado.

## Límites por resolver

- `nilo.py` conserva validaciones de rutas y acciones específicas de la isla, reglas de proyectos y lógica de migración de partidas.
- `brain.py` todavía conoce topología de isla_v1 en varios campos de contexto.
- `world.py` combina navegación y ejecución física. Para un entorno urbano o extraterrestre habrá que proporcionar implementaciones distintas, no simplemente un nuevo prompt.
- La API y la interfaz actuales consumen las claves cartográficas de isla_v1; otros mundos requieren adaptadores de visualización o representaciones genéricas.
- Hay que tipar los resultados de acciones y evitar decisiones apoyadas en cadenas narrativas (C.2).

## Criterio de aceptación

Mismo escenario y semillas: los hashes de replay deben mantenerse invariantes (si la línea base no cambia), la compatibilidad con partidas anteriores debe continuar y la pantalla debe conservar el contrato JSON. Las pruebas `test_v0581.py` verifican la nueva frontera sin LLM ni servidor.

Evitar dividir archivos por cantidad de líneas sin reducir el acoplamiento real.

## Reglas y filtrado de planificación en 0.5.8.2

- `Environment.validate_plan(world, agent, steps, remember_strategy, event)` valida restricciones físicas observables sin otorgar conocimiento oculto.
- `Environment.improve_plan(world, agent, steps, remember_strategy, event)` conserva rechazos de redundancia física por mismas condiciones.
- El adaptador de isla actual implementa ambas funciones con `IslandPlanner` en `island_planning.py`. `Simulation` coordina, registra y llama al contrato sin alojar estos algoritmos.
- La interfaz mantiene los símbolos cartográficos; tres temas modifican exclusivamente CSS local, no la topología.
- Los tests y el replay determinista tienen prioridad sobre la extracción de más código; lo siguiente es sacar otras verificaciones específicas de la isla del coordinador, no crear mundos de ficción con un prompt.
