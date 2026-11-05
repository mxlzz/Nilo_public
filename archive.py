"""Registro histórico append-only de Nilo y marcadores de lectura persistentes.

Se conserva el snapshot rápido para la simulación; el archivo no tiene política de
retención automática. INSERT OR IGNORE aporta idempotencia durante las migraciones.
"""
from __future__ import annotations

from nilo_runtime.core.identity import new_uuid
import json, time, uuid, hashlib
from record_links import explicit_links, record_title

CATEGORIES = ('journal', 'news', 'event', 'chat', 'research', 'project', 'design', 'proposal', 'habit', 'experience', 'decision', 'observation', 'construction', 'tool', 'diagnostic', 'measurement', 'conclusion', 'llm_decision', 'prediction')

class History:
    def __init__(self, conn):
        self.db = conn
        self.db.execute('''CREATE TABLE IF NOT EXISTS history (
           seq INTEGER PRIMARY KEY AUTOINCREMENT,
           category TEXT NOT NULL, item_id TEXT NOT NULL,
           simulated_at TEXT NOT NULL, real_at REAL NOT NULL,
           payload TEXT NOT NULL, UNIQUE(category, item_id))''')
        self.db.execute('CREATE INDEX IF NOT EXISTS history_by_category ON history(category,seq)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS history_revisions (
            revision INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
            item_id TEXT NOT NULL, captured_at REAL NOT NULL, digest TEXT NOT NULL,
            payload TEXT NOT NULL, UNIQUE(category,item_id,digest))''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS reading_positions (
           category TEXT PRIMARY KEY, through_seq INTEGER NOT NULL DEFAULT 0)''')
        self.db.execute("CREATE TABLE IF NOT EXISTS read_items (category TEXT NOT NULL, seq INTEGER NOT NULL, PRIMARY KEY(category,seq))")
        self.db.execute('''CREATE TABLE IF NOT EXISTS record_links (
          source_category TEXT NOT NULL, source_id TEXT NOT NULL,
          target_category TEXT NOT NULL, target_id TEXT NOT NULL,
          reason TEXT NOT NULL,
          PRIMARY KEY(source_category,source_id,target_category,target_id,reason))''')
        self.db.execute('CREATE INDEX IF NOT EXISTS record_links_reverse ON record_links(target_category,target_id)')
        self.db.execute('CREATE TABLE IF NOT EXISTS record_link_meta (key TEXT PRIMARY KEY)')
        # Migración inicial: solo se vinculan IDs ya guardados de modo explícito.
        if not self.db.execute("SELECT 1 FROM record_link_meta WHERE key='indexed_v1'").fetchone():
            cursor=self.db.execute('SELECT category,item_id,payload FROM history')
            for category,item_id,payload in cursor:
                self._index_links(category,item_id,json.loads(payload))
            self.db.execute("INSERT INTO record_link_meta(key) VALUES('indexed_v1')")
        # Los índices creados por versiones anteriores podían haber omitido
        # vínculos a partir del 80.º/100.º/150.º elemento. Reindexar una vez
        # sobre IDs explícitos, sin reinterpretar ni alterar los registros.
        if not self.db.execute("SELECT 1 FROM record_link_meta WHERE key='indexed_v2_full'").fetchone():
            for category,item_id,payload in self.db.execute('SELECT category,item_id,payload FROM history'):
                self._index_links(category,item_id,json.loads(payload))
            self.db.execute("INSERT INTO record_link_meta(key) VALUES('indexed_v2_full')")
        for category in ('journal', 'news'):
            self.db.execute('INSERT OR IGNORE INTO reading_positions(category, through_seq) VALUES(?,0)',(category,))
        # La conexión del llamador decide cuándo confirmar migración y tablas.
        # Carga una sola vez el índice de entradas inmutables para no reconstruir
        # miles de historiales cada cinco segundos de simulación.
        self._sync_seen_static=set(
            (cat,rid) for cat,rid in self.db.execute(
                "SELECT category,item_id FROM history WHERE category NOT IN "
                "('research','project','design','proposal','construction','tool','prediction')"))
        self._sync_digest={}
        self._static_cursors={}
        # Primera apertura: conocer la última versión ya archivada evita
        # volver a indizar todas las estructuras sin modificaciones.
        mutable={'research','project','design','proposal','construction','tool','prediction'}
        for category,item_id,payload in self.db.execute(
            "SELECT category,item_id,payload FROM history_revisions ORDER BY revision DESC"):
            key=(category,item_id)
            if category not in mutable or key in self._sync_digest:continue
            try:
                canonical=json.dumps(json.loads(payload),sort_keys=True,
                          ensure_ascii=False,separators=(',',':'),default=str)
            except (ValueError,TypeError):
                continue
            self._sync_digest[key]=hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def add(self, category, item, fallback=None):
        if category not in CATEGORIES:raise ValueError('Categoría inválida')
        key = str(item.get('id') or fallback or new_uuid().hex)
        item['id'] = key  # Estabiliza importaciones antiguas y evita duplicados
        payload=json.dumps(item,ensure_ascii=False,separators=(',',':'),default=str)
        # No ejecutar INSERT OR IGNORE sobre una clave ya presente: la secuencia
        # AUTOINCREMENT avanza aun si SQLite descarta la fila duplicada.
        row=self.db.execute('SELECT seq FROM history WHERE category=? AND item_id=?',
                            (category,key)).fetchone()
        if row is None:
            self.db.execute('''INSERT INTO history(category,item_id,simulated_at,real_at,payload)
                               VALUES(?,?,?,?,?)''',
                            (category,key,str(item.get('when',item.get('started','—'))),
                             float(item.get('at') or item.get('started_at') or time.time()),payload))
        # Preservar también los cambios de hipótesis, diseños, proyectos y pruebas.
        if category in ('research','project','design','proposal','construction','tool','prediction'):
            digest=hashlib.sha256(payload.encode('utf-8')).hexdigest()
            self.db.execute('''INSERT OR IGNORE INTO history_revisions(
                category,item_id,captured_at,digest,payload) VALUES(?,?,?,?,?)''',
                (category,key,time.time(),digest,payload))
        self._index_links(category,key,item)
        row=self.db.execute('SELECT seq FROM history WHERE category=? AND item_id=?',(category,key)).fetchone()
        return int(row[0])

    def _index_links(self,category,item_id,item):
        # Indizado incremental idempotente; una relación también puede llegar después
        # de que se haya archivado su otro extremo.
        for target,target_id,reason in explicit_links(category,item):
            self.db.execute('''INSERT OR IGNORE INTO record_links
               (source_category,source_id,target_category,target_id,reason)
               VALUES(?,?,?,?,?)''',(category,item_id,target,target_id,reason))

    @staticmethod
    def relation_phase(origin_category, origin, related_category, related, reason, direction):
        """Categorizar vínculos del cuaderno por evidencia temporal real.

        Nunca presentar un objeto antiguo como nuevo por estar enlazado.
        Con datos insuficientes conservar el estado neutral de relacionado.
        """
        if origin_category != 'journal' or not isinstance(origin,dict):
            return 'related'
        stamp=origin.get('when')
        if not isinstance(stamp,str) or not stamp:
            return 'related'
        if reason=='origen' and direction=='incoming':
            return 'new'
        if not isinstance(related,dict):
            return 'related'
        created=(related.get('started') or related.get('created') or
                 related.get('when'))
        if related_category in ('measurement','conclusion','prediction',
                                'proposal','research','project','design',
                                'construction','tool') and created==stamp:
            return 'new'
        updated=(related.get('updated') or related.get('closed'))
        if related_category in ('project','research','design','construction','tool',
                                'prediction') and updated==stamp and created!=stamp:
            return 'updated'
        return 'related'

    def relations_for(self,category,item_id,limit=None):
        """Todos los vínculos por defecto; límite solo si un consumidor lo solicita."""
        if category not in CATEGORIES or not isinstance(item_id,str) or len(item_id)>100:return []
        outgoing=self.db.execute('''SELECT l.target_category,l.target_id,l.reason,h.payload,h.seq
          FROM record_links l JOIN history h ON h.category=l.target_category AND h.item_id=l.target_id
          WHERE l.source_category=? AND l.source_id=? ORDER BY h.seq DESC''',
          (category,item_id)).fetchall()
        incoming=self.db.execute('''SELECT l.source_category,l.source_id,l.reason,h.payload,h.seq
          FROM record_links l JOIN history h ON h.category=l.source_category AND h.item_id=l.source_id
          WHERE l.target_category=? AND l.target_id=? ORDER BY h.seq DESC''',
          (category,item_id)).fetchall()
        origin_row=self.db.execute(
            'SELECT payload FROM history WHERE category=? AND item_id=?',
            (category,item_id)).fetchone()
        origin=json.loads(origin_row[0]) if origin_row else {}
        result={}
        for direction,records in (('outgoing',outgoing),('incoming',incoming)):
            for kind,rid,reason,payload,seq in records:
                item=json.loads(payload)
                phase=self.relation_phase(category,origin,kind,item,reason,direction)
                key=(kind,rid)
                if key not in result or (result[key]['phase']=='related' and phase!='related'):
                    result[key]={'category':kind,'id':rid,
                       'title':record_title(kind,item),'when':item.get('when',item.get('started','')),
                       'relation':reason,'direction':direction,'phase':phase,'seq':seq}
        if category=='journal':
            # Expandir SOLO mediciones ligadas por journal_id auténtico.
            # La procedencia de inventario puede leerse también en archivos
            # anteriores, sin fingir que cada unidad es un objeto independiente.
            for kind,rid,reason,payload,seq in incoming:
                if kind!='measurement':continue
                measurement=json.loads(payload)
                if measurement.get('journal_id')!=item_id:continue
                for material,quantity in (measurement.get('inventory_delta') or {}).items():
                    if (not isinstance(material,str) or not material or
                            isinstance(quantity,bool) or not isinstance(quantity,(int,float)) or
                            quantity==0):continue
                    verb='Obtenido' if quantity>0 else 'Consumido'
                    amount=('+' if quantity>0 else '')+str(quantity)
                    key=('material',rid+':'+material)
                    result[key]={'category':'material','id':rid+':'+material,
                        'title':f'{material} {amount} · {verb.lower()}',
                        'when':measurement.get('when',''),'relation':verb.lower(),
                        'direction':'incoming','phase':'new','seq':seq}
                for link in measurement.get('entity_links',[]):
                    if not isinstance(link,dict):continue
                    entity_kind=link.get('category')
                    entity_id=link.get('id')
                    if entity_kind not in ('tool','construction') or not isinstance(entity_id,str):
                        continue
                    row=self.db.execute(
                        'SELECT payload,seq FROM history WHERE category=? AND item_id=?',
                        (entity_kind,entity_id)).fetchone()
                    if not row:continue
                    item=json.loads(row[0])
                    relation=link.get('relation','referencia')
                    phase='new' if relation=='creada' else (
                        'updated' if relation in ('modificada','retirada') else 'related')
                    key=(entity_kind,entity_id)
                    if key not in result or result[key]['phase']=='related':
                        result[key]={'category':entity_kind,'id':entity_id,
                            'title':record_title(entity_kind,item)+' · '+relation,
                            'when':measurement.get('when',''),'relation':relation,
                            'direction':'incoming','phase':phase,'seq':seq}
        rank={'new':0,'updated':1,'related':2}
        rows=sorted(result.values(),key=lambda r:(rank.get(r['phase'],2),-r['seq']))
        # Solo los consumidores que solicitan explícitamente selección editorial
        # (por ejemplo QMP) reciben un máximo. Cuaderno/API nunca lo envían.
        return rows if limit is None else rows[:max(0,int(limit))]

    def relations_batch(self,keys):
        """Solo registros visibles, cada uno con todos sus vínculos documentados."""
        result={}
        for category,item_id in dict.fromkeys(keys):
            links=self.relations_for(category,item_id)
            if links:result[f'{category}:{item_id}']=links
        return result

    def sync(self, state):
        person=state['person']
        groups={'journal':state.get('journal',[]),'news':state.get('news',[]),
                'event':state.get('events',[]),'chat':state.get('chat',[]),
                'research':person.get('research',[]),
                'project':person.get('projects',[])+([person['project']] if person.get('project') else []),
                'design':person.get('designs',[]),'proposal':person.get('proposals',[]),
                'diagnostic':person.get('action_outcomes',[]),
                'prediction':person.get('prediction_log',[]),
                'measurement':person.get('measurements',[]),
                'conclusion':person.get('conclusions',[]),
                'habit':person.get('waiting_history',[]),
                'experience':person.get('experience_summary',[]),
                'decision':person.get('decision_history',[]),
                'observation':person.get('observations',[]),
                'construction':state['world'].get('structures',[])+state['world'].get('retired_structures',[]),
                'tool':person.get('items',[])+person.get('retired_items',[])}
        mutable={'research','project','design','proposal','construction','tool','prediction'}
        for category,records in groups.items():
            # Ventana append-only para listas inmutables: O(nuevo), no O(toda
            # la biografía). Si cambió la identidad de la lista, se acotó una
            # ventana o hubo sustitución, se recorre la lista y se deduplica
            # por ID en SQLite, jamás se adivinan desplazamientos del cursor.
            pending=records
            if category not in mutable and isinstance(records,list):
                last=self._static_cursors.get(category)
                # Mantener referencia fuerte: id(list) puede reciclarse y
                # confundir una nueva ventana con una lista anterior.
                if last and last[0] is records and len(records)>=last[1]:
                    size=last[1]
                    first=records[0].get('id') if records and isinstance(records[0],dict) else None
                    prev=records[size-1].get('id') if size and isinstance(records[size-1],dict) else None
                    if first==last[2] and prev==last[3]:
                        pending=records[size:]
                first=records[0].get('id') if records and isinstance(records[0],dict) else None
                last_id=records[-1].get('id') if records and isinstance(records[-1],dict) else None
                self._static_cursors[category]=(records,len(records),first,last_id)
            for item in pending:
                if not isinstance(item,dict):continue
                rid=item.get('id')
                if not isinstance(rid,str) or not rid:
                    self.add(category,item)
                    continue
                key=(category,rid)
                if category not in mutable:
                    if key in self._sync_seen_static:continue
                    self.add(category,item)
                    self._sync_seen_static.add(key)
                else:
                    digest=hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False,
                                      separators=(',',':'),default=str).encode('utf-8')).hexdigest()
                    if self._sync_digest.get(key)==digest:continue
                    self.add(category,item)
                    self._sync_digest[key]=digest

    def recent_meta(self, categories=('journal','news')):
        """One SELECT for identity/seq and one for explicit read markers."""
        cats=tuple(c for c in categories if c in ('journal','news'))
        if not cats:return {},set()
        markers={c:{} for c in cats}
        qs=','.join('?' for _ in cats)
        for cat,item_id,seq in self.db.execute(
            f'SELECT category,item_id,seq FROM history WHERE category IN ({qs})',cats):
            markers[cat][item_id]=int(seq)
        read={(c,int(seq)) for c,seq in self.db.execute(
            f'SELECT category,seq FROM read_items WHERE category IN ({qs})',cats)}
        return markers,read

    def seq_for(self, category, item_id):
        row=self.db.execute('SELECT seq FROM history WHERE category=? AND item_id=?',(category,str(item_id))).fetchone()
        return int(row[0]) if row else 0

    def position(self, category):
        row=self.db.execute('SELECT through_seq FROM reading_positions WHERE category=?',(category,)).fetchone()
        return int(row[0]) if row else 0

    def count_unread(self, category):
        return int(self.db.execute('''SELECT COUNT(*) FROM history h WHERE h.category=? AND h.seq>?
           AND NOT EXISTS (SELECT 1 FROM read_items r WHERE r.category=h.category AND r.seq=h.seq)''',
           (category,self.position(category))).fetchone()[0])

    def is_read(self, category, seq):
        if seq<=self.position(category):return True
        return bool(self.db.execute('SELECT 1 FROM read_items WHERE category=? AND seq=?',
                                    (category,int(seq))).fetchone())

    def mark_one_read(self, category, seq):
        """Lee exactamente una entrada, sin desplazar el marcador cronológico."""
        if category not in ('journal','news'):raise ValueError('Categoría inválida')
        seq=int(seq)
        if not self.db.execute('SELECT 1 FROM history WHERE category=? AND seq=?',
                               (category,seq)).fetchone():raise ValueError('No existe esta entrada')
        self.db.execute('INSERT OR IGNORE INTO read_items(category,seq) VALUES (?,?)',(category,seq))
        return self.count_unread(category)

    def max_seq(self, category):
        return int(self.db.execute('SELECT COALESCE(MAX(seq),0) FROM history WHERE category=?',(category,)).fetchone()[0])

    def mark_read(self, category, seq=None):
        if category not in ('journal','news'):raise ValueError('Categoría de lectura inválida')
        maximum=self.max_seq(category)
        if seq is None:seq=maximum
        seq=int(seq)
        if seq<0 or seq>maximum:raise ValueError('Marcador de lectura fuera de rango')
        # Se avanza la posición, nunca se retrocede accidentalmente.
        self.db.execute('UPDATE reading_positions SET through_seq=MAX(through_seq,?) WHERE category=?',(seq,category))
        return self.position(category)

    def unread(self, category, limit=None, after=None):
        if category not in ('journal','news'):raise ValueError('Categoría inválida')
        cursor=self.position(category) if after is None else int(after)
        sql="SELECT seq,payload FROM history h WHERE h.category=? AND h.seq>? AND NOT EXISTS (SELECT 1 FROM read_items r WHERE r.category=h.category AND r.seq=h.seq) ORDER BY seq ASC"
        params=[category,cursor]
        if limit is not None:sql+=' LIMIT ?';params.append(int(limit))
        return [{'seq':int(row[0]),**json.loads(row[1])} for row in self.db.execute(sql,params)]

    def pending_page(self, offset=0, limit=80):
        where="((category='journal' AND seq>?) OR (category='news' AND seq>?)) AND NOT EXISTS (SELECT 1 FROM read_items r WHERE r.category=history.category AND r.seq=history.seq)"
        params=(self.position('journal'),self.position('news'))
        total=sum((self.count_unread('journal'),self.count_unread('news')))
        rows=self.db.execute(f'SELECT seq,category,payload FROM history WHERE {where} ORDER BY seq ASC LIMIT ? OFFSET ?',
                             (*params,max(1,int(limit)),max(0,int(offset))))
        return total,[{'seq':int(row[0]),'category':row[1],**json.loads(row[2])} for row in rows]

    def get(self, category, item_id):
        """Recuperar un registro histórico por identificador sin alterar el archivo."""
        if category not in CATEGORIES or not isinstance(item_id, str):
            return None
        row=self.db.execute(
            'SELECT payload FROM history WHERE category=? AND item_id=?',
            (category,item_id)).fetchone()
        return json.loads(row[0]) if row else None

    def latest_record(self,category,item_id):
        """Vista actual de un registro mutable, sin cambiar su primer asiento."""
        if category in ('research','project','design','proposal','construction','tool','prediction'):
            row=self.db.execute('''SELECT payload FROM history_revisions
                WHERE category=? AND item_id=? ORDER BY revision DESC LIMIT 1''',
                (category,str(item_id))).fetchone()
            if row:return json.loads(row[0])
        return self.get(category,item_id)

    def recent(self, category, limit=50):
        if category not in CATEGORIES:raise ValueError('Categoría inválida')
        return [{'seq':int(row[0]),**json.loads(row[1])} for row in self.db.execute(
            'SELECT seq,payload FROM history WHERE category=? ORDER BY seq DESC LIMIT ?',
            (category,int(limit)))]

    def counts(self):
        return {cat:int(n) for cat,n in self.db.execute('SELECT category,COUNT(*) FROM history GROUP BY category')}
