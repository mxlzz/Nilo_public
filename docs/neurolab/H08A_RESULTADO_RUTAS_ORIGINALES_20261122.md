# H-08a — resultado de auditoría estática del ejecutable original de Creatures 1

**Fecha:** 22/11/2026. **Dictamen:** **PASS limitado a inventario de llamadas directas y secuencia local**, con **nuevo tercer invocador químico identificado**. **NO** se alcanza exhaustividad de rutas indirectas ni frecuencia efectiva. [Preregistro anterior al script](H08A_PREREGISTRO_RUTAS_EJECUTABLE_20261122.md).

## Procedencia y cadena de verificación

- Se localizaron `Creatures.exe` (387.072 bytes) y `dad1.gen` (10.001 bytes) en la carpeta ya asociada `neurolab` de Google Drive, ID `1lUxvBeYDhrAXM619kq6CTOm1nWFq1jE8`. Archivos identificados en Drive: `Creatures.exe` ID `176UuTc_So8aOYNsZh7UfOA6a1Aq1M5Oh`; `dad1.gen` ID `11_NIwwRzPBlYnZhtw3CfggIP4hbFBI1n`. Se descargaron **sin ejecutar**.
- Verificación binaria local: EXE SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`; GEN SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`. **Coinciden exactamente** con la edición usada por [H1–H6](E09_H_06B_RESULTADO_CADENCIA.md); quedó levantada la dependencia de archivos de [H-07](H07_AUDITORIA_CADENA_TEMPORAL_Y_BLOQUEO_20261122.md).
- Auditoría **local sobre bytes auténticos**: GNU objdump 2.44 (`-d -M intel`) y Python 3.13.5. [Verificador versionado](../../experiments/neurolab/h08a_static_audit.py) SHA256 de archivo `7d490c041ffd573747a891dcd065abca741c36c7d3af7a280b185d84d28f3755`; blob Git `4570735c96f319573665c62e058de9377846b54d`; [salida exacta preservada](resultados/h08a_original_evidence_20261122.json), SHA256 `34963b1d4415c0e42158d86884d180165c57d640d9dd419ab9183fb5fd43c4bb`, blob Git `2e07755184c9150f84b72e70776fadb31eb6ad60`. El hash del blob de ambos archivos se comparó y coincide con las salidas locales.
- **15 firmas de instrucciones verificadas** contra `.text` del PE hasheado. Los targets de cada `E8 rel32` identificada se recalcularon con `VA+5+signed_disp32` y contrastaron con la decodificación GNU objdump.
- **Pruebas sintéticas:** cinco tests sobre PE inválido, sección truncada, lectura y desplazamiento E8, inconsistencia entre bytes y destino de objdump y punteros literales. El primer intento local del test adversarial tuvo un **oráculo del fixture incorrecto** (cambiaba el destino fuera del conjunto bajo búsqueda y por eso no constituía inconsistencia para el parser); se corrigió exclusivamente el fixture manteniendo el parser y **5/5 pasó**. [CI específica #45061311716](https://github.com/mxlzz/Nilo_public/actions/runs/45061311716) **SUCCESS**, sin originales (valida tests sintéticos y forma del JSON archivado; **NO** reanaliza el EXE en CI).
- No se suben a GitHub el ejecutable, genoma ni desensamblado completo; se preservan solo direcciones, unos bytes de firma y evidencia derivada reproducible con originales.

## Inventario de llamadas directas verificadas

Destinos exactos y sitios `call E8 rel32` en desensamblado lineal `.text` de este build:

- **Brain tick `0x403BB0`: 2** — desde `0x405DAF` (alternativa química→brain), `0x407583` (regular brain→química).
- **Química `0x421E70`: 3** — desde `0x405D32` (alternativa), `0x407595` (regular), **`0x40B089` (tercera ruta)**.
- **World tick `0x4247B0`: 3** — desde `0x418966` (WM_TIMER conocido), `0x424C98`, `0x426894` (rutas ya descritas en H6).
- El barrido de 32 bits little-endian de los **tres punteros absolutos** en el archivo PE retornó cero ocurrencias. **No es prueba de ausencia de llamadas indirectas**: pueden construirse punteros en runtime, pasar por vtables o no aparecer como literales.

**Alcance de inventario:** llamadas directas E8 cuyo comienzo objdump reconoce en el barrido lineal de `.text`; no incluye código no alcanzado, despacho virtual, saltos indirectos ni flujo dinámico.

## Hallazgo nuevo: la química se actualiza también en preparación de criatura

La llamada `0x40B089` está dentro de una función con prólogo en `0x40ADF0` y retorno en `0x40B0C4`. La función:
- Reserva/construye objeto cerebral alrededor de `0x40AF54–0x40AF89`, y objeto bioquímico en `0x40AF8F–0x40AFB2`. Esto respalda interpretar la rutina como **configuración/construcción de una criatura**, sin afirmar qué evento de juego la invoca.
- En `0x40B07C` lee `[criatura+0x2C20]` y lo pasa como contador; en `0x40B083` lee `[criatura+0x2C1C]`, objeto químico; en `0x40B089` llama a la **misma rutina de química 0x421E70** que utiliza el loop de criatura.
- Después llama a `0x40A640` en `0x40B090` y escribe `[criatura+0x2CBC]=1` en `0x40B095`. La ruta regular `0x407540` lee **ese mismo flag** en `0x407543` y, si es distinto de cero, salta a salida evitando cerebro/química en esa ruta. La ruta alternativa `0x4075C0` también consulta ese flag (comprobada en H6a).
- En el intervalo acotado `0x40ADF0–0x40B0C4` **no hay una llamada E8 directa al brain tick `0x403BB0`**; no se concluye que el cerebro carezca de inicialización, pues hay llamadas a otros helpers.
- El constructor tiene tres sitios `call E8` directos verificados adicionalmente hacia su entrada `0x40ADF0`: `0x415BAA`, `0x42564D`, `0x4256DD`. **No se infiere de eso** si corresponden a nacimiento, carga de partida o episodios concretos.
- Resultado **A con límite C**: la química puede procesarse en esta ruta de construcción sin pasar previamente por el tick cerebral regular. El flag sugiere relación con estado transitorio, pero su significado exacto y la frecuencia de uso de esta ruta requieren trazas observadas.

## Implicación causal y límites

La secuencia histórica tiene al menos **tres clases de contexto**: (1) ruta regular condicionada brain→química, (2) ruta excepcional química→brain, y (3) química en construcción/preparación del objeto. El temporizador nominal solicitado al Windows es de **90 ms** según H6b, pero no se midió duración efectiva entre ticks cerebrales. No se puede representar universalmente cada paso cerebral como `reward_t→weight_{t+1}` sin especificar clase de ruta, receptor, química y condiciones de estado.

La microred `C1ContextBrain` continúa siendo **modelo experimental N** con químicos inyectados directamente; no recibe la ruta externa química en el mismo reloj del C1 histórico. Por tanto, este hallazgo **no reabre ni salva por sí mismo** el fracaso de los bancos g.10b y G05-NX01, ni certifica capacidad neuronal.

**Puertas:**
- `G-H08a-DIRECT`: **verificada** para este binario y esas tres funciones.
- `G-H08a-INDIRECT`: **ABIERTA**, no se auditó exhaustivamente despacho virtual/computado.
- `G-H6-CLOCK efectiva`, `G00-H`, `G05`, `G09`: **ABIERTAS**.
- `NR01` y `G05-NX01`: **STOP** por reglas científicas previas; no abrir sus cohortes de confirmación.

## Próxima decisión necesaria

**H-08b** exige un diseño de observación **controlado sobre el motor C1 real** si se pretende conocer cadencia efectiva y respuesta química del organismo, con consentimiento específico del usuario antes de ejecutar código propietario; además harían falta el entorno y los recursos del juego. Un nuevo análisis de llamadas directas repetido no cerrará esa puerta. Una auditoría más profunda de despachos indirectos también sería posible estáticamente, pero no debe confundirse con un reloj real medido. **Recomendación:** no abrir otra línea de aprendizaje N hasta tener una consecuencia experimental concreta de la diferencia histórica.

**Sin ejecución del juego, sin binarios publicados, PR #103 draft, `main` y Nilo0.7 intactos.**
