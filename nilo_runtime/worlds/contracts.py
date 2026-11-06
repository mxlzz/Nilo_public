"""Contratos descriptivos y de generación: independientes de la isla y el agente.

Una implementación nueva aporta un WorldGenerator compatible con make_world;
este contrato no la registra, no modifica las leyes y no añade campos a los saves.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any, runtime_checkable


@dataclass(frozen=True, slots=True)
class WorldDefinition:
    """Geometría y propiedades declaradas del ENTORNO, no saber del agente."""

    environment_id: str
    generator_version: int
    width: int
    height: int
    levels: tuple[str, ...]
    terrain_symbols: frozenset[str]
    passable_symbols: frozenset[str]
    resource_symbols: frozenset[str]
    site_positions: tuple[tuple[str, int, int, int], ...]

    def __post_init__(self) -> None:
        if not self.environment_id or self.generator_version < 1:
            raise ValueError("Identidad o versión de generador inválida.")
        if self.width <= 0 or self.height <= 0 or not self.levels:
            raise ValueError("Dimensiones o niveles de mundo inválidos.")
        if len(self.levels) != len(set(self.levels)):
            raise ValueError("Niveles del mundo duplicados.")
        if not self.passable_symbols <= self.terrain_symbols:
            raise ValueError("Símbolos transitables sin definición de terreno.")
        if not self.resource_symbols <= self.terrain_symbols:
            raise ValueError("Símbolos de recursos sin definición de terreno.")
        if any(len(ch) != 1 for ch in self.terrain_symbols):
            raise ValueError("Símbolos de terreno no unitarios.")
        if len({row[0] for row in self.site_positions}) != len(self.site_positions):
            raise ValueError("Identificadores de sitios duplicados.")
        for name, x, y, z in self.site_positions:
            if (not name or not 0 <= x < self.width or
                    not 0 <= y < self.height or str(z) not in self.levels):
                raise ValueError(f"Sitio fuera del dominio del mundo: {name!r}")

    def describe(self) -> dict[str, Any]:
        """Copia legible para diagnóstico, no es una mutación del save."""
        return {
            "environment_id": self.environment_id,
            "generator_version": self.generator_version,
            "width": self.width, "height": self.height,
            "levels": list(self.levels),
            "terrain_symbols": sorted(self.terrain_symbols),
            "passable_symbols": sorted(self.passable_symbols),
            "resource_symbols": sorted(self.resource_symbols),
            "site_positions": [
                {"name": name, "x": x, "y": y, "z": z}
                for name, x, y, z in self.site_positions
            ],
        }


@runtime_checkable
class WorldGenerator(Protocol):
    """Puerto de generación; otro entorno debe implementar solo su propia ley."""

    @property
    def definition(self) -> WorldDefinition: ...

    def generate(self, seed: int) -> dict[str, Any]: ...
