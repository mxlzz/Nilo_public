"""Backups recuperables de la partida local. Ningún backup se publica por Git.

Uso: python gestionar_partidas.py backup|restore|list
Nilo debe estar cerrado para restaurar (backup SQLite admite una base abierta).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
from contextlib import closing

HERE = Path(__file__).resolve().parent
DB = HERE/'nilo_mundo.sqlite3'
CONFIG = HERE/'config.env'
BACKUPS = HERE/'backups'
VERSION = (HERE/'VERSION').read_text('utf-8').strip() if (HERE/'VERSION').exists() else 'sin_identificar'


def check_db(path: Path) -> None:
    with closing(sqlite3.connect(f'{path.resolve().as_uri()}?mode=ro', uri=True)) as con:
        valid = con.execute('PRAGMA quick_check').fetchone()
        if not valid or valid[0] != 'ok':
            raise ValueError('La copia de la partida no pasó la comprobación de integridad.')
        if not con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshot'").fetchone():
            raise ValueError('No es una base de datos de Nilo.')


def backup() -> Path:
    if not DB.exists():
        raise FileNotFoundError('Todavía no hay partida en esta carpeta.')
    BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    target = BACKUPS / f'{stamp}_v{VERSION.replace("/", "-")}'
    target.mkdir()
    try:
        # sqlite3.Connection.__exit__ NO cierra la conexión en Python.
        # Usar closing() para liberar lectores WAL también en Windows.
        with closing(sqlite3.connect(f'{DB.resolve().as_uri()}?mode=ro',
                                     uri=True, timeout=10)) as src:
            with closing(sqlite3.connect(target/'nilo_mundo.sqlite3')) as dst:
                src.backup(dst)
        check_db(target/'nilo_mundo.sqlite3')
        if CONFIG.exists():
            shutil.copy2(CONFIG, target/'config.env')
        (target/'MANIFIESTO.json').write_text(json.dumps({
            'version': VERSION,
            'fecha': datetime.now().isoformat(timespec='seconds'),
            'incluye_configuracion': CONFIG.exists()
        },ensure_ascii=False,indent=2),encoding='utf-8')
        return target
    except Exception:
        shutil.rmtree(target,ignore_errors=True)
        raise


def available_backups() -> list[Path]:
    return sorted((p for p in BACKUPS.iterdir() if p.is_dir() and (p/'nilo_mundo.sqlite3').exists()),reverse=True) if BACKUPS.exists() else []



def _windows_exclusive_probe(path: Path) -> None:
    """Distinguir archivos WAL residuales de una conexión SQLite abierta.

    En Windows, CreateFileW sin compartir accesos falla cuando otro proceso
    mantiene un descriptor abierto sobre la base, el WAL o el SHM.
    """
    if os.name != 'nt' or not path.exists():
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                       wintypes.HANDLE)
    create.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = create(str(path), 0x80000000, 0, None, 3, 0, None)
    if handle in (None, ctypes.c_void_p(-1).value):
        error = ctypes.get_last_error()
        if error in (32, 33):  # Sharing violation / lock violation
            raise RuntimeError(
                'Se detectó SQLite abierto por otro proceso. Cerrá Nilo '
                'completamente antes de restaurar.')
        raise ctypes.WinError(error)
    kernel.CloseHandle(handle)


def _prepare_closed_sqlite_for_restore() -> None:
    """No retirar un WAL activo; consolidar WAL residual solo si no hay lectores.

    En Linux/macOS se conserva el rechazo conservador anterior. El gestor
    portable usa Windows, donde el sondeo de handles es específico del SO.
    """
    wal = Path(str(DB) + '-wal')
    shm = Path(str(DB) + '-shm')
    auxiliary = (wal, shm)
    if not DB.exists():
        if any(p.exists() for p in auxiliary):
            raise RuntimeError('Hay archivos SQLite auxiliares sin base original.')
        return
    if os.name != 'nt':
        if any(p.exists() for p in auxiliary):
            raise RuntimeError('Se detectó SQLite activo o sin cerrar. '
                               'Cerrá Nilo completamente antes de restaurar.')
        return
    for p in (DB, *auxiliary):
        _windows_exclusive_probe(p)
    if any(p.exists() for p in auxiliary):
        # Consolidar los cambios pendientes antes de borrar la antigua base.
        with closing(sqlite3.connect(DB, timeout=1)) as con:
            result = con.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
            if result and result[0]:
                raise RuntimeError('El WAL tiene lectores activos; '
                                   'no es seguro restaurar todavía.')
        # Los auxiliares son descartables SOLO tras un checkpoint exitoso,
        # y luego de repetir el sondeo de handles.
        for p in (DB, *auxiliary):
            _windows_exclusive_probe(p)
        for p in auxiliary:
            if p.exists():
                p.unlink()



def restore(folder: Path, restore_config: bool = False) -> None:
    folder=folder.resolve()
    src=folder/'nilo_mundo.sqlite3'
    check_db(src)
    # Rechazar procesos vivos, no confundir un WAL residual con una sesión
    # abierta. El checkpoint previo conserva todos los datos confirmados.
    _prepare_closed_sqlite_for_restore()
    if DB.exists():
        # Crear siempre una copia de seguridad de la partida que se va a reemplazar.
        current = backup()
        print(f'Partida actual resguardada en: {current}')
        # El propio backup también puede haber abierto WAL temporal.
        _prepare_closed_sqlite_for_restore()
    temporary = HERE/'nilo_restauracion_temporal.sqlite3'
    shutil.copy2(src,temporary)
    try:
        check_db(temporary)
        os.replace(temporary,DB)
    finally:
        temporary.unlink(missing_ok=True)
    if restore_config and (folder/'config.env').exists():
        shutil.copy2(folder/'config.env',CONFIG)


def main() -> int:
    parser=argparse.ArgumentParser(description='Respaldar o restaurar una partida local de Nilo')
    parser.add_argument('action',choices=('backup','restore','list'))
    args=parser.parse_args()
    try:
        if args.action=='backup':
            path=backup()
            print(f'\nRespaldo completo: {path}')
            print('Incluye una copia coherente de SQLite y la configuración si estaba presente.')
            return 0
        options=available_backups()
        if not options:
            print('Todavía no existen respaldos en la carpeta backups.')
            return 1
        for i,p in enumerate(options,1):
            details=''
            if (p/'MANIFIESTO.json').exists():
                try:details=' · código '+json.loads((p/'MANIFIESTO.json').read_text('utf-8')).get('version','')
                except (ValueError,OSError):pass
            print(f'{i}. {p.name}{details}')
        if args.action=='list':return 0
        print('\nADVERTENCIA: restaurar sobrescribe el progreso de la partida actual.')
        print('Se guardará automáticamente una copia de la partida actual antes del cambio.')
        chosen=int(input('Número del respaldo a restaurar (0 para cancelar): '))
        if chosen==0:return 0
        if not 1<=chosen<=len(options):raise ValueError('Número no válido.')
        if input('Escribí RESTAURAR para confirmar: ').strip()!='RESTAURAR':
            print('Cancelado.');return 0
        restore(options[chosen-1])
        print('Partida restaurada. config.env no se modificó.')
        return 0
    except (OSError,ValueError,sqlite3.Error,RuntimeError) as exc:
        print('ERROR:',exc)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
