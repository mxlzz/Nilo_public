# E0.8 — H12a: auditoría del paquete oficial DRYP 2.0

Fecha: 2026-11-21. Estado: H12a VALIDADA como **inspección de distribución**, no como prueba funcional. E0 general abierta.
Plan previo: `ETAPA_0_8_DRYp_ALTERNATIVAS_Y_H11C_PLAN.md`.
Script: `experiments/probe_dryp2_archive_static.py`.
Workflow aislado: `.github/workflows/world-dryp2-static-audit.yml`.
CI real: https://github.com/mxlzz/Nilo_public/actions/runs/44956976701 (**SUCCESS**).

## Procedencia
Origen: https://zenodo.org/records/17451148 , publicado 26-oct-2025, autores Quichimbo/Singer/Michaelides/Cuthbert, DOI 10.5281/zenodo.17451148. Descarga original ZIP de 5,733,796 bytes, hash MD5 **f1c491b001755a22c90214d609c0d51b** coincidió exactamente con Zenodo. Hash SHA-256 verificado en runner: **38032acd29b592e8fcf4aa9edf180bbaa6a933ec19af85c9921150bcc3bfe36a**.

## Contenido inspeccionado sin ejecutar código externo
- 165 archivos, 40,949,130 bytes sin comprimir.
- 46 archivos fuente Python; **0 errores sintácticos** detectados por `compile` bajo Python 3.13. No se importaron clases ni dependencias; esto NO prueba compatibilidad operacional.
- Extensiones y compilados: 12 DLL, 10 PYD, 6 SO, 3 archivos Fortran, 2 Pyx, 1 C, otros módulos binarios. Requieren comprobar plataformas, ABIs y dependencias antes de ejecutar en Windows/Linux. También 18 PYC.
- Archivos de datos: NetCDF (.nc) y raster .asc, CSV, otros archivos de prueba.
- Archivo de setup descubierto: `dryp/components/setup.py`, sin `pyproject.toml`/requirements detectados con nombres estándar en el ZIP por el ensayo.
- **0 archivos `LICENSE` dentro del ZIP**. El registro Zenodo ofrece un LICENSE separado, de tipo MIT, con copyright `2024 CornishLeo`; este identificador coincide con el mantenedor citado en el tutorial de CUWALID (https://cuwalid.github.io/tutorials/github-installation/), posible explicación de procedencia. **Aún no se ha verificado que la persona que firma esa licencia sea titular/autorizado por todos los autores de los archivos DRYP.** No se copió código a nuestro repositorio.

## Dictamen
**H12a aprobada para disponibilidad y estructura verificables; ejecución/redistribución aún bloqueadas.** DRYP2 está publicado y tiene un cuerpo de código significativo. Para no duplicar desarrollo se priorizará averiguar sus dependencias/runtime reales, test upstream, licencia/autorización y contratos exportables sobre construir por cuenta propia un sistema nuevo de zona radicular/acuífero.

## Próximas comprobaciones
1. Inspeccionar estáticamente importaciones y configuración del paquete para comparar con Python y Landlab actuales. Cualquier prueba de ejecución debe ser en runner efímero sin secretos, con checksum y alcance de red controlados; no publicar el ZIP ni resultado binario de terceros.
2. Confirmar si DRYP2 permite condiciones iniciales de suelo/vegetación modificables durante el tiempo, y en qué magnitudes. No afirmar emergentismo solo por modelo climático.
3. Resolver la autoridad de la licencia antes de adaptar/copy-paste código a nuestro repositorio.
4. Conservar plan alternativo Landlab-first (H7–H11) que sigue funcional y MIT verificado.

**No se modificó NeuroLab ni se avanzó etapa 1.**
