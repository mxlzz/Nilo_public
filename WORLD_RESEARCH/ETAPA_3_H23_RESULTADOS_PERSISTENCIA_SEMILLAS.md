# Etapa 3 — H23. Ensayo longitudinal detenido por concentración físicamente inválida

**Fecha:** 2026-11-22. **Dictamen:** **H23 NO APROBADA**. La CI ejecutó el ensayo original hasta detectar y rechazar un estado numérico inválido; no produjo resultados completos para las tres semillas/controles ni alcanza sus gates estructurales. [Protocolo previo](ETAPA_3_H23_PROTOCOLO_PERSISTENCIA_SEMILLAS.md), [código](experiments/probe_e3_h23_longrun_seeds.py), [CI 45084330437 — FAIL](https://github.com/mxlzz/Nilo_public/actions/runs/45084330437).

## Hallazgo exacto

Se utilizó FiPy4.0.3 para la ecuación de Cahn–Hilliard de H21/H22 con `epsilon=.5`, `D=1`, mezcla A/B de400kg en grilla20×20 y calendario temporal original extendido a600 pasos, seeds fijadas20261122,20261123,20261124. La CI **se detuvo durante la tercera semilla, paso579** al devolver `phi_min=0,06843968511496144` y **`phi_max=1,001010939558874`**. `phi` representa la fracción A de una celda y no puede exceder 1; implicaría masa negativa B si se publicara al owner.

El arnés detectó el estado provisional **antes de publicar** el siguiente candidato; imprimió `WORLD_EVAL_JSON` con seed, paso, extremos y gate `nonphysical_phi_or_nonfinite`, y salió con error, según [log CI](https://github.com/mxlzz/Nilo_public/actions/runs/45084330437). No recortó `phi`, no corrigió masa ni cambió `dt` ni tolerancias. El código de H21/H22 sigue igual y la masa autoritativa no incorporó ese candidato.

**Alcance de los datos:** las primeras dos semillas llegaron hasta sus600 pasos dentro de la misma ejecución secuencial, pero el arnés original estaba diseñado para emitir el informe global solo tras completar los cinco escenarios; **sus estadísticas no se emitieron y no se infieren ni inventan**. La tercera seed no terminó; el control D0 y el replay **no se ejecutaron** en esa corrida. Por ello no es posible emitir el contraste de al menos2/3 semillas ni dictaminar estabilidad/variación. Se trata de **fallo de factibilidad numérica/conservación de límites físicos**, no una refutación de la ecuación matemática Cahn–Hilliard.

## Análisis técnico independiente

La documentación upstream de FiPy `examples/cahnHilliard/mesh2D.py` proporciona un método de diferencia conservativa de masa, **no garantía explícita de preservar [0,1]** bajo todos los pasos del esquema. La literatura académica reconoce esta dificultad y propone discretizaciones específicas de volumen finito con **preservación de cotas y disipación de energía** (Bailo et al., 2023, [publicación](https://www.global-sci.com/cicp/article/view/7202)), así como modelos no locales con garantías parecidas ([artículo 2024](https://comptes-rendus.academie-sciences.fr/mecanique/articles/10.5802/crmeca.265/)). **No es lícito deducir que esas técnicas ya están implementadas en FiPy o en nuestro repositorio** sin código comprobado.

**No** implementar clipping, proyección, reescalado energético ni un solver nuevo para «salvar» H23: convertiría el fallo en un parche y ocultaría la propiedad que falta.

## Decisión de valor y línea siguiente

H21 y H22 evidencian causalidad de una separación de fases en una **mezcla abstracta2D**, pero no forman estructuras sólidas mecánicamente soportadas del mundo. H23 demuestra además una limitación de estabilidad numérica de la aproximación durante su continuación. Antes de más barridos de `epsilon`, `dt` y mallas, revisar la pertinencia de esta línea frente al objetivo [etapa3](BASES_Y_HOJA_DE_RUTA.md): **depósito/cohesión/transporte/agregación con configuraciones estables, no plantadas**.

**Propuesta de prioridad:** suspender optimización del ejemplo Cahn–Hilliard hasta disponer de un fenómeno material del mundo que necesite efectivamente separación de mezclas. Comparar **soluciones existentes de deposición granular/cuerpos con fricción y validación de estabilidad** usando nuestro PyBullet H17/H10 (y alternativas MuJoCo/DEM), sin inventar otro motor. Solo después preregistrar una prueba de formación de agregado que respete masa, geometría, contactos y persistencia. E3 ABIERTA, sin fusión a main ni NeuroLab.
