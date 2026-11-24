# Migración de los laboratorios — registro operativo (2026-11-24)

## Estado y autorización
El usuario aprobó la separación en siete repositorios independientes y la puesta en marcha documental. Se verificaron los siete repositorios públicos con permiso push; todos partían vacíos. WorldLab ya tiene nombre canónico nilo-worldlab. No hay autorización para borrar ramas históricas ni reescribir historial, publicar archivos privados o ejecutar campañas fuera de los protocolos existentes.

## Migración conservadora de las dos líneas activas
Origen: mxlzz/Nilo_public. HEAD observados al preparar este registro (volver a comprobar antes del corte, no congelar a ciegas):
- NeuroLab: docs/neurolab-protocolo-20261120, 4f72af2ea39c515467d3ebf1e013306e0cc14645. PR #103 draft, issue #102. N STOP; G05/G09 abiertos. Consultar ESTADO_Y_CONTINUIDAD.md: H-08b requiere medio original completo; no repetir petición de DATA.zip ni exponer recursos propietarios.
- WorldLab: research/world-foundations-2026-11, 18c66381b6ba36b7e7601de0fa11eb6e5db05e8b. Etapa 7 abierta, etapas 0–6 cerradas provisionalmente en recortes específicos, etapa 8 no superada; consultar última evidencia de la rama, no inferir mundo operativo.
Destinos respectivos: mxlzz/nilo-neurolab y mxlzz/nilo-worldlab, main, vacíos. Intento de crear main con SHA original vía API de GitHub: 409 Git Repository is empty en ambos; ningún ref creado. Entorno de ejecución local: git ls-remote falla por DNS de github.com. No se dispone de una acción de transferencia de objetos Git entre repositorios en el conector. No inicializar destinos con archivos sueltos; no simular historial mediante commits recreados. 

### Paso manual mínimo pendiente del propietario
1. Coordinar pausa de escrituras en los dos chats de origen durante el corte. Verificar que los destinos sigan vacíos. En Settings > Actions > General de ambos destinos, desactivar Actions temporalmente para evitar ejecutar workflows heredados sin auditoría. No modificar permisos de origen.
2. Desde una carpeta de trabajo NUEVA, con Git instalado y credenciales propias del usuario, ejecutar los comandos siguientes (Git Bash/terminal). No hace falta compartir tokens ni secretos con el agente. El push inicial transmite el árbol e historial alcanzable desde cada rama, incluidos archivos heredados de Nilo_public; no transfiere todos los refs, issues/PRs, artifacts, secretos o configuración.
```bash
git clone --bare --single-branch --branch docs/neurolab-protocolo-20261120 https://github.com/mxlzz/Nilo_public.git neurolab-migration.git
git -C neurolab-migration.git rev-parse HEAD
git -C neurolab-migration.git push https://github.com/mxlzz/nilo-neurolab.git HEAD:refs/heads/main
git clone --bare --single-branch --branch research/world-foundations-2026-11 https://github.com/mxlzz/Nilo_public.git worldlab-migration.git
git -C worldlab-migration.git rev-parse HEAD
git -C worldlab-migration.git push https://github.com/mxlzz/nilo-worldlab.git HEAD:refs/heads/main
```
No usar --force, --mirror ni borrar refs. Si Git solicita autenticación, usar el mecanismo local habitual y permisos Contents/Workflows requeridos para el push, nunca publicar credenciales. Si falla, preservar todo y comunicar error exacto. Si el usuario prefiere otra herramienta, exigir equivalencia de SHA y objetos en lugar de copiar ZIP.
3. Verificar HEAD destino igual a SHA clonado, origen sin nuevos commits durante corte, tree y ancestros. Confirmar que documentos, tests y evidencias siguen accesibles. Mantener enlaces al repositorio original para PR/issues/runs/artifacts; no afirmar que se transfirieron. No activar workflows hasta inventariar desencadenantes, dependencias y permisos; secretos no se transfieren. Para NeuroLab conservar restricciones de material original, sin duplicar archivos propietarios.
4. Solo tras verificación: añadir README/AGENTS/STATUS de orientación al nuevo repo sin pisar protocolos, retirar de la punta del árbol archivos/workflows ajenos únicamente tras inventario y justificación, conservar historia original; no reescribir. Mantener ramas originales y PRs como referencia histórica, señalizar nueva fuente canónica y estado de corte en ambos extremos. No modificar funcionalidades durante migración. Ejecutar regresión focalizada segura. Coordinar nuevo acceso a secretos si requerido, no reactivarlos automáticamente. Evitar duplicar instrucciones del protocolo vigente.
5. Reanudar cada chat en su nuevo repo después de la aceptación. Hasta entonces la fuente canónica sigue siendo la rama original. No trabajar simultáneamente sobre dos copias.

## Cinco nuevos laboratorios: inicialización documental completada
Cada uno tiene README.md, AGENTS.md, ROADMAP.md y STATUS.md, verificados por lectura desde GitHub. E0 abierta: revisión de antecedentes; no se completó revisión exhaustiva ni se ejecutaron experimentos.
- BodyLab: https://github.com/mxlzz/nilo-bodylab/tree/b45bb3c0c46b8a16852314feeb5050d9d8af8fb1
- EpistemeLab: https://github.com/mxlzz/nilo-epistemelab/tree/aeb0511e5267fd86f3374cdc21e5080f99fed1ca
- AgencyLab: https://github.com/mxlzz/nilo-agencylab/tree/c3b30201349ef1f8a6c76e1ab099df04440e775e
- SocioLab: https://github.com/mxlzz/nilo-sociolab/tree/f95082644f34e532f5772102e80303c3bb72af44
- Observer: https://github.com/mxlzz/nilo-observer/tree/0275af3fe6ef6403de767d79afd0235f8e8c18a7
No se eligieron tecnologías, licencias ni formatos integradores. Directorio y reglas comunes: [programa Nilo](PROGRAMA_INVESTIGACION_NILO.md).
