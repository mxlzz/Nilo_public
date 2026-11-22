# Etapa 1 — H5: resultados de propiedad exclusiva superficie/volumen local

**Fecha:** 2026-11-22. **Estado:** H5 APROBADA para un contrato de datos particionado, SIN movimiento ni leyes físicas; etapa 1 ABIERTA.
**Plan anterior al código:** `ETAPA_1_H5_PROTOCOLO_ACOPLAMIENTO_ESTADO.md`.
**Arnés:** `experiments/probe_e1_surface_volume_partition.py`.
**CI verificable:** https://github.com/mxlzz/Nilo_public/actions/runs/45035061531 (**SUCCESS**).
**Versiones del runner:** Python 3.13.18, Landlab 2.11.0, xarray 2026.9.0.

## Contrato ensayado
- Dominio 12×8 columnas; región volumétrica rectangular de 8×6 columnas, hasta 7 niveles (1m por voxel); 48 columnas en ROI, 48 columnas exteriores.
- **Estado autoritativo, un solo Dataset:** `outside_column_mass(material,y,x)` tiene cantidades únicamente fuera de ROI; `roi_voxel_mass(material,z,roi_y,roi_x)` contiene cantidades únicamente dentro de ROI. Un campo de región `region_is_volume(y,x)` impide superposición. Ambos suman inventario por especie (A densidad2kg/m³, B densidad1kg/m³; valores ficticios de capacidad, NO materiales reales). `Landlab.topographic__elevation` es **caché de altura DERIVADA**, no material duplicado.
- Estado inicial **A=762kg, B=3kg**. Fuera de ROI una columna homogénea está representada por 4kg A equivalentes a 2m; en ROI hay columnas llenas de 6m con tres vóxeles superiores B. No se simula equilibrio ni desplazamiento.

## Resultados y controles
1. **Cavidad:** retirar manualmente material A en 16 vóxeles internos (16m³) con registro de salida externa **32kg A**, conserva exactamente el resto de inventario. La superficie z(x,y) no cambió. Control deliberado sin declarar salida fue rechazado por balance. Una reconstrucción ingenua de columnas desde altura crearía **32kg A fantasma**.
2. **Remoción del techo:** se extrajeron luego otros **2kg A** del voxel superior z5 en una columna; cota derivada allí cayó de 6 a 5m y ninguna otra columna cambió. Su primer raster pasó a estar desactualizado y el verificador lo detectó; se volvió a publicar el campo derivado.
3. **Caché de altura adulterada:** modificación directa en Landlab sin cambio de owner fue detectada; no cambió el inventario.
4. **Doble owner simulado:** añadir 1kg exterior dentro de ROI provocó rechazo por contrato y no modificó el estado válido.
5. **Balance:** con 34kg A de salidas explícitas, inventario final **A=728kg, B=3kg**, correcto. NetCDF sin caché duplicada, **8,536 bytes**, recuperó exactamente masas, máscara, alturas regeneradas y mismo SHA-256 del estado final.
6. **Reproducibilidad/identidad:** SHA256 inicial `ef46761f7b075dde268f57be226d3f38096d72a5a6c50d5bccc635a1e46c5460`, tras cavidad `68fff3e0155332c4de3e33a05594297441e49ddfd84c2f5b6ce109de49328a29`, final `cd57f7a67e96df5896741d671ce85a02c589e198cf5e26f035f7fb82cc25b31f`.

## Juicio
**H5 validó que superficies y volúmenes locales pueden compartir un contrato de propiedad material sin doble contabilización en un caso fijo y medible**, usando soluciones de datos existentes. Esto aporta evidencia para una representación **híbrida opcional** y reduce necesidad de motor desde cero; no significa que Landlab esté integrado físicamente con un solver volumétrico.

**Límites:** ROI rectangular estática, exterior de columnas homogéneas sin cavidades, pasos enteros de 1m, sin leyes de gravedad/erosión/cohesión/flujo ni cargas reales. La sincronización de cache fue explícita en el script y NO automática a un solver. La prueba no demuestra evolución abierta, representación universal ni seguridad multiproceso.

## Gate posterior
La **evolución** podría generar cavidades fuera de ROI; por ello, una arquitectura híbrida necesita saber promocionar una columna de superficie al dominio 3D **sin perder inventario**, y debe impedir colapsar una columna con huecos a una representación que no pueda distinguirlos. Este paso se autoriza como H6 de datos con un escenario mínimo (no solver) antes de ADR de arquitectura provisional. No pasar a Etapa 2 sin contrato material de salida suficiente.
