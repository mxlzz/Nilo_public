# H-08b.9 — modo de arranque documentado

Fecha 2026-11-24. Se parte de la secuencia observada en [H-08b.8](H08B_08_TRAZA_INICIALIZACION_20261124.md). Objetivo acotado: conseguir sesión observable del mismo ejecutable original, no resolver un problema genérico de instalación.

## Hipótesis discriminante

Las dos condiciones comprobadas en el objeto de línea de comandos MFC son coherentes con los flags de ejecución OLE: [CCommandLineInfo, Microsoft](https://learn.microsoft.com/en-us/cpp/mfc/reference/ccommandlineinfo-class?view=msvc-170). La rama anterior al cierre contiene operaciones de registro del programa: las cadenas de datos referenciadas incluyen UninstallString y la clave de desinstalación, Patch, Build ID y Build type. No prueba fallo de licencia. La configuración publicada del producto comercial [SteamDB, opción alternativa C1](https://steamdb.info/app/1818340/config/) especifica Creatures.exe -embedding. Esta es una hipótesis documentada de lanzamiento, no modificación de flags internos ni parche. Se conserva CD genuino montado, directorios y DLL originales, ninguna clave de privilegios modificada.

## Prueba

[CI #45448765821](https://github.com/mxlzz/Nilo_public/actions/runs/45448765821), job 138639737883, script commit e2f8e472cb093cb78d70f6c25e479100bdcead5b, workflow commit 061c365e86d503cfd43f015c131c6fb3b22cec13. Mismo ZIP/EXE/GEN verificados, original ISO montada CDRom CDFS, configuración temporal como H-08b.7. Único cambio deliberado al lanzamiento: argumento documentado. Resultado: ventana principal visible clase Afx y título Creatures, diálogo Tip of the Day con instrucciones de hatchery. Ensayo terminó de manera controlada al detectar modal; retirada de rutas, DLL, ISO y archivos confirmada. Esto establece arranque de interfaz, NO ciclo mundial activo, DDE de datos, criatura ni traza cerebral todavía.

## Siguiente gate

Cerrar exclusivamente diálogo de bienvenida reconocido por PID, clase y título y botón Close; consultas CAOS de solo lectura: constante 123, cantidad de Norns y Grendels; referencias [interfaz DDE](https://sheeslostknowledge.blogspot.com/2014/02/connecting-to-creatures-dde-interface.html) y [CDR](https://double.nz/creatures/brainutilities.htm). [CI #45449002204](https://github.com/mxlzz/Nilo_public/actions/runs/45449002204) en curso al escribir. Si el mundo no contiene Norns, utilizar procedimiento documentado de nacimiento desde un genoma verificado en copia desechable, antes de instrumentar química/cerebro. No atribuir propiedades temporales al host moderno; G05/G09 abiertas y N STOP. PR103 draft, main intacto.
