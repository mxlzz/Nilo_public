# NeuroLab — E09: preservación adicional de evidencia experimental (22/11/2026)

**Operación realizada, no solo plan:** se descargaron artefactos oficiales de GitHub Actions, se verificaron hashes SHA-256 localmente, se comprobaron los nombres de las entradas ZIP y se copiaron a un almacenamiento Drive del usuario para evitar depender solo de los 90 días de Actions. **No** se subieron archivos originales propietarios de *Creatures* al repositorio. Inventario previo: [E09.01/E09.07](E09_01_07_PRESERVACION_EVIDENCIAS_20261122.md).

**Ubicación de las copias:** carpeta Drive de trabajo de NeuroLab, bajo control de la cuenta del usuario. Los enlaces/IDs completos se conservan en la ficha *privada* de NeuroLab en Notion; **deliberadamente no se enlaza desde GitHub público la carpeta Drive**, que también contiene archivos originales del juego ajenos a los resultados sintéticos. Este registro público fija huellas, procedencia y nombres para que se puedan verificar los bytes recuperados. No se cambiaron permisos de Drive.

| Nombre del ZIP respaldado en Drive | Fuente Actions | ZIP SHA-256 | Bytes ZIP |
|---|---|---|---:|
| `I3c7e_factorial_CI44969153930_20261122.zip` | [run 44969153930 / artifact 14733290218](https://github.com/mxlzz/Nilo_public/actions/runs/44969153930) | `bbd0ad8d9c87f263f5272dbcc4d0c2c65a6dbc8e56c1a9662a4d6230c7cef578` | 1 480 338 |
| `I3c7f_persistencia_CI44970236994_20261122.zip` | [run 44970236994 / artifact 14733312090](https://github.com/mxlzz/Nilo_public/actions/runs/44970236994) | `ad7f5b1fa7634c970dde8884debd05c7b818000b6ee10db023cec546b5bdc126` | 1 491 014 |
| `I3c7g_horizonte_CI44970705424_20261122.zip` | [run 44970705424 / artifact 14733194016](https://github.com/mxlzz/Nilo_public/actions/runs/44970705424) | `ee5144c19af23a809d7b40415b6abb7ace8734f573098a2933f252df565ab9d2` | 1 860 882 |
| `I3c7h_contingencia_CI44986258314_20261122.zip` | [run 44986258314 / artifact 14739997041](https://github.com/mxlzz/Nilo_public/actions/runs/44986258314) | `9605bdaf0ad7955d3209c24564275084f6a074f740e1df76b9c3e59c6234bd4e` | 6 880 751 |
| `I3c7i_ablacion_CI44987034290_20261122.zip` | [run 44987034290 / artifact 14739729195](https://github.com/mxlzz/Nilo_public/actions/runs/44987034290) | `3aaa4e8492f5de84bbd3193972a19870668e6c65133921f8d4d35668f4c7c6bc` | 43 779 |
| `I3c7k_transferencia_CI44987744410_20261122.zip` | [run 44987744410 / artifact 14740013286](https://github.com/mxlzz/Nilo_public/actions/runs/44987744410) | `d8de45c2c7e30aba1db7fa93b81ccfb2ecace1a9d50fe5f934e8b7cae63a31a5` | 10 412 |
| `E09-TAB1_20261122_CI45028224155.zip` | [run 45028224155 / artifact 14756368469](https://github.com/mxlzz/Nilo_public/actions/runs/45028224155) | `01fee34891b2802b4fc5e55c9e27c04bf62c1e17ba97d14accaedf6bfedf3348` | 1 115 |
| `E09_TAB2_CI45028560329_20261122.zip` | [run 45028560329 / artifact 14756592272](https://github.com/mxlzz/Nilo_public/actions/runs/45028560329) | `1e3c8adf39e630e9f190dc13981da93f4c3d7362023c5403fa211d99aaa2e2ba` | 936 |

## Verificaciones independientes realizadas

1. SHA256 de los ocho **ZIP descargados** coincide byte a byte con el digest de artefacto comunicado por Actions. Se inspeccionaron sus rutas internas: `i3c7e.json`, `i3c7g.json`, `i3c7h.json`, `i3c7i.json`, `i3c7k.json`, informes `summary.json` y manifiestos internos; TAB1/TAB2 incluyen JSON y `full.sha256`.
2. SHA256 de JSON interno independiente, contrastado con informes originales:
   - I3c7e `i3c7e.json`: `193ef109e214d33b9779611f1757d3bf23781755d38a0212778ed4269748752c`.
   - I3c7g `i3c7g.json`: `128e92df48b749c046fb9e1b02fce3beb54f4c8b82ed814b067a7c8d0c215d78`.
   - I3c7h `i3c7h.json`: `d723c4a590c0428e13b175c39cd9028c69ed5b714d000f46ada61717eebe925e`.
   - I3c7i `i3c7i.json`: `e6a30b3c2271a87b7404e4c0a9544f41c5ba0d265f946c8ece188fcc93952b5d`.
   - I3c7k `i3c7k.json`: `d67d77d09844ab6699d3e2d56434f21b91d56fb79fb05c882cdd5ea9f4b4fccf`.
3. Google Drive confirmó **éxito de carga, nombre, bytes y parent de la carpeta de los ocho ZIP** mediante lecturas de metadatos posteriores. Esta prueba NO es un nuevo cálculo SHA de los bytes descargados nuevamente desde Drive; para auditoría íntegra futura, volver a descargarlos y comparar con los hashes anteriores.

## Estado de preservación

- **Resueltos por duplicación:** ocho artefactos estratégicos de E09, incluidos los JSON crudos antes efímeros de e/g/h/i/k y sus antecedentes de persistencia.
- **Ya permanentes:** 48 blobs de resultados en `docs/neurolab/resultados/` (revisión de árbol anterior).
- **No resuelto globalmente:** NO se archivaron todos los artefactos de todas las cientos de variantes exploratorias; algunos siguen solo en Actions. Un «archivo de evidencia completo sin pérdidas» sería una afirmación falsa.
- **Vulnerabilidades de preservación:** Drive admite modificación o borrado por usuarios con permisos; el SHA versionado detectará alteraciones, no las impedirá. No se cambió la política de permisos. Los originales EXE/GEN no se redistribuyen.

**Decisión:** base suficiente para un cierre honesto de las conclusiones centrales de E09; conservar la brecha de evidencia de corridas secundarias como limitación del proyecto. No seguir descargando artefactos por rutina sin indicar qué conclusión depende de ellos.
