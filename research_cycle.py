"""Hipótesis de Nilo, contrastadas solo con métricas reales del motor."""
import math
import re
import uuid

OPS = {"experiment", "use", "rest", "craft", "build", "assemble", "modify", "combine", "excavate"}
CMP = {"gte": lambda a,b:a>=b, "gt": lambda a,b:a>b,
       "lte":lambda a,b:a<=b, "lt":lambda a,b:a<b, "eq":lambda a,b:a==b}

# Variables numéricas que el contrato ActionResult realmente puede entregar.
# No inventar mediciones por analogía con una función todavía sin física.
PREDICTION_METRICS={
    ('rest',''):{'energy_per_hour'},
    ('experiment','golpear'):{'dureza'},
    ('experiment','cargar'):{'resistencia'},
    ('use','contener'):{'capacidad_util_agua'},
    ('use','llenar'):{'capacidad_util_agua'},
    ('use','flotar'):{'empuje','carga'},
    ('use','navegar'):{'empuje','carga'},
    ('use','carga'):{'carga_aplicada','limite_carga'},
    ('use','resistir_carga'):{'carga_aplicada','limite_carga'},
    ('use','transmision'):{'energia_aplicada','energia_salida'},
    ('use','transmitir_movimiento'):{'energia_aplicada','energia_salida'},
}

def prediction_metric_warning(step):
    """Diagnóstico anterior al ensayo: no invalida la acción física."""
    pred=step.get('prediction')
    if not isinstance(pred,dict):return ''
    metric=str(pred.get('metric') or '').strip()
    if not metric or not pred.get('operator'):return ''
    op=str(step.get('op',''));method=str(step.get('method','')).lower().strip()
    allowed=PREDICTION_METRICS.get((op,method),set())
    # Las pruebas con herramientas precisan además forma y condiciones apropiadas:
    # la validación definitiva se hace después con evidencia física real.
    if metric not in allowed:
        available=', '.join(sorted(allowed)) if allowed else 'ninguna variable numérica modelada'
        return (f"La operación {op}/{method or 'sin método'} no mide '{metric}'. "
                f"Variables que este método puede devolver: {available}. "
                'La acción puede ejecutarse, pero no se crea una predicción numérica sin modelo.')
    return ''

def normalize_prediction(raw):
    if not isinstance(raw,dict):return None
    hypothesis=str(raw.get("hypothesis") or "").strip()[:260]
    effect=str(raw.get("expected_effect") or "").strip()[:220]
    if not hypothesis or not effect:return None
    metric=str(raw.get("metric") or "").strip()[:64]
    if metric and not re.fullmatch("[a-z][a-z0-9_]{0,63}",metric):metric=""
    operator=str(raw.get("operator") or "").lower().strip()
    value=raw.get("threshold")
    if operator not in CMP or not metric or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        operator="";value=None
    return {"hypothesis":hypothesis,"expected_effect":effect,"metric":metric,
            "operator":operator,"threshold":value}

def begin_prediction(person,step,stamp):
    if step.get("op") not in OPS:return None
    pred=normalize_prediction(step.get("prediction"))
    if pred is None:return None
    row={"id":"pred-"+uuid.uuid4().hex[:12],"when":stamp,
         "clock_minutes":float(person.get("clock_minutes",0)),
         "project_id":(person.get("project") or {}).get("id"),
         "operation":step["op"],"target":str(step.get("target") or step.get("item") or step.get("name") or "")[:120],
         "method":str(step.get("method") or "")[:80],
         "position":list(person.get("pos",[])),**pred,"status":"pendiente"}
    if isinstance(step.get('_journal_id'),str):row['journal_id']=step['_journal_id']
    person.setdefault("prediction_log",[]).append(row)
    person["prediction_log"]=person["prediction_log"][-120:]
    return row

def finish_prediction(person,prediction_id,result,stamp,measurement_id=None,action_id=None,measurement=None):
    row=next((x for x in reversed(person.get("prediction_log",[])) if x["id"]==prediction_id),None)
    if row is None or row["status"]!="pendiente":return None
    physical=result.physical if isinstance(result.physical,dict) else {}
    metrics=dict(physical.get("metrics") if isinstance(physical.get("metrics"),dict) else {})
    if measurement and measurement.get('op')=='rest' and measurement.get('rest_comparable'):
        if isinstance(measurement.get('energy_per_hour'),(int,float)):
            metrics['energy_per_hour']=measurement['energy_per_hour']
    value=metrics.get(row["metric"])
    valid=isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    if result.status=="no_evaluable":status="sin_modelo_evaluable"
    elif row["metric"] and row["operator"] in CMP and valid:
        status="prediccion_coincide" if CMP[row["operator"]](value,row["threshold"]) else "prediccion_no_coincide"
    elif row["metric"] and row["operator"] in CMP:status="variable_no_medida"
    elif row["metric"]:status="criterio_incompleto"
    else:status="prediccion_cualitativa"
    row.update({"status":status,"finished":stamp,"evaluation_status":result.status,
                "operation_success":result.success,"measured_value":value if valid else None,
                "available_metrics":sorted(metrics),"physical_kind":physical.get("kind"),
                "measurement_id":measurement_id,"action_id":action_id,
                "scope":"El contraste evalúa esta métrica, no la hipótesis causal ni otras propiedades."})
    return row

def recent_predictions(person,limit=5):
    keys=("id","hypothesis","expected_effect","metric","operator","threshold",
          "measured_value","available_metrics","status","evaluation_status",
          "measurement_id","action_id")
    return [{k:r.get(k) for k in keys} for r in person.get("prediction_log",[])[-limit:]]
