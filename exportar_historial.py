"""Exporta toda la historia registrada, sin modificar la partida ni las claves."""
from __future__ import annotations
import json, sqlite3, datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
DB=HERE/'nilo_mundo.sqlite3'

def main():
    if not DB.is_file():raise SystemExit('No hay partida para exportar en esta carpeta.')
    destination=HERE/'exportaciones'
    destination.mkdir(exist_ok=True)
    target=destination/('Nilo_historial_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.jsonl')
    connection=sqlite3.connect(f'file:{DB.as_posix()}?mode=ro',uri=True)
    try:
        with target.open('w',encoding='utf-8') as out:
            try:
                cursor=connection.execute('SELECT seq,category,item_id,simulated_at,real_at,payload FROM history ORDER BY seq')
            except sqlite3.OperationalError:
                raise SystemExit('Esta partida no tiene aún tablas de historial. Iniciá Nilo 05.2 una vez.')
            for seq,category,item_id,sim_time,real_time,payload in cursor:
                entry={'secuencia':seq,'categoria':category,'id':item_id,'momento_simulado':sim_time,
                       'momento_real':real_time,'contenido':json.loads(payload)}
                out.write(json.dumps(entry,ensure_ascii=False)+'\n')
            for revision,category,item_id,captured,payload in connection.execute(
                'SELECT revision,category,item_id,captured_at,payload FROM history_revisions ORDER BY revision'):
                out.write(json.dumps({'revision':revision,'categoria':category,'id':item_id,
                    'capturado_en':captured,'contenido':json.loads(payload)},ensure_ascii=False)+'\n')
    finally:connection.close()
    print('Historial exportado:',target)
if __name__=='__main__':main()
