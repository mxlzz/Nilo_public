# Compatibilidad histórica en el repositorio público

La CI pública no necesita acceso al repositorio privado. Verifica seis partidas
**sintéticas**, iniciales y progresadas, de 0.5.9.4.2, 0.6.0 y 0.6.4.
La importación se ejecuta tanto con la referencia pública 0.6.4 inmutable
(`8b7bc69afea1c003d51029f76c592d7b1f85b74b`) como con el runtime 0.7.
Cada importación trabaja sobre copias y comprueba que el original no cambió.

Los seis SQLite proceden del artefacto de CI histórico `13357489405`, generado
sin LLM ni partidas personales, con semillas mundo=7321 y RNG=9821. El ZIP
original se comprobó contra su SHA-256 registrado por GitHub:
`3237b38f90bc0d7e553a810396473337af950c763ec2cf8b4958fbf1a034c3d5`.
Antes de publicar se revisaron todas las tablas y los registros de los seis
SQLite y se compararon sus hashes con el informe de importación original.

`tests/fixtures/baseline_historico_07.zip` contiene únicamente los seis SQLite;
el JSON adjunto documenta tamaño y hash de cada archivo. No contiene código
histórico, configuración, ZIPs de releases, claves ni partidas personales.
`tools/preparar_baseline_publica_07.py` verifica el conjunto exacto de archivos,
sus hashes, integridad SQLite y condiciones de la receta antes de importarlos.

La receta original de generación sigue documentada en
`tools/congelar_baseline_064.py`, como procedencia histórica. Su ejecución
requiere los árboles históricos que deliberadamente no se publicaron.
La CI pública consume las fixtures versionadas y no regenera esos árboles.
Esta verificación no reemplaza una evaluación conductual con un LLM real.
