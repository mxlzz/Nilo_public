"""Importación no destructiva de partidas de versiones anteriores de Nilo.

La fuente solo se lee; la partida se copia a la nueva instalación mediante
la API de backup de SQLite. No contiene ni publica credenciales.
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
from pathlib import Path

from interface_prefs import import_settings

HERE = Path(__file__).resolve().parent
DEST_DB = HERE / 'nilo_mundo.sqlite3'
DEST_CFG = HERE / 'config.env'


def _valid_folder(path: Path) -> bool:
    return path.is_dir() and (path / 'nilo.py').is_file() and (path / 'nilo_mundo.sqlite3').is_file()


def import_from(source: Path) -> tuple[Path, bool]:
    source = source.expanduser().resolve()
    if not _valid_folder(source):
        raise ValueError('La carpeta de origen debe contener nilo.py y nilo_mundo.sqlite3.')
    if source == HERE.resolve():
        raise ValueError('La carpeta de origen y destino son la misma.')
    if DEST_DB.exists():
        raise FileExistsError('Esta instalación ya tiene una partida. No se reemplazó ningún archivo.')

    src_db = source / 'nilo_mundo.sqlite3'
    try:
        with sqlite3.connect(src_db.as_uri()+'?mode=ro', uri=True, timeout=5) as origin:
            row = origin.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshot'").fetchone()
            if not row:
                raise ValueError('La base de datos de origen no parece una partida válida de Nilo.')
            with sqlite3.connect(DEST_DB, timeout=15) as dest:
                origin.backup(dest)
                check = dest.execute('PRAGMA quick_check').fetchone()
                if not check or check[0] != 'ok':
                    raise ValueError('Falló la validación de la copia de SQLite.')
    except Exception:
        DEST_DB.unlink(missing_ok=True)
        raise

    config_copied = False
    old_config = source / 'config.env'
    if old_config.is_file() and not DEST_CFG.exists():
        shutil.copy2(old_config, DEST_CFG)
        config_copied = True
    import_settings(source, HERE)
    return DEST_DB, config_copied


def main() -> int:
    parser = argparse.ArgumentParser(description='Importar una copia de una partida de Nilo sin modificar el original')
    parser.add_argument('--from', dest='origin', help='Ruta de la carpeta de Nilo anterior')
    args = parser.parse_args()
    print('\nNILO 04 - Importar partida de una versión anterior\n')
    print('Cerrá primero todas las ventanas de Nilo. El original no se modificará.\n')
    if DEST_DB.exists():
        print('Esta carpeta ya tiene una partida. Por seguridad no se sobrescribe.')
        return 2
    if args.origin:
        old = Path(args.origin.strip('"'))
    else:
        possible = [HERE.parent/'Nilo_v2', HERE.parent/'Nilo', HERE.parent.parent/'Nilo_v2', HERE.parent.parent/'Nilo']
        guess = next((path for path in possible if _valid_folder(path)), None)
        if guess:
            print(f'Carpeta detectada: {guess}')
            raw = input('Enter para usarla o pegá otra carpeta: ').strip().strip('"')
            old = Path(raw) if raw else guess
        else:
            raw = input('Pegá la ruta de la carpeta de Nilo anterior: ').strip().strip('"')
            if not raw:
                print('Cancelado; no se modificó nada.')
                return 1
            old = Path(raw)
    try:
        _, copied = import_from(old)
    except (ValueError, FileExistsError, OSError, sqlite3.Error) as exc:
        print('No se pudo importar:', exc)
        return 1
    print('\nPartida copiada y validada correctamente.')
    print('La carpeta anterior conserva su partida original.')
    if copied:
        print('También se copió config.env, incluidas tus preferencias y claves locales.')
    else:
        print('La configuración existente no se modificó.')
    print('Ahora podés iniciar INICIAR_NILO.bat.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
