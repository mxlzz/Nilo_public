# E09h.6b — preregistro de origen de cadencia del mundo C1

**Fecha:** 2026-11-21. **Orden:** redactado después de inspección exploratoria de SetTimer/WM_TIMER y **antes** de implementar auditor y tests. Continúa h.6a, sin alterar cerebro, Nilo ni main.

## Hipótesis falsables

H6b.1: el ejecutable original importa USER32.SetTimer y KillTimer; un wrapper específico solicita timer ID1 con intervalo **0x5A = 90 ms** y callback NULL sobre HWND del objeto global 0x43F08C; el wrapper de pausa elimina ID1. Comprobar la ubicación exacta de la llamada, argumento ID, frecuencia y HWND en código máquina.

H6b.2: la tabla de mensajes en .rdata a partir de VA 0x433988 incluye mensaje **0x113 (WM_TIMER)** y puntero manejador 0x418960 en la misma entrada. La rutina 0x418960 llama a 0x4247B0. Verificar que son partes de una entrada coherente de message map, no bytes casuales.

H6b.3: hay al menos **otro** temporizador solicitado en el EXE (0x40D078, ID1, 500 ms) desde otra ruta/ventana; **no debe confundirse** con el temporizador del mundo.

H6b.4: el estado de pausa puede instalar/cancelar timer (funciones 0x411F50/0x411F70). Se deben distinguir temporización nominal solicitada, cumplimiento efectivo del scheduler Windows, colas de mensajes y fases 0..4 de h6a.

## Criterios

- Cerrar **G-H6-CLOCK-NOMINAL** solo si auditor SHA verifica import, argumentos SetTimer/KillTimer, puntero de mensaje y llamada al world tick; test sintético y CI verdes.
- **No** cerrar frecuencia efectiva ni G-H6-CLOCK global sin verificar que los mensajes realmente llegan a intervalos regulares al ejecutarlo; no multiplicar 90 ms por cinco fases para afirmar tiempo de Norn, porque puede haber ticks omitidos o estados alternativos.
- Preservar como una incógnita el timer secundario de 500 ms si no se prueba su dueño.
- No publicar ni ejecutar EXE, no integrar, no editar estudios previos, no modificar Nilo0.7.

Evidencia local esperada: firmas x86 exactas, referencias de datos .rdata, callsites, test adversarial donde una firma falla, JSON reducido y resultado con límites explícitos.
