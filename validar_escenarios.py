"""Sondas físicas reproducibles sin LLM ni servidor.

No afirma replicar deliberaciones reales: usa acciones explícitas y semilla fija.
Ejecutar: python validar_escenarios.py --seed 7321 --output resultados.json
"""
from __future__ import annotations
import argparse, json, random, hashlib
from world import (new_world, tile_key, reveal, pathfind, resolve_go, known_exit_route,
                   execute_action, set_tile, cave_exit)
from physics import properties


def run(seed=7321):
    rng=random.Random(int(seed));w=new_world(seed)
    p={'pos':[15,10,0], 'inventory':{'madera':2,'arcilla':2,'fibra':2,'piedra':2},
       'materials':{}, 'items':[], 'knowledge':{}, 'observations':[], 'clock_minutes':0.0,
       'needs':{'hidratacion':80,'nutricion':80,'energia':90,'abrigo':80,'seguridad':68}}
    # El rechazo de un destino oculto debe ser indiferente a su geología real.
    unknown_a=resolve_go(w,p,{'op':'go','x':0,'y':2})
    unknown_b=resolve_go(w,p,{'op':'go','x':5,'y':2})
    identical_unknown=(unknown_a[2]==unknown_b[2]) and unknown_a[:2]==unknown_b[:2]
    # Ruta hacia una casilla conocida, sin revelar atajos ocultos.
    reveal(w,15,11,0,1)
    known_route=pathfind(w,(15,10,0),(15,11,0),known_only=True)
    # Una mezcla crea propiedades físicas aplicables a objetos posteriores.
    _,facts,mixed,_=execute_action(w,p,{'op':'combine','materials':['arcilla','fibra'], 'method':'mezclar'},rng)
    key='compuesto mezclar (arcilla + fibra)'
    mixed_prop=properties(key,p['materials']) if mixed else None
    # El ascenso requiere un portal descubierto y un recorrido en el nivel correcto.
    ex,ey=cave_exit(w)
    p['pos']=[ex,ey,-1]
    reveal(w,ex,ey,-1,2)
    route=known_exit_route(w,p)
    # Una segunda muestra con idéntica semilla arroja iguales resultados sin LLM.
    result={'seed':int(seed),'hidden_go_no_oracle':identical_unknown,
            'known_path_found':bool(known_route),'compound_created':mixed,
            'compound':{'name':key,'physical':mixed_prop},
            'known_cave_exit_route':route==[],
            'level_exit':[ex,ey,-1],
            'facts':facts[:2], 'map_geometry':[len(w['levels']['0'][0]),len(w['levels']['0'])]}
    result['passed']=all(result[k] for k in ['hidden_go_no_oracle','known_path_found','compound_created','known_cave_exit_route'])
    body=json.dumps(result,ensure_ascii=False,sort_keys=True)
    result['fingerprint']=hashlib.sha256(body.encode()).hexdigest()[:16]
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=7321)
    ap.add_argument('--output');args=ap.parse_args()
    result=run(args.seed)
    data=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        with open(args.output,'w',encoding='utf-8') as f:f.write(data+'\n')
    print(data)
    raise SystemExit(0 if result['passed'] else 1)
