"""QA 0.7/22: perfil transversal reproducible sin credenciales ni saves personales.

Este benchmark mide coste de mundos, BFS conocido, escrituras SQLite v5
con historial creciente, peticiones HTTP locales y recuperación en una copia.
No fija umbrales artificiales ni presume autonomía cognitiva del modelo LLM.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
from pathlib import Path
import statistics
import sys
import tempfile
import threading
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from nilo_runtime.application.engine import Simulation
from nilo_runtime.core.state import validate_current_state
from nilo_runtime.storage.backups import backup_file,inspect_backup
from nilo_runtime.worlds.island import new_world,validate_generated_world,PASSABLE,tile
from nilo_runtime.worlds.navigation import pathfind
from nilo_runtime.web.http import create_server


def percentile(samples,p):
    values=sorted(samples)
    if not values:return 0.0
    return round(values[max(0,min(len(values)-1,(len(values)*p+99)//100-1))]*1000,3)


def run(seed_count=24,history_entries=3000,ticks=100,http_requests=36):
    if not (4<=seed_count<=128 and 200<=history_entries<=12000
            and 1<=ticks<=1000 and 5<=http_requests<=300):
        raise ValueError("Parámetros fuera de la ventana de ensayo acotada")
    tracemalloc.start()
    worlds=[]
    distances=0
    world_durations=[]
    for seed in range(seed_count):
        start=time.perf_counter()
        w=new_world(seed)
        validate_generated_world(w)
        origin=(15,10,0)
        count=0
        for key in w["revealed"]:
            x,y,z=map(int,key.split(","))
            if z!=0 or tile(w,x,y,z) not in PASSABLE:continue
            path=pathfind(w,origin,(x,y,z),known_only=True)
            count+=1
            distances+=len(path)
            if count>=10:break
        world_durations.append(time.perf_counter()-start)
        worlds.append(hashlib.sha256(json.dumps(
            w,sort_keys=True,ensure_ascii=False,
            separators=(",",":")).encode()).hexdigest())
    with tempfile.TemporaryDirectory(prefix="nilo-qa22-benchmark-") as directory:
        root=Path(directory)
        db=root/"long_history.sqlite3"
        sim=Simulation(db_path=db,world_seed=7321,rng_seed=9821)
        server=None
        restored=None
        try:
            sim.think=lambda:None
            sim.s["speed"]=60
            sim.s["mode"]="demo"
            sim.s["auto_wait_frozen"]=False
            notes=[{"id":f"qa22-{i:05d}","when":"Día 1",
                    "text":f"Observación de ensayo {i}"}
                   for i in range(history_entries)]
            t=time.perf_counter()
            sim.s["journal"].extend(notes)
            sim.write()
            first_write=time.perf_counter()-t
            p0=sim.conn.execute(
                "SELECT COUNT(*) FROM history WHERE category='journal' "
                "AND item_id LIKE 'qa22-%'").fetchone()[0]
            durations=[]
            for _ in range(6):
                t=time.perf_counter()
                sim.write()
                durations.append(time.perf_counter()-t)
            appends=100
            sim.s["journal"].extend(
                {"id":f"qa22-new-{i:04d}","when":"Día 2",
                 "text":"Entrada nueva de prueba"}
                for i in range(appends))
            t=time.perf_counter()
            sim.write()
            appended_write=time.perf_counter()-t
            p1=sim.conn.execute(
                "SELECT COUNT(*) FROM history WHERE category='journal' "
                "AND item_id LIKE 'qa22-%'").fetchone()[0]
            if (p0,p1)!=(history_entries,history_entries+appends):
                raise AssertionError("Se perdieron o duplicaron registros")
            t=time.perf_counter()
            for _ in range(ticks):
                sim.tick(20)
            elapsed_ticks=time.perf_counter()-t
            validate_current_state(sim.s,strict_physics=True)
            if any(v<0 for v in sim.s["person"]["inventory"].values()):
                raise AssertionError("Inventario negativo durante ejecución")
            sim.write()
            t=time.perf_counter()
            reads=15
            before=sim.conn.total_changes
            for _ in range(reads):
                sim.public_state()
            get_state=(time.perf_counter()-t)/reads
            if sim.conn.total_changes!=before:
                raise AssertionError("Un GET de observación escribió en SQLite")
            t=time.perf_counter()
            backup_manifest=backup_file(db,root/"backup.sqlite3")
            backup_ms=round((time.perf_counter()-t)*1000,3)
            if backup_manifest!=inspect_backup(root/"backup.sqlite3"):
                raise AssertionError("Backup inválido")
            t=time.perf_counter()
            restored=Simulation(db_path=root/"backup.sqlite3")
            restore_ms=round((time.perf_counter()-t)*1000,3)
            if abs(restored.s["person"]["clock_minutes"]
                   -sim.s["person"]["clock_minutes"])>1e-5:
                raise AssertionError("El snapshot recuperado perdió tiempo")
            if restored.entropy_origin!="restored_exact":
                raise AssertionError("El backup perdió el RNG")
            server=create_server(sim,0)
            worker=threading.Thread(target=server.serve_forever,
                                    kwargs={"poll_interval":0.03},daemon=True)
            worker.start()
            timings=[]
            try:
                port=server.server_address[1]
                for i in range(http_requests):
                    path=("/api/state" if i%3==0 else "/"
                          if i%3==1 else "/assets/nilo.css")
                    conn=http.client.HTTPConnection("127.0.0.1",port,timeout=10)
                    try:
                        t=time.perf_counter()
                        conn.request("GET",path)
                        response=conn.getresponse()
                        data=response.read()
                        timings.append(time.perf_counter()-t)
                        if response.status!=200 or not data:
                            raise AssertionError("HTTP local falló: "+path)
                    finally:
                        conn.close()
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)
                server=None
            peak=tracemalloc.get_traced_memory()[1]
            return {
                "fixture":"qa_transversal_22",
                "llm_calls":0,
                "seed_count":seed_count,
                "world_sha256_count":len(set(worlds)),
                "world_generation_and_10_routes_ms_p50":percentile(world_durations,50),
                "world_generation_and_10_routes_ms_p95":percentile(world_durations,95),
                "known_route_total_steps":distances,
                "journal_records":p1,
                "journal_first_write_ms":round(first_write*1000,3),
                "journal_unchanged_write_ms_p50":percentile(durations,50),
                "journal_append_100_ms":round(appended_write*1000,3),
                "physical_ticks":ticks,
                "tick_total_ms":round(elapsed_ticks*1000,3),
                "simulated_minutes":round(sim.s["person"]["clock_minutes"],3),
                "freeze_without_llm":bool(sim.s.get("auto_wait_frozen")),
                "public_state_read_ms_avg":round(get_state*1000,3),
                "http_requests":len(timings),
                "http_latency_ms_p50":percentile(timings,50),
                "http_latency_ms_p95":percentile(timings,95),
                "backup_ms":backup_ms,"restore_open_ms":restore_ms,
                "backup_verified":True,"entropy_restored_exact":True,
                "sqlite_bytes":db.stat().st_size,
                "backup_bytes":(root/"backup.sqlite3").stat().st_size,
                "tracemalloc_peak_mib":round(peak/(1024*1024),2),
                "note":"Runner y fixture sintético: resultados no generalizables a runs autónomos reales."
            }
        finally:
            if server:server.shutdown();server.server_close()
            if restored:restored.conn.close()
            sim.conn.close()
            tracemalloc.stop()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--seeds",type=int,default=24)
    parser.add_argument("--history",type=int,default=3000)
    parser.add_argument("--ticks",type=int,default=100)
    parser.add_argument("--http",type=int,default=36)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run(args.seeds,args.history,args.ticks,args.http)
    output=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output+"\n",encoding="utf-8")
    print(output)


if __name__=="__main__":
    main()
