# H-08b.2 — factibilidad de observación Win32 nativa sin sistema invitado propietario

**Fecha:** 2026-11-24. **Alcance:** prueba sintética de infraestructura de H-08b, no ejecución de C1, no experimento de aprendizaje. H-08b.1 ya estableció QEMU remoto. Se prioriza la alternativa de menor complejidad para intentar arranque y observación del Build 47 auténtico.

## Alternativas evaluadas

- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners): Windows 2022 x64 permite probar un proceso x86 sin obtener una imagen Windows antigua. La sesión disponible y DDE se comprobaron en una prueba real, no se infieren solo de la documentación.
- [ReactOS](https://reactos.org/download/) es libre y compatible en parte con Win32, funciona en QEMU; no es Windows 95/98 ni un oráculo histórico y la compatibilidad C1 no se probó. Mantenerlo como alternativa si es necesario.
- [Documentación de compatibilidad C1](https://www.pcgamingwiki.com/wiki/Creatures), [archivos históricos de soporte](https://eem.foo/ccarchive/Sites/creatures.treesprite.com/Upgrades.html): las ediciones originales de 3.1/95 y compatibilidad NT tienen requisitos diferentes; las actualizaciones del motor NO son equivalentes al Build 47 hasheado. Community Edition modifica comportamiento y compatibilidad; no utilizarla como sustituto histórico.
- Internet Archive puede proporcionar documentación y materiales históricos; una imagen antigua accesible no prueba licencia o autorización. No se descargó una imagen propietaria ni se requiere una licencia antigua para esta fase.

## Prueba ejecutada y verificada

[Workflow Win32 DDE](../../.github/workflows/neurolab-win32-dde.yml), commit `defd8974ce486d4bc1074b2652fcb0dab6966f4b`. [CI #45325543969](https://github.com/mxlzz/Nilo_public/actions/runs/45325543969), job `138214139804`, SUCCESS. Runner `windows-2022`; compilador .NET Framework x86, proceso verificó IntPtr.Size=4; dos hilos con inicialización DDEML, servidor registró servicio sintético, bombeó mensajes, cliente conectó y efectuó XTYP_REQUEST, recibió CF_TEXT y verificó marcador exacto. Log efectivo posterior a ejecución: `PASS: synthetic native x86 Win32 DDE request and response`. Sesión de proceso 2; no interpretar Environment.OSVersion sin manifiesto como versión exacta del host.

**Resultado:** factibilidad de comunicación nativa Win32 DDE en runner PASS sintético. No demuestra que C1 arranque, que su tema Macro funcione, que los datos CHEM sean accesibles o que la cadencia sea equivalente a un PC de 1996. No se ejecutó ni descargó C1 en el runner.

## Puerta de transferencia y ejecución

DATA.zip está en Drive (hash SHA256 `df490a704ae5b6f44016b2ac35e899fe30b7550c7666990edb60c0ebddf025dd`, 14624092 bytes), EXE/GEN identificados en H-08b.0. El conector puede recuperarlo a la sesión de análisis, pero no ofrece una transferencia privada directa al runner ni configuración de Actions secrets. La revisión de metadatos de Drive mostró acceso por enlace con rol writer; no se cambió ese permiso. No publicar URL, ID del archivo, ZIP, imágenes de disco ni credenciales en commits o logs. El ID de acceso debe suministrarse por un secreto configurado por el propietario del repositorio, no por texto de workflow. Un secreto no vuelve privado un archivo que ya es accesible por enlace; recomendar rol lector si el usuario desea cambiarlo. El hash congelado debe validarse antes de cualquier extracción y ejecución.

Primera prueba posterior: archivo privado al job efímero, verificación SHA-256 del ZIP, extracción segura, verificar EXE y GEN, prueba de arranque de una copia desechable del Build 47 con DLLs locales originales; tiempo acotado, sin instalar servicios, sin cambiar componentes del sistema, sin distribuir archivos propietarios. Si falla, registrar error concreto sin parchear binario. Si arranca, verificar detección de ventana y conexión DDE antes de intentar sondeos; ninguna prueba de aprendizaje. El entorno Windows moderno será **prueba de compatibilidad y orden lógico**, no medición histórica de frecuencia. Si requiere otro SO o manifiesto del CD, justificarlo tras el fallo observado.

**Dependencias reales:** propietario configura secret `NEUROLAB_DATA_FILE_ID` en GitHub Actions para el archivo DATA.zip y autoriza específicamente ejecutar el original en runner efímero. No se puede crear dicho secreto con herramientas actuales. Tras consentimiento se activa workflow acotado. N STOP, G05/G09 abiertas; PR103 draft, main y Nilo0.7 intactos.
