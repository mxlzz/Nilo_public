"""Modelo de objetos isla_v1: identidad física, forma y capacidades.

No conoce la UI, LLM, lógica de acciones, contexto del agente ni persistencia.
Los nombres solo se consultan en las funciones explícitas de compatibilidad
con objetos antiguos. Los objetos nuevos requieren forma declarada para
obtener efectos: el lenguaje de su etiqueta no constituye evidencia física.
"""
from __future__ import annotations

import math
from catalogo import FORMS, PORTABLE_WORDS
from nilo_runtime.core.identity import physical_suffix


def infer_form(name,form=''):
    form=str(form).lower().strip()
    if form in FORMS:return form
    name=str(name).lower()
    for kind,words in FORMS.items():
        if any(word in name for word in words):return kind
    return 'golpe' if 'herramienta' in name else 'simple'

def is_portable(name,form='',purpose=''):
    if str(form).lower().strip() in FORMS:return True
    name=str(name).lower()
    return any(word in name for word in PORTABLE_WORDS)

def item_effects(item):
    # Capacidades verificables limitadas por geometría y resistencia estructural.
    form=item.get('form','simple')
    def measured(key):
        try:
            value=float(item.get(key,0))
        except (TypeError,ValueError,OverflowError):
            return 0.0
        return max(0.0,min(10.0,value)) if math.isfinite(value) else 0.0
    q=measured('resistance');hard=measured('hardness')
    if form=='golpe':return {'golpear':round(min(10,(q+hard)/2),1)}
    if form=='punta':return {'excavar':round(min(10,hard*.7+q*.3),1),'golpear':round(hard*.4,1)}
    if form=='filo':return {'cortar':round(min(10,hard*.75+q*.25),1)}
    if form=='palanca':return {'mover':round(min(10,q*.8+hard*.2),1)}
    if form=='recipiente':return {'contener':round(min(10,q*.5),1)}
    return {}

def make_item(name,purpose,materials,props,clock,source=None,rng=None,*,strict_form=False):
    form=declared_form(source) if strict_form else infer_form(name,source or '')
    item={'id':'obj-'+str(physical_suffix(52,rng=rng)), 'name':name,'purpose':purpose,
          'form':form,'materials':list(materials),'resistance':round(props['resistencia'],1),
          'hardness':round(props['dureza'],1),'weight':round(props['peso'],1),
          'durability':100,'tests':[],'created_at_minutes':round(clock,1),'portable':True}
    item['possible_uses']=item_effects(item)
    return item

def classify_structure(name,purpose):
    """Clasificación solo visual: no atribuye funciones demostradas."""
    t=(name+' '+purpose).lower()
    if any(k in t for k in ('palanca','polea','contrapeso','mecanismo','rueda','engranaje','torno','herramienta','dispositivo')):return 'mecanismo'
    if any(k in t for k in ('refugio','habitación','habitáculo','casa','cabaña','taller','almacén','cobertizo')):return 'habitaculo'
    if any(k in t for k in ('soporte','puente','plataforma','escalera','muro','mesa','banco','andamio','estructura')):return 'estructura'
    return 'prototipo'


def structure_symbol(s):
    return {'mecanismo':'M','estructura':'E','habitaculo':'H','prototipo':'?'}.get(s.get('category','prototipo'),'?')


def enrich_structure(s):
    """Compatibilidad de construcciones previas: descripción basada en datos existentes."""
    s.setdefault('category',classify_structure(str(s.get('name','')),str(s.get('purpose',''))))
    s.setdefault('status','Prototipo sin funcionamiento verificado')
    mats=s.get('materials',[])
    strength=s.get('resistance',0)
    s.setdefault('description',f"{s.get('category','Prototipo').capitalize()} hecho con {', '.join(mats) if mats else 'materiales sin registrar'}. Resistencia estructural estimada: {strength}/10. La función que imaginé aún no está probada.")
    return s



def declared_form(form):
    """Forma física validada; los rótulos y propósitos no se interpretan."""
    value=str(form or '').strip().casefold()
    return value if value in FORMS else 'simple'


def physical_item(name, purpose, materials, props, clock, source=None, rng=None):
    """Factoría para entidades nuevas: la forma explícita es su único origen.

    Conserva la estructura histórica de make_item y la fuente de IDs.
    """
    return make_item(name,purpose,materials,props,clock,source,rng=rng,
                     strict_form=True)


def component_summary(obj):
    """Proyección no mutante, sin crear IDs ni rellenar components en saves."""
    materials=obj.get('materials',())
    comps=obj.get('components')
    if isinstance(comps,list):
        return tuple((str(c.get('material','')),c.get('condition',1.0))
                     for c in comps if isinstance(c,dict))
    if isinstance(materials,list):
        return tuple((str(m),None) for m in materials)
    return ()
