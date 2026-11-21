# Ensayo 01 — materia, cantidades e invariantes (2026-11-21)

**Estado tras auditoría:** spike exploratorio con pruebas CI, **no adoptado como núcleo del proyecto**. Se implementó antes de cerrar etapa 0, incumpliendo la puerta de evaluación de alternativas. Congelar expansión hasta ADR-0002. No forma parte de Nilo ni NeuroLab.

## Decisión de alcance

Para evitar variables inertes y una falsa apariencia de física completa, el primer programa implementa únicamente las propiedades que pueden ponerse a prueba ahora. El sistema puede ampliarse o reemplazarse después; la grilla no constituye una decisión final sobre la representación espacial del mundo.

### Propiedad del material (ficha inmutable)
- `id`: identidad de componente.
- `density`: densidad positiva finita (unidades de masa/unidades de volumen). En esta etapa constante; no representa todavía temperatura, presión ni fases.

### Estado de una región
- Posición de celda `(x,y)`, en una grilla finita bidimensional.
- Inventario de **masa por componente** (valores positivos). Dos materiales pueden coexistir en una celda; eso no implica mezclado químico ni miscibilidad física.
- Capacidad espacial `cell_volume` común para cada celda.
- **Volumen ocupado derivado**: suma de `mass[material] / density[material]`. No se persiste por separado.
- Instantánea con versión, dimensiones, materiales y distribución de materia.

### Reglas del primer ensayo
1. `add_initial` introduce masa de manera **explícita** durante la configuración. No es un proceso natural.
2. `transfer` mueve masa de un componente entre celdas en una operación atómica; no la crea ni destruye.
3. Una operación no puede retirar más masa que la disponible, superar la capacidad de destino o usar coordenadas/materiales desconocidos. Un rechazo deja el estado intacto.
4. Las propiedades y cantidades deben ser finitas, sin masa ni densidad negativas; pequeños errores de coma flotante se admiten con tolerancia documentada `1e-10` para capacidad y balances.

**Aún NO implementado:** gravedad, aceleración, velocidad, fuerzas de contacto, cohesión, adherencia, movilidad, energía, temperatura, cambio de fase, erosión, formación de estructuras, generaciones, criaturas y LLM. Propuestas de catálogo posteriores:
- movilidad efectiva, cuando un modelo de transporte explique cómo se usa;
- cohesión/adhesión, cuando un ensayo de agregación pueda medirlas;
- energía y termodinámica, cuando haya intercambios térmicos que se puedan verificar.

El objetivo NO es que todos los materiales sean líquidos o se mezclen; la grilla solo contabiliza masas compatibles con una capacidad común. No extrapolar la regla de volumen aditivo a todos los estados físicos reales.

## Experimento ejecutado

Archivos:
- `experiments/matter_v0.py`: núcleo mínimo de materia.
- `experiments/test_matter_v0.py`: ocho pruebas `unittest` sin librerías externas.

Ejecutar desde la raíz del repositorio:

```bash
cd WORLD_RESEARCH/experiments
python -m unittest -v test_matter_v0.py
```

**Evidencia verificable (2026-11-21): 8 pruebas satisfactorias en GitHub Actions**, ejecución https://github.com/mxlzz/Nilo_public/actions/runs/44942005067 . No conservar una afirmación independiente de ejecución local si no se dispone de registro verificable. El resultado no demuestra dinámica, rendimiento, aptitud arquitectónica ni emergencia.

Pruebas:
1. Densidades distintas implican volúmenes ocupados distintos para una misma masa.
2. Dos componentes coexisten sin superar capacidad ni transformarse mutuamente.
3. Transferencia conserva la masa total de **cada** componente.
4. Rechazo de capacidad excedida conserva estado.
5. Rechazo de masa inexistente conserva estado.
6. Rechazo de propiedades, cantidades y posiciones inválidas.
7. Serialización y restauración reproducen el mismo estado; versión incompatible falla.
8. Secuencia de 200 intentos de transferencia con semilla 7321: misma trayectoria determinista en la misma versión e invariantes verificadas.

No se afirma que haya 200 transferencias exitosas: las propuestas inválidas se rechazan; el ensayo registra 200 intentos.

## Prueba siguiente propuesta histórica — movimiento por gravedad (EN PAUSA)

Hipótesis: un material con movilidad positiva desciende por una regla local sin órdenes externas, respetando materia y capacidad, y el mismo material con movilidad nula queda inmóvil. Evitar una regla especial «material A cae»; comportamiento en función de propiedades.

Pruebas de aceptación a escribir antes del algoritmo:
- Masa por componente conservada en cada paso y en 1000 pasos.
- Ninguna celda excede su capacidad.
- En ausencia de soporte, el centro de masa del componente móvil disminuye en altura con orientación definida.
- Con movilidad 0 no cambia su distribución.
- Tras guardar y restaurar, la trayectoria continúa idéntica (dentro del modelo determinista).
- Sin gravedad, no hay descenso sistemático inducido por el motor.
- En dos orientaciones/simetrías equivalentes, la regla no produce sesgos espurios de barrido.
- Registrar casos de fracaso y dependencia del paso temporal.

**Advertencia:** este pequeño motor no sería todavía competente para líquidos, sólidos elásticos ni erosión real. Comparar la representación con técnicas existentes antes de extenderlo. Si los requisitos crecen, evaluar sustituirlo por una biblioteca física apropiada sin perder los casos de prueba.

## Soluciones existentes consideradas

- [Sandspiel](https://github.com/MaxBittker/sandspiel): simulación celular de «arena», Rust/WASM/WebGL, licencia MIT; referencia adecuada para actualización local eficiente y sesgos de barrido. No garantiza organización evolutiva abierta.
- [The Powder Toy](https://github.com/The-Powder-Toy/The-Powder-Toy): sistemas de partículas/materiales, presión, calor y otras interacciones; licencia GPLv3. Mayor alcance pero modelo y licencia condicionan integración.
- [GeoTaichi](https://github.com/Yihao-Shi/GeoTaichi): simulación numérica de materiales granulares, fluidos y mecánica acoplada. Más física y complejidad que las requeridas en esta primera prueba.

**Decisión provisional:** prueba propia mínima para verificar y precisar invariantes; no decidir todavía reutilización o desarrollo de motor físico. La comparación es de alcance, no un benchmark.

## Criterio de progreso

- La etapa «representación mínima y balances» posee un prototipo verificable con tests locales.
- **No** está validada como fundamento físico completo ni como diseño irrevocable.
- **Siguiente trabajo real:** cerrar etapa 0 con comparación de reutilización y benchmarking de candidatos; no ampliar el motor de materia hasta que un ADR valide esa necesidad. CI ya configurado y verificado.
- **Control de proyecto:** [procedimiento y auditoría](PROCEDIMIENTO_Y_AUDITORIA.md) y [ADR-0001](DECISIONES/ADR-0001_REUTILIZACION.md).
