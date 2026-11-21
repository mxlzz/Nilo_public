"""Prueba mínima de materia compartida: balances y capacidad; NO simula movimiento.

Los valores son propiedades efectivas en unidades arbitrarias consistentes:
masa, densidad (masa/volumen), volumen de celda. Sin reglas por material.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite, fsum
from typing import Mapping
import json

_EPS = 1e-10


def _positive(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError(f"{name} debe ser un número finito positivo")
    return float(value)


@dataclass(frozen=True)
class Material:
    id: str
    density: float

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError('id de material vacío')
        object.__setattr__(self, 'density', _positive(self.density, 'densidad'))


class MatterGrid:
    """Celdas con inventario de masa por material, sin mezclar químicamente."""

    def __init__(self, width: int, height: int, materials: Mapping[str, Material], cell_volume: float = 1.0):
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            raise ValueError('dimensiones enteras positivas requeridas')
        if not materials or any(k != m.id for k, m in materials.items()):
            raise ValueError('catálogo de materiales inválido')
        self.width, self.height = width, height
        self.materials = dict(materials)
        self.cell_volume = _positive(cell_volume, 'volumen de celda')
        self.cells: dict[tuple[int,int], dict[str,float]] = {}

    def _check_pos(self, pos: tuple[int,int]) -> None:
        if not (isinstance(pos,tuple) and len(pos)==2 and all(type(c) is int for c in pos)
                and 0 <= pos[0] < self.width and 0 <= pos[1] < self.height):
            raise ValueError(f'celda fuera de dominio: {pos}')

    def _check_material(self, material_id: str) -> None:
        if material_id not in self.materials:
            raise ValueError(f'material no registrado: {material_id}')

    def volume_at(self, pos: tuple[int,int]) -> float:
        self._check_pos(pos)
        return fsum(mass / self.materials[mid].density for mid,mass in self.cells.get(pos,{}).items())

    def mass_by_material(self) -> dict[str,float]:
        return {mid:fsum(cell.get(mid,0) for cell in self.cells.values()) for mid in sorted(self.materials)}

    def add_initial(self, pos: tuple[int,int], material_id: str, mass: float) -> None:
        """Solo fuente inicial explícita. Las transferencias posteriores deben conservar masa."""
        self._check_pos(pos)
        self._check_material(material_id)
        mass = _positive(mass, 'masa inicial')
        if self.volume_at(pos)+mass/self.materials[material_id].density > self.cell_volume+_EPS:
            raise ValueError('capacidad de celda excedida')
        cell=self.cells.setdefault(pos,{})
        cell[material_id] = cell.get(material_id,0.0)+mass

    def transfer(self, src: tuple[int,int], dst: tuple[int,int], material_id: str, mass: float) -> None:
        """Movimiento manual atómico; no hay gravedad ni algoritmo de transporte todavía."""
        self._check_pos(src)
        self._check_pos(dst)
        self._check_material(material_id)
        mass = _positive(mass, 'masa a transferir')
        available=self.cells.get(src,{}).get(material_id,0.0)
        if mass > available + _EPS:
            raise ValueError('masa insuficiente en origen')
        if mass > available: # tolerancia de representación, jamás inventar materia
            mass=available
        if src == dst:
            return
        if self.volume_at(dst)+mass/self.materials[material_id].density > self.cell_volume+_EPS:
            raise ValueError('capacidad de destino excedida')
        origin=self.cells[src]
        remaining=available-mass
        if remaining > 0:
            origin[material_id]=remaining
        else:
            del origin[material_id]
        if not origin:
            del self.cells[src]
        dest=self.cells.setdefault(dst,{})
        dest[material_id]=dest.get(material_id,0)+mass

    def snapshot(self) -> str:
        """Snapshot determinista, versionado y con propiedades necesarias para restaurar."""
        data={'version':1, 'width':self.width,'height':self.height,'cell_volume':self.cell_volume,
              'materials':{name:self.materials[name].density for name in sorted(self.materials)},
              'cells':[{'x':x,'y':y,'mass':dict(sorted(m.items()))}
                       for (x,y),m in sorted(self.cells.items())]}
        return json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False)

    @classmethod
    def from_snapshot(cls, raw: str) -> 'MatterGrid':
        data=json.loads(raw)
        if data.get('version') != 1:
            raise ValueError('versión de snapshot no compatible')
        mat={name:Material(name,density) for name,density in data['materials'].items()}
        grid=cls(data['width'],data['height'],mat,data['cell_volume'])
        for cell in data['cells']:
            for material_id,mass in cell['mass'].items():
                grid.add_initial((cell['x'],cell['y']),material_id,mass)
        return grid
