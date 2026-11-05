"""Lecturas transversales y resúmenes históricos de la observación de Nilo.

No interviene en la memoria del personaje. Las marcas por ficha son independientes
del navegador; los registros Cuaderno/Novedades conservan sus marcas del archivo.
"""
from __future__ import annotations
import json
import time
import uuid

TABS=frozenset(('activity','research','measurements','findings','creations','projects',
                'agenda','identity','habits','proposals'))
KINDS=frozenset(('event','research','prediction','measurement','conclusion','finding',
                 'knowledge','design','plan','project','agenda','experience','habit',
                 'skill','proposal'))

class ReviewStore:
    def __init__(self,db):
        self.db=db
        db.execute("""CREATE TABLE IF NOT EXISTS reviewed_entries(
            tab TEXT NOT NULL, entry_key TEXT NOT NULL,
            read_at REAL NOT NULL, PRIMARY KEY(tab,entry_key))""")
        db.execute("""CREATE TABLE IF NOT EXISTS review_meta(
            key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS observer_summaries(
            id TEXT PRIMARY KEY, made_at REAL NOT NULL,
            text TEXT NOT NULL, entries TEXT NOT NULL, model TEXT NOT NULL,
            acknowledged INTEGER NOT NULL DEFAULT 0)""")
        db.commit()

    def initialized(self):
        return bool(self.db.execute("SELECT 1 FROM review_meta WHERE key='initialized_v1'").fetchone())

    def seen(self):
        result={t:[] for t in TABS}
        for tab,key in self.db.execute('SELECT tab,entry_key FROM reviewed_entries'):
            if tab in result:result[tab].append(key)
        return result

    def is_seen(self,tab,key):
        return bool(self.db.execute('SELECT 1 FROM reviewed_entries WHERE tab=? AND entry_key=?',
                                    (tab,key)).fetchone())

    def mark(self,pairs):
        for tab,key in pairs:
            if tab not in TABS or not isinstance(key,str) or not (0<len(key)<=300):
                raise ValueError('Registro de lectura inválido')
        for tab,key in pairs:
            self.db.execute('INSERT OR IGNORE INTO reviewed_entries(tab,entry_key,read_at) VALUES (?,?,?)',
                            (tab,key,time.time()))

    def bootstrap(self,seen):
        if self.initialized():return False
        if not isinstance(seen,dict):raise ValueError('Estado inicial inválido')
        pairs=[]
        for tab,keys in seen.items():
            if tab not in TABS:continue
            if not isinstance(keys,list) or len(keys)>3000:raise ValueError('Demasiados registros de lectura')
            pairs.extend((tab,k) for k in keys if isinstance(k,str) and 0<len(k)<=300)
        self.mark(pairs)
        self.db.execute("INSERT INTO review_meta(key,value) VALUES('initialized_v1','1')")
        return True

    def new_summary(self,text,entries,model):
        sid='sum-'+uuid.uuid4().hex[:14]
        self.db.execute('INSERT INTO observer_summaries(id,made_at,text,entries,model) VALUES(?,?,?,?,?)',
                        (sid,time.time(),text,json.dumps(entries,ensure_ascii=False),model))
        return sid

    def summary(self,sid):
        row=self.db.execute('SELECT id,made_at,text,entries,model,acknowledged FROM observer_summaries WHERE id=?',
                            (sid,)).fetchone()
        if not row:return None
        return dict(id=row[0],at=row[1],text=row[2],entries=json.loads(row[3]),
                    model=row[4],acknowledged=bool(row[5]))

    def recent_summaries(self,limit=100):
        output=[]
        for sid,at,summary_text,raw,ack in self.db.execute(
            'SELECT id,made_at,text,entries,acknowledged FROM observer_summaries ORDER BY made_at DESC LIMIT ?',
            (int(limit),)):
            refs=json.loads(raw);links=[];seen=set()
            for ref in refs:
                category,rid=ref.get('category'),ref.get('id')
                if category not in ('research','prediction','measurement','conclusion',
                                    'proposal','project','design','tool','construction','journal'):continue
                if (category,rid) in seen:continue
                seen.add((category,rid))
                links.append({'category':category,'id':rid,'title':str(ref.get('title','Registro original'))[:90]})
                if len(links)>=12:break
            output.append(dict(id=sid,at=at,text=summary_text,
                               count=len({(r.get('category'),r.get('id')) for r in refs}),
                               acknowledged=bool(ack),links=links))
        return output

    def acknowledge(self,sid,archive):
        item=self.summary(sid)
        if item is None:raise ValueError('No existe ese resumen')
        if item['acknowledged']:return item
        pairs=[]
        for r in item['entries']:
            if r.get('category') in ('journal','news'):
                category=r['category'];seq=archive.seq_for(category,r['id'])
                if seq:archive.mark_one_read(category,seq)
            elif r.get('tab') in TABS and r.get('key'):
                pairs.append((r['tab'],r['key']))
        self.mark(pairs)
        self.db.execute('UPDATE observer_summaries SET acknowledged=1 WHERE id=?',(sid,))
        return self.summary(sid)
