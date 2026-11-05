"""Prevalidación y filtrado de planes de isla_v1.

El agente conserva las decisiones; este módulo solo aplica reglas verificables
del entorno. Se inyectan el entorno, el mundo, la persona y los callbacks de
registro, sin importar Simulation ni modificar el contexto del LLM.
"""
from __future__ import annotations
from collections import Counter
from construction import find_object
from physics import geometry_from_step
from phenomena import missing_physics
from research_cycle import prediction_metric_warning
from world import (infer_form, is_portable, item_effects, cave_exit, known_exit_route, gather_material)


class IslandPlanner:
    def __init__(self, environment, world, person, remember_strategy, event):
        self.environment = environment
        self.world = world
        self.person = person
        self.remember_strategy = remember_strategy
        self.event = event

    def validate_plan(self,steps):
        """Prevalidación conservadora: geometría, recursos y capacidades.

        No anticipa el resultado de acciones futuras; si antes se fabrica/recolecta,
        permite que los efectos físicos se verifiquen durante la ejecución.
        """
        from world import passable, pathfind
        p=self.person;w=self.world
        ready_forms={it.get('form') for it in p.get('items',[]) if it.get('durability',0)>0}
        future_names={it.get('name','').lower() for it in p.get('items',[]) if it.get('durability',0)>0}
        available={m for m,n in p.get('inventory',{}).items() if n>0}
        projected_gather=set();future_forms={};possible_move=False;plan=[];rejected=[]
        returning_to_surface=False
        for raw in steps:
            step=dict(raw);op=step.get('op')
            explanation=None
            if op=='go':
                # Si el plan incluye primero volver a superficie, la orilla solo
                # puede comprobarse después del ascenso. Nunca evaluarla desde z=-1.
                if returning_to_surface:
                    possible_move=True
                else:
                    destination,water_target,reason=self.environment.validate_destination(w,p,step)
                    if reason:explanation=reason
                    else:possible_move=True
            elif op=='gather':
                material=gather_material(step.get('target'))
                if material is None:
                    explanation=('No reconozco ese nombre de material o depósito. '
                                 'Para recolectar usá piedra/roca, mineral oscuro/'
                                 'afloramiento mineral, madera/arboleda, arcilla, fibra o cristal.')
                else:
                    # Anticipar solo el material que realmente produce el depósito.
                    available.add(material)
                    projected_gather.add(material)
                    possible_move=True
            elif op in ('craft','build','combine'):
                mats=step.get('materials',[])
                if not isinstance(mats,list):mats=[]
                mats=[str(m).lower().strip() for m in mats]
                if mats and any(m not in available for m in mats):
                    explanation='Propone fabricar o combinar materiales que todavía no llevo; primero debo conseguirlos.'
                if not explanation and op=='craft':
                    form=infer_form(str(step.get('name','')),step.get('form',''))
                    if form not in ('golpe','punta','filo','palanca','recipiente','simple'):
                        explanation='La herramienta propuesta no especifica una forma físicamente implementada.'
                    else:
                        ready_forms.add(form);future_names.add(str(step.get('name','')).lower())
                        future_forms[str(step.get('name','')).lower()]=form
            elif op=='assemble':
                parts=step.get('parts',[])
                if not isinstance(parts,list) or len(parts)<2:
                    explanation='Un ensamblaje requiere dos o más piezas.'
                elif any(not isinstance(part,dict) or str(part.get('material','')).lower() not in available for part in parts):
                    explanation='Antes de ensamblar necesito los materiales de todas las piezas.'
                else:
                    future_names.add(str(step.get('name','')).lower())
                    future_forms[str(step.get('name','')).lower()]='ensamblaje'
            elif op in ('modify','dismantle'):
                from construction import find_object
                name=step.get('item') or step.get('target') or step.get('object')
                kind,obj=find_object(w,p,name)
                if not obj:
                    # Puede haberse construido en un paso anterior del mismo bloque.
                    if not any(str(s.get('name','')).casefold()==str(name).casefold() for s in plan if s.get('op') in ('build','craft')):
                        explanation='Antes de intervenir debo identificar una obra/herramienta existente o construirla en este bloque.'
                elif kind=='structure' and not possible_move:
                    pos=obj.get('pos',[])
                    if len(pos)!=3 or pos[2]!=p['pos'][2] or abs(pos[0]-p['pos'][0])+abs(pos[1]-p['pos'][1])>1:
                        explanation='Debo acercarme a esa construcción antes de modificarla.'
            elif op=='experiment':
                requested=str(step.get('target','')).lower()
                if not missing_physics(step) and not any(m in requested for m in available):
                    explanation='El experimento necesita una muestra en inventario antes de ejecutarse.'
            elif op=='use':
                name=str(step.get('item','')).lower().strip()
                method=str(step.get('method','')).lower().strip()
                known=next((it for it in p.get('items',[]) if it.get('id','').lower()==name or
                            it.get('name','').lower()==name or name in it.get('name','').lower()),None) if name else None
                form=known.get('form') if known else None
                if known and not missing_physics(step) and method not in (set(item_effects(known)) | {'llenar','contener','flotar','navegar'} | ({'transmitir_movimiento','transmision','resistir_carga','carga'} if known.get('form')=='ensamblaje' else set())):
                    explanation=f'La forma de {known.get("name")} no permite {method}.'
                elif not known and not any(name==n or (name and name in n) for n in future_names) and not (
                        missing_physics(step) and any(
                        (name==str(obj.get('id','')).lower() or name==str(obj.get('name','')).lower())
                        and len(obj.get('pos',[]))==3 and obj['pos'][2]==p['pos'][2]
                        and abs(obj['pos'][0]-p['pos'][0])+abs(obj['pos'][1]-p['pos'][1])<=1
                        for obj in w.get('structures',[]))):
                    explanation=f'La herramienta {name or "sin identificar"} no está en mi inventario ni en el bloque.'
                elif not known:
                    future_form=next((form for item,form in future_forms.items() if name==item or (name and name in item)),None)
                    allowed={'golpe':{'golpear'},'punta':{'excavar','golpear'},
                        'filo':{'cortar'},'palanca':{'mover'},'recipiente':{'contener'},'simple':set(), 'ensamblaje':{'transmitir_movimiento','transmision','resistir_carga','carga'}}
                    for methods in allowed.values(): methods.update(('llenar','contener','flotar','navegar'))
                    if future_form and not missing_physics(step) and method not in allowed.get(future_form,set()):
                        explanation=f'La forma {future_form} no permite {method}.'
                if method in ('excavar','navegar') and explanation is None:
                    possible_move=True
            elif op=='excavate':
                if 'punta' not in ready_forms:
                    explanation='Para excavar necesito fabricar o llevar una herramienta de punta primero.'
                else:possible_move=True
            elif op in ('descend','ascend'):
                from world import cave_exit, known_exit_route
                ex,ey=cave_exit(w)
                if op=='ascend' and p['pos'][2]==-1:
                    if known_exit_route(w,p) is None:
                        explanation='No conozco una ruta transitable de regreso hasta la salida de la cueva.'
                    else:
                        possible_move=True
                        returning_to_surface=True
                elif not possible_move and abs(p['pos'][0]-ex)+abs(p['pos'][1]-ey)>1:
                    explanation='Necesito llegar a la conexión entre niveles antes de cambiar de nivel.'
            if explanation:
                rejected.append(f'{op}: {explanation}')
                continue
            warning=prediction_metric_warning(step)
            if warning:
                step.pop('prediction',None)
                self.remember_strategy('Predicción no medible: '+warning)
                self.event([warning],'evaluación')
            plan.append(step)
        for reason in rejected:self.remember_strategy('Plan validado: '+reason)
        if rejected:self.event(['Descarté '+str(len(rejected))+' paso(s) físicamente imposibles antes de ejecutarlos. '+rejected[0]],'evaluación')
        return plan

    def improve_plan(self, steps):
        """Filtro conservador: no repetir ensayos ya resueltos sin anular copias legítimas.

        Nunca decide si una idea es 'interesante'; solo descarta operaciones sin efecto nuevo.
        """
        from collections import Counter
        p=self.person;plan=[];skipped=[];aliases={}
        for raw_step in steps:
            step=dict(raw_step)
            if step.get('op')=='use':
                old=str(step.get('item','')).lower().strip()
                if old in aliases:step['item']=aliases[old]
            op=step.get('op')
            if op=='experiment':
                target=str(step.get('target','')).lower();method=str(step.get('method') or 'golpear').lower()
                mat=next((m for m,n in p['inventory'].items() if n>0 and m in target),None)
                if mat and f'{mat}|{method}' in p['knowledge']:
                    skipped.append(f"El experimento {mat} + {method} ya tiene resultado comprobado.")
                    continue
            elif op=='use':
                name=str(step.get('item') or step.get('target') or '').lower();method=str(step.get('method','')).lower()
                tool=next((it for it in p.get('items',[])
                           if it.get('id')==name or it.get('name','').lower()==name
                           or (name and name in it.get('name','').lower())),None)
                if tool:
                    tgt=str(step.get('target','')).lower()
                    material=next((m for m,n in p['inventory'].items() if n>0 and m in tgt),None)
                    context=('agua' if 'agua' in tgt else material or 'entorno')
                    failed=any(t.get('revision',1)==tool.get('revision',1) and t.get('method')==method and t.get('target')==context
                        and not t.get('success') and (method=='golpear' or t.get('pos')==p['pos'])
                        for t in tool.get('tests',[]))
                    if failed:
                        skipped.append(f"El uso {tool['name']} + {method} + {context} ya falló en las mismas condiciones.")
                        continue
            plan.append(step)
        for reason in skipped:self.remember_strategy(reason)
        if skipped:
            self.event(["Revisé mi plan y descarté operaciones redundantes. "+' '.join(skipped[:2])], 'evaluación')
        if not plan:
            self.event(['Descarté todos los pasos por inviables o repetidos; no invento una orden de exploración.'], 'evaluación')
        return plan

