# H-08b.5 — contraste Wine y decisión sobre el medio original

**Fecha:** 2026-11-24. **Alcance:** contraste acotado de compatibilidad después de [cinco ensayos Win32](H08B_04_ARRANQUE_WIN32_ORIGINAL_20261124.md). El usuario autorizó ejecutar el original remotamente. No experimento N, no intervención en criaturas, no parches del motor.

## Prueba y resultado

[Workflow Wine](../../.github/workflows/neurolab-original-wine.yml), commit `fd236b26b17083554915f9eea03fb104e1e40745`; [CI #45390024315](https://github.com/mxlzz/Nilo_public/actions/runs/45390024315), job 138430963130, SUCCESS como ejecución del diagnóstico. Ubuntu 24.04, Wine 9.0, prefijo win32 aislado, Xvfb con profundidad solicitada de 16 bits, valores de directorios derivados del EXE. Se verificaron SHA256 del ZIP, EXE y GEN y CRC del archivo; se utilizaron los recursos extraídos y configuración temporal. Log ejecutado:

- PASS: exact original input verified.
- BEGIN: original Build 47, Wine win32 prefix, 16-bit X display.
- OBSERVED: original process exited code=0 at sample=1.
- No líneas de error seleccionadas; no se estableció DDE funcional ni se verificó carga del mundo. Prefijo efímero eliminado; no se publicaron archivos propietarios.

**STOP de esta configuración.** La coincidencia de salida 0 en Windows moderno y Wine no identifica la causa. No se comprobó que los cinco DLL cargados por Wine correspondan individualmente a cada fichero extraído; no atribuir la salida a un DLL concreto. No hacer nuevos cambios aleatorios de compatibilidad.

## Nueva dependencia relevante: medio original de instalación

Evidencia primaria sobre Creatures.exe hasheado: cadena `CD Drive` en VA 0x439A08 (file offset 0x37208), valor por defecto `D:` en VA 0x439A14. La función 0x4119D0 busca recursos; rama 0x411AE2–0x411AFA consulta el valor de registro y después construye una ruta alternativa, intenta abrir el recurso en 0x411B86; la rama 0x411AD3 puede terminar sin acudir al CD según argumento. No se ha probado que esta rama se alcance durante el cierre observado ni que sea un mecanismo de verificación de licencia. [Manual de datos original](https://eem.foo/archive/downloads/9fd4?download=true) indica que la instalación en disco duro y presencia del CD son requisitos de uso. DATA.zip contiene el contenido extraído de DATA.Z, pero no es imagen íntegra del CD ni contiene los scripts/manifiesto del instalador y estructura completa del medio. No se puede sustituir ese requisito con archivos ficticios o cambios en el binario.

## Puerta siguiente y criterio de detención

Antes de otro intento, recuperar del usuario el medio completo del CD original (preferiblemente imagen ISO o BIN/CUE, o contenido íntegro con árbol y etiqueta original si no existe imagen). Comprobar compatibilidad entre el ejecutable de ese medio y los hashes de H1–H08a; analizar configuración del instalador y archivos externos a DATA.Z; probar montaje legítimo del CD en el entorno aislado. No asumir que obtener el medio resuelve la salida. No solicitar todavía una licencia/imagen de Windows 98 hasta evaluar lo que aporta el CD completo; si el sistema histórico sigue siendo imprescindible, utilizar un medio legítimo. QEMU remoto ya verificado. No descargar ni publicar imágenes propietarias sin procedencia/autorización. No publicar identificadores de acceso ni nuevos secretos. La intervención se limita a conseguir el medio que el usuario ya posee; los binarios y DATA.zip no se vuelven a pedir.

**Estado:** ejecución autorizada y arranque parcial demostrados; C1 no operativo, mediciones neuronales no iniciadas. N STOP, G05/G09 abiertas. Main intacto, PR103 draft.
