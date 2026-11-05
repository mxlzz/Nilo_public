# Diagnóstico supervisado de Nilo — versión 0.5.9.0

## Objeto

Una anomalía experimental no es automáticamente un bug. Puede ser
una hipótesis equivocada, un límite legítimo o una física ausente.
La implementación diferencia tres circuitos:

| Circuito | Origen | Salida |
| --- | --- | --- |
| `propose` | Nilo | Solicitud `sol-...` para estudiar una ley no implementada |
| `report_issue` | Nilo | Solicitud `bug-...` para revisar una contradicción percibida |
| `inspect_invariants` | Motor | Solicitud `bug-...` si detecta un incumplimiento objetivable |

Todas quedan **pendientes** hasta una evaluación externa explícita.

## Monitor determinista

Tras ejecutar una acción verificable y registrar `ActionResult`, el
monitor comprueba:

1. Posición fuera de los niveles/casillas existentes (`isla_v1`).
2. Cantidad negativa de cualquier recurso en inventario.
3. Necesidades fuera de 0–100.
4. Incompatibilidad entre `ActionResult.status` y `success`.

La inspección no lee la narrativa. No afirma que una prueba fallida sea
un error de software. Deduplica solicitudes pendientes por chequeo y operación.
Las propiedades físicas y las decisiones de Nilo no cambian.

## Exportación del informe

1. En Nilo, entrar en **Vínculo → Propuestas**.
2. Abrir una solicitud y seleccionar **Exportar informe JSON**.
3. El navegador genera un archivo `nilo-informe-<id>.json` obtenido
   localmente mediante `GET /api/diagnostic?id=<id>`.
4. Leerlo y, si querés revisarlo conmigo, compartirlo en nuestra conversación.
   Yo puedo analizar el informe y proponer alternativas, pero la decisión
   de modificar el mundo o el programa siempre es tuya.

El informe es `nilo-diagnostic-v1`: contiene declaración, referencia
de escenario/entorno/versión, pruebas existentes, estado de revisión
y un hash SHA256 calculado sobre los campos restantes. El hash detecta
cambios en el contenido, pero no es firma criptográfica con identidad.

**Restricción de reproducción:** si no se guardó el mundo completo,
el estado previo y el RNG de esa acción, el archivo contiene una receta
orientativa, no un replay exacto. Nunca afirma haber replicado una falla.

## Revisión de un informe

1. Verificar que haya evidencia física y que `act-...` o
   `no-modelo-...` sean identificadores reales. El LLM puede relatar
   una observación, pero no asignar éxitos ni medidas.
2. Intentar reproducir el problema en una copia **aislada** del
   estado y comprobar si las condiciones son comparables.
3. Clasificar como bug confirmado, limitación válida, capacidad ausente,
   interpretación equivocada o información insuficiente.
4. Discutir con ChatGPT las opciones de corrección o ampliación. **El
   observador decide** si corresponde modificar el código o descartar
   la propuesta. Solo con su autorización explícita se implementan
   cambios en una rama GitHub separada, se ejecutan tests y replay
   y se integran tras su conformidad.

La revisión desde la UI modifica la **clasificación**, nunca la física.
**Aprobar el estudio o clasificar un bug no constituye autorización para
escribir código.** No hay ni se planifica un agente desarrollador que
revise, apruebe o corrija automáticamente los reportes. El único
circuito de modificación es decisión del observador, discusión con
ChatGPT e implementación autorizada por él. Nilo no accede al código
fuente ni puede escribir parches. No dar por concluido el autodiagnóstico.

## Trabajo pendiente

- Registro compacto del estado *antes* de cada acción seleccionada,
  incluida semilla RNG, reloj y versión exacta para reproducibilidad.
- Verificadores de invariantes causales específicos por fenómeno,
  evitando diagnosticar como bug una falla legítima.
- Generar casos de regresión a partir de reportes reproducidos.
- Ayudas para analizar reportes y reproducir fallos **a pedido del observador**.
  Los cambios de código, tests y GitHub se ejecutarán únicamente si él los
  solicita o autoriza expresamente, y nunca por aprobación automática.

Consultar `docs/PROTOCOLO_REVISION_HUMANA.md` para el flujo acordado.
