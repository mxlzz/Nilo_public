"""Asistente de primera ejecución para las versiones portables de Nilo.

Nunca mueve ni modifica la instalación de origen. Las credenciales permanecen
locales en config.env y no se imprimen, almacenan en el mundo ni suben a Git.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from migrar import import_from
from interface_prefs import import_settings

HERE = Path(__file__).resolve().parent
MARKER = '.nilo_primera_ejecucion'


def candidates(here: Path) -> list[Path]:
    """Búsqueda superficial y acotada; no recorre el disco ni archivos privados."""
    home = Path.home()
    bases = [here.parent, here.parent.parent, home / 'Desktop', home / 'Documents',
             home / 'Downloads', home / 'OneDrive' / 'Desktop']
    found: list[Path] = []
    seen = {here.resolve()}
    for base in bases:
        if not base.is_dir():
            continue
        try:
            # Solo carpetas hijas inmediatas cuyo nombre empieza con Nilo.
            # Reconoce Nilo-main, Nilo-0.5.9.2.3 y los nombres históricos.
            folders = sorted(
                (p for p in base.iterdir() if p.is_dir()
                 and p.name.casefold().startswith('nilo')),
                key=lambda p: p.name.casefold(), reverse=True,
            )
        except OSError:
            continue
        for path in folders:
            try:
                resolved = path.resolve()
                if resolved in seen:
                    continue
                if not (path / 'nilo.py').is_file():
                    continue
                if not ((path / 'config.env').is_file() or
                        (path / 'nilo_mundo.sqlite3').is_file()):
                    continue
            except OSError:
                continue
            seen.add(resolved)
            found.append(path)
    return found


def parse_path(value: str) -> Path:
    return Path(value.strip().strip('"').strip("'")).expanduser()


def is_yes(value: str, default: bool = False) -> bool:
    value = value.strip().lower()
    return default if not value else value in ('s', 'sí', 'si', 'y', 'yes')


def first_run(prompt=input, here: Path | None = None) -> str:
    here = (here or HERE).resolve()
    if (here / MARKER).exists() or (here / 'nilo_mundo.sqlite3').exists():
        return 'already-configured'
    print('\n=== NILO - PRIMER INICIO ===')
    print('Podés empezar un mundo nuevo o importar una copia del anterior.')
    print('La carpeta anterior no se modifica. Las claves API nunca se muestran.\n')
    old = None
    found = candidates(here)
    if found:
        print('Se encontraron posibles instalaciones anteriores:')
        for i, folder in enumerate(found, 1):
            print(f'  {i}. {folder}')
        print('  0. Elegir otra carpeta (también sirve la letra O)')
        print('  N. No tengo una versión anterior / comenzar desde cero')
        choice = prompt('Elegí una opción [1]: ').strip().lower()
        if not choice:
            old = found[0]
        elif choice.isdigit() and 1 <= int(choice) <= len(found):
            old = found[int(choice) - 1]
        elif choice in ('0', 'o'):
            raw = prompt('Pegá la ruta completa de la carpeta anterior (Enter para cancelar): ').strip()
            if not raw:
                raise ValueError('No se eligió ninguna carpeta. Se canceló la importación.')
            old = parse_path(raw)
        elif choice not in ('n',):
            raise ValueError('Opción no válida. Usá el número de una instalación, 0 para elegir carpeta o N para un mundo nuevo.')
    elif is_yes(prompt('¿Tenés instalada una versión anterior de Nilo? [s/N]: ')):
        raw = prompt('Pegá la ruta completa de su carpeta (Enter para cancelar): ').strip()
        if not raw:
            raise ValueError('No se eligió ninguna carpeta. Se canceló la importación.')
        old = parse_path(raw)

    if old is not None:
        old = old.resolve()
        if old == here or not old.is_dir() or not (old / 'nilo.py').is_file():
            raise ValueError('La carpeta indicada no contiene una instalación anterior válida de Nilo.')
        previous_cfg = old / 'config.env'
        dest_cfg = here / 'config.env'
        if previous_cfg.is_file():
            if not dest_cfg.exists():
                shutil.copy2(previous_cfg, dest_cfg)
                print('\nConfiguración anterior copiada (Gemini/Groq y preferencias).')
            else:
                print('\nYa existe config.env en la carpeta nueva. Se conserva sin sobrescribir.')
        else:
            print('\nNo se encontró config.env en la versión anterior.')

        if import_settings(old, here):
            print('Preferencias visuales de la versión anterior recuperadas.')
        previous_db = old / 'nilo_mundo.sqlite3'
        if previous_db.is_file():
            if is_yes(prompt('¿Querés recuperar UNA COPIA de la partida anterior? [s/N]: ')):
                # import_from usa backup de SQLite, evitando copias inconsistentes de WAL.
                # Siempre se invoca antes de que Nilo cree una partida en este directorio.
                if here == HERE.resolve():
                    import_from(old)
                else:
                    import migrar
                    prev = (migrar.HERE, migrar.DEST_DB, migrar.DEST_CFG)
                    try:
                        migrar.HERE = here
                        migrar.DEST_DB = here / 'nilo_mundo.sqlite3'
                        migrar.DEST_CFG = here / 'config.env'
                        migrar.import_from(old)
                    finally:
                        migrar.HERE, migrar.DEST_DB, migrar.DEST_CFG = prev
                print('Partida copiada y validada. La instalación anterior sigue intacta.')
            else:
                print('Elegiste crear un mundo nuevo; la partida anterior se conserva.')
        else:
            print('No se encontró una partida anterior; se creará un mundo nuevo.')
    else:
        print('Se iniciará un mundo nuevo.')

    config = here / 'config.env'
    if not config.exists():
        template = here / 'config.env.example'
        if template.is_file():
            shutil.copy2(template, config)
            print('Se creó config.env desde la plantilla. Podés agregar claves API después.')
    (here / MARKER).write_text('Configuración de primer inicio completada.\n', encoding='utf-8')
    print('\nConfiguración inicial finalizada. Iniciando Nilo...\n')
    return 'configured'


def main() -> int:
    try:
        first_run()
        return 0
    except (EOFError, KeyboardInterrupt):
        print('\nInicio cancelado; no se inició Nilo.')
        return 1
    except Exception as exc:
        print(f'ERROR de primera configuración: {exc}')
        print('Podés volver a ejecutar INICIAR_NILO.bat. La carpeta anterior no se modificó.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
