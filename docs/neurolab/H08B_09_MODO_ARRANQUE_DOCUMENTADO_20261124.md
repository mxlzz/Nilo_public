# H-08b.9 — modo de arranque documentado

Fecha 2026-11-24. Se parte de la secuencia observada en [H-08b.8](H08B_08_TRAZA_INICIALIZACION_20261124.md). Objetivo acotado: conseguir sesión observable del mismo ejecutable original, no resolver un problema genérico de instalación.

## Hipótesis discriminante

Las dos condiciones comprobadas en el objeto de línea de comandos MFC son coherentes con los flags de ejecución OLE: [CCommandLineInfo, Microsoft](https://learn.microsoft.com/en-us/cpp/mfc/reference/ccommandlineinfo-class?view=msvc-170). La rama anterior al cierre contiene operaciones de registro del programa: las cadenas de datos referenciadas incluyen UninstallString y la clave de desinstalación, Patch, Build ID y Build type. No prueba fallo de licencia. La configuración publicada del producto comercial [SteamDB, opción alternativa C1](https://steamdb.info/app/1818340/config/) especifica Creatures.exe -embedding. Esta es una hipótesis documentada de lanzamiento, no modificación de flags internos ni parche. Se conserva CD genuino montado, directorios y DLL originales, ninguna clave de privilegios modificada.

## Prueba

[CI #45448765821](https://github.com/mxlzz/Nilo_public/actions/runs/45448765821), job 138639737883, script commit e2f8e472cb093cb78d70f6c25e479100bdcead5b, workflow commit 061c365e86d503cfd43f015c131c6fb3b22cec13. Mismo ZIP/EXE/GEN verificados, original ISO montada CDRom CDFS, configuración temporal como H-08b.7. Único cambio deliberado al lanzamiento: argumento documentado. Resultado: ventana principal visible clase Afx y título Creatures, diálogo Tip of the Day con instrucciones de hatchery. Ensayo terminó de manera controlada al detectar modal; retirada de rutas, DLL, ISO y archivos confirmada. Esto establece arranque de interfaz, NO ciclo mundial activo, DDE de datos, criatura ni traza cerebral todavía.

## Siguiente gate

Cerrar exclusivamente diálogo de bienvenida reconocido por PID, clase y título y botón Close; consultas CAOS de solo lectura: constante 123, cantidad de Norns y Grendels; referencias [interfaz DDE](https://sheeslostknowledge.blogspot.com/2014/02/connecting-to-creatures-dde-interface.html) y [CDR](https://double.nz/creatures/brainutilities.htm). [CI #45449002204](https://github.com/mxlzz/Nilo_public/actions/runs/45449002204) en curso al escribir. Si el mundo no contiene Norns, utilizar procedimiento documentado de nacimiento desde un genoma verificado en copia desechable, antes de instrumentar química/cerebro. No atribuir propiedades temporales al host moderno; G05/G09 abiertas y N STOP. PR103 draft, main intacto.

## Resultado de lectura CAOS

[CI #45449002204](https://github.com/mxlzz/Nilo_public/actions/runs/45449002204), job 138640600957: POKE aceptado, REQUEST error16386, el motor mostró que el observador había enviado un separador final redundante (el propio C1 agrega delimitador y endm). Se corrigió el observador, no el ejecutable, commit `eba10ede61b10f8d35a465b0d2c77d58f5d49a94`. [CI #45449178994](https://github.com/mxlzz/Nilo_public/actions/runs/45449178994), job 138641244763: diálogo Tip cerrado, ventana principal, consulta constante 123 exacta (4 B), Norns=0 y Grendels=0 (2 B cada respuesta). PASS de comunicación real con C1 en el entorno remoto. No extrapolar a frecuencia del mundo ni aprendizaje. Todos los recursos temporales retirados.

## H-08b.10: primer individuo controlado, preregistro operativo

[Commit f051526728c461f0f6e1eb036f90c23567f97e95](https://github.com/mxlzz/Nilo_public/commit/f051526728c461f0f6e1eb036f90c23567f97e95) incorpora una única creación controlada mediante NEW: CREA (documentada en [CDN](https://lisdude.com/cdn/76.html)), copia desechable byte a byte de dad1.gen, moniker NL01, sexo1, mundo originalmente sin Norns, ubicación x2408 y870 (la rutina original de Hatchery.exe SHA256 dcb324da6ca3cc038e94eabcd3b0e40337bb23d5c75f1ccafc5b42623a4f5814 genera x=2408+40*índice en 0x4039A7 y cadena mvto %d 870). Nacimiento directo NO equivale a incubación ordinaria. No reintentar la macro mutante si respuesta incierta. Verificar número de Norns=1, moniker estable antes/después de cada ronda, química 49/50/51/54/55 y célula Decision0 tipo0, 3 rondas con latencias por consulta. Sin estímulos ni inferencia intratick; los datos serían sondeos secuenciales, no snapshots atómicos. [CI #45449497913](https://github.com/mxlzz/Nilo_public/actions/runs/45449497913) aún en curso al registrar esta nota.
