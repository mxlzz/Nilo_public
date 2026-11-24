# H38.0 — Incidencia de definición CI, no resultado físico

2026-11-23. [Primera ejecución 45299168169](https://github.com/mxlzz/Nilo_public/actions/runs/45299168169) terminó failure con **cero jobs**. La definición YAML incluía `run: python -m pip install --only-binary=:all: pybullet...`; el segundo dos puntos seguido de espacio invalida el scalar YAML. Se sustituyó únicamente por bloque `run: |` (commit 9dcd1f4309d94940b87c8691792718a870f6060b). No se modificaron script, física, versiones, criterios ni preregistro. El primer fallo no aporta evidencia a H38.
