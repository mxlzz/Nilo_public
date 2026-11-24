# H-08b.0 — inspección del contenido DATA.Z extraído y alternativas de observación

**Fecha:** 2026-11-24. **Alcance:** preparación de factibilidad H-08b según [gate vigente](H08B_GATE_FACTIBILIDAD_TRAZA_DINAMICA_20261122.md); NO ejecución del original, NO evidencia dinámica, NO reactivación N. La pregunta sigue siendo distinguir orden y latencia efectivos de señales de refuerzo en un individuo real; no reconstruir la instalación por sí misma.

## Evidencia primaria inspeccionada

Archivo DATA.zip suministrado por el usuario en Drive/neurolab, procedente según el usuario del contenido extraído de DATA.Z del CD. SHA256 `df490a704ae5b6f44016b2ac35e899fe30b7550c7666990edb60c0ebddf025dd`, tamaño 14624092 bytes, 1163 entradas de archivo, 37691719 bytes descomprimidos, CRC de todas las entradas correcto mediante ZipFile.testzip(). No confundir integridad con autenticidad independiente del CD completo.

- Creatures/Creatures.exe: 387072 bytes, SHA256 `548a8388660e8441e391472258a30af5e57fdbb3567056916eae48ea625460d7`.
- Creatures/Genetics/dad1.gen: 10001 bytes, SHA256 `e2bb4ccf6a4081a128c6c9ffc6eb233452d416717ceef47e78820ca3a152ddd4`.
- Ambos hashes son idénticos a H1–H08a. Version.txt: Creatures Build 47; Build.txt: US Version. El contenido no es un ejecutable parcheado de Community Edition.
- Directorios por número de archivos: Images 439, Body data 340, Sounds 248, raíz Creatures 88, Hatchery 22, Genetics 16 (14 GEN y 2 GNO), Backup 1, TempBu 1, Palettes 1, Dlls 7. ZIP no incluye entradas de directorio vacías; Macros no está representado, aunque el EXE referencia Macros. No se demuestra que todas las dependencias de instalación estén satisfechas.
- World.sfc, Eden.sfc y Backup/World.sfc: 177269 bytes cada uno, los tres SHA256 `5383f806c62d1ad553219f2cbc185bf83b4434c0a8f6a7b1dbd7ab9260365c07`. No se abrió ni modificó ningún estado de mundo.
- Dlls: MFC40.DLL, CTL3D32.DLL, Wing32.dll, MSVCRT40.DLL, MSVCRT.DLL, MSVCIRT.DLL, MFC42.DLL.

## Dependencias estáticas y limitación de ejecución

GNU objdump -p sobre miembros PE extraídos temporalmente sin ejecutarlos:
- Creatures.exe: WING32.dll, DSOUND.dll, MFC42.DLL, MSVCRT.dll, KERNEL32.dll, USER32.dll, GDI32.dll, ADVAPI32.dll, SHELL32.dll, MSVCIRT.dll.
- Science Kit.exe: DSOUND.dll, MFC42.DLL, MSVCRT.dll, KERNEL32.dll, USER32.dll, GDI32.dll, ADVAPI32.dll, OLEAUT32.dll.
- Hatchery.exe: mismo conjunto que Science Kit.
- Launcher.exe: MFC40.DLL, MSVCRT40.dll, KERNEL32.dll, USER32.dll, GDI32.dll, ADVAPI32.dll, SHELL32.dll.

Wing32 y bibliotecas de runtime antiguas relevantes están en el ZIP; los restantes imports directos corresponden a bibliotecas del sistema Windows. Su compatibilidad y dependencias transitivas no se probaron. Strings del EXE: Main Directory, Millennium Interactive, Genetics Directory, Image Directory, Palette Directory, Macro Directory, Sound Directory, SetCurrentDirectoryA. Science Kit y Hatchery contienen avisos de fallback al directorio actual si no localizan Creatures. **No demuestra que el motor arranque sin registro ni CD, o sin instalador.** Entorno local Linux sin wine/wine64/qemu-system-i386/dosbox localizados; no ejecutar ni instalar software para resolverlo en esta fase.

## Hallazgo útil para el diseño experimental: observación nativa existente

