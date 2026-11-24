# H-08b.6 — identificación y montaje de la imagen completa del CD

**Fecha:** 2026-11-24. **Alcance:** recuperar el medio original aportado por el usuario; contrastar la dependencia del CD detectada en [H-08b.5](H08B_05_CONTRASTE_WINE_Y_MEDIO_ORIGINAL_20261124.md). No sustituir el motor ni ejecutar instaladores por inferencia.

## Transferencia y huellas

El usuario configuró el segundo secreto para el ZIP completo. El primer intento de inventario (sin secreto) quedó bloqueado; el segundo [CI #45446481434, attempt 2](https://github.com/mxlzz/Nilo_public/actions/runs/45446481434) terminó SUCCESS. ZIP 591498236 bytes, SHA256 `91805784212380b804ec5c3889f2524ff358379c6a0a964e5dadba147c5498af`, 8 archivos, 591497068 B descomprimidos y CRC de todas las entradas correcto. Contiene `Creatures.iso`, no BIN/CUE: 591384576 bytes; descriptor ISO9660 sector16, sector 2048 B, etiqueta CREATURES, raíz LBA23.

[CI Windows de montaje #45447141306](https://github.com/mxlzz/Nilo_public/actions/runs/45447141306), commit `f418f84b4a0810ac3b54362dee11fd052b45c330`: se volvió a verificar la huella ZIP y se obtuvo SHA256 de ISO `555ac57e00d2080268da75ef6063708a7ad20f56f9fd79f0507ab3505c91b297`. Montaje **ReadOnly, CDRom, CDFS, etiqueta Creatures** confirmado. Desmontaje y eliminación del medio temporal confirmados. No se ejecutó ningún archivo del disco en estos dos inventarios.

## Estructura relevante

Raíz: AUTORUN.EXE, AUTORUN.INF, AUTORUN.ICO, CREATURE.11, HELP4YOU, INSTALL, INTRO, MSREG. La carpeta INSTALL contiene DirectX y la distribución InstallShield, SETUP.EXE (47616 B), SETUP.INS (61497 B), SETUP.PKG (19112 B), DATA.Z (16262549 B, SHA256 `0854dc449cd6b7fbb7584019c21d2d95249db6d10d8810e335b350ce2448d6ed`). CREATURE.11 incluye CREATURE, WIN32S, WINDOWS, INI, INTRO y un instalador distinto; no mezclarlo con Build47 sin cotejar versiones. INTRO contiene los vídeos, no necesarios para inferir actividad cerebral. La clasificación completa de formatos PE/NE e instrucciones de instalación queda pendiente.

Este inventario verifica integridad y estructura, no certifica de manera independiente el origen comercial del medio ni que todos los archivos de DATA.Z correspondan byte a byte al ZIP de instalación extraído previamente.

## Siguiente contraste preregistrado en código

`h08b_mounted_launch.py` (commit `42739c0441e1eb9b4cc6a898c0c9913ae0ffc312`) reutiliza preparación y observación del original. [Workflow de lanzamiento con CD](../../.github/workflows/neurolab-mounted-launch.yml) commit `f35c4318f235c9766ebb8dfb477d83c6df60c43f` monta el medio verificado, configura temporalmente `CD Drive` y ejecuta el EXE hasheado de DATA.zip en runner Windows. El formato sin barra final (letra y dos puntos) está respaldado por inspección local de bytes del EXE: 0x439A14 = D:, 0x439A04 = barra inversa, 0x4337C0 = Genetics, consulta en 0x411AFA con argumento 1 (HKLM32), concatenación posterior. No se modifica ninguna condición ni validación del motor. Comparar con arranque por defecto H-08b.4 intento4. No afirmar que CD sea la causa hasta observar diferencia. CI #45447365541 en curso al registrar esta unidad. No se publica ISO, ZIP, ejecutable o identificadores de acceso.

N STOP, G05/G09 abiertas, PR103 draft y main intacto.