Science Kit.exe del ZIP SHA256 `6ee5b07ad9dc3dbcbac7141eb7e6e2f1f4d73ba804994a698e3695731d8db9d8`. Extracción de cadenas ASCII: `dde: getb monk`, `dde: cell 6 var0 0,`, `dde: putv chem %d,`, consultas específicas 54 y 55. Creatures.exe contiene temas Macro, BrainActivity, BrainWiring, SysInfo, Vivarium e imports DdeInitializeA, DdeNameService, DdeCreateDataHandle, etc. Demuestra presencia de interfaz DDE y uso de consultas por la herramienta incluida; NO demuestra todavía conectividad, formato de respuesta o frecuencia de muestreo en este build.

Chemicals.txt tiene 5900 bytes: lectura estática de registros con longitud uint16 little-endian arroja 514 entradas, primeros 256 nombres; hay campos vacíos adicionales. Nombres por índice 49 REWARD, 50 PUNISHMENT, 51 reinforcement, 52 ConASH, 53 DecASH1, 54 RewardEcho, 55 PunishEcho, 70 DecASH2. Los textos descriptivos adyacentes son coherentes con la generación de reinforcement por ambos tipos de refuerzo y con un eco más duradero destinado, entre otros fines, a facilitar la monitorización. No confundir eco con señal instantánea ni usarlo para inferir un orden intratick. No se atribuye un offset universal a las descripciones hasta comprobar el lector del recurso.

Alternativas existentes (consulta 2026-11-24):
- [CDR Brain Utilities](https://double.nz/creatures/brainutilities.htm): BrainViewer lee .EXP con conexiones y STW/LTW/strength individuales, BrainCellMonitor consulta DDE CELL (salida, estado y sumas por tipo de dendrita), ChemMonitor lee química aproximadamente cada medio segundo; BrainActivity actualiza aproximadamente cada segundo. Versiones específicas de C1, no se descargaron o ejecutaron sus binarios.
- [CAOS Docs](https://www.caoschaos.com/docs/index.html): documentación de comandos C1, confirmar gramática y respuesta con la edición real.
- [C1 Community Edition](https://lisdude.com/Creatures/Community/C1/): ofrece cambios de compatibilidad y velocidad; NO sustituir nuestro Build 47 como oráculo histórico.
- [openc2e](https://openc2e.github.io/): implementación alternativa abierta; útil como referencia independiente, no evidencia de comportamiento del original.

## Decisión y siguiente unidad

**H-08b.0 inventario estático COMPLETO / runtime pendiente.** Ya hay recursos principales de motor, hatchery, mundo, genética, sonidos, imágenes y DLLs. No pedir de nuevo EXE, GEN ni DATA.Z. Priorizar una prueba de arranque aislada y sin modificaciones del binario, usando una copia desechable de los archivos y entorno Windows compatible (VM si disponible); bibliotecas del CD locales al programa cuando proceda, no reemplazar DLL del sistema. Si el arranque falla por registro o CD, recuperar únicamente manifiesto/script original de instalación y mensaje de error; no improvisar claves ni usar parches de motor como evidencia equivalente.

Primera observación posterior a arranque y autorización: prueba de lectura DDE de identificación de un Norn, concentraciones 49/50/51/54/55 y una célula válida del lóbulo Decision, con marcas temporales de inicio y fin de cada consulta; verificar límites de resolución, muestras perdidas y efectos del observador antes de cualquier intervención. Usar Science Kit como contraste inicial. Los observadores históricos no garantizan acceso a CHEM0..3 del lóbulo ni a los límites de cada invocación; si el objetivo intratick no se alcanza, valorar traza selectiva de H-08a, no declarar G-H6-CLOCK efectivo a partir de sondeos. No ejecutar binarios externos ni el original en esta intervención.

Cierre: nueva evidencia primaria habilita preparar arranque, no demuestra ejecución ni fidelidad dinámica. NR01 y G05-NX01 STOP, confirmaciones intactas; G05/G09 abiertas. PR103 draft, main/Nilo0.7 intactos. No publicar archivo, DLLs, recursos ni ejecutables propietarios.
