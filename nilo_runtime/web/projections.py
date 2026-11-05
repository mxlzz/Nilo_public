"""Vista pública v1: quitar metadatos internos sin cambiar el motor.

Se mantienen los nombres usados por interfaz.html. Ninguna clave API,
fingerprint de credenciales o campo del proveedor se devuelve como identidad
del transporte, aunque exista en el estado de ruteo del motor.
"""
from __future__ import annotations


def observer_state(raw):
    """Copia superficial de la respuesta y copia defensiva del árbol de IA."""
    if not isinstance(raw,dict):
        raise TypeError("La proyección de estado debe ser un objeto")
    result=dict(raw)
    ai=raw.get("ai")
    if not isinstance(ai,dict):
        return result
    ai=dict(ai)
    routing=ai.get("routing")
    if isinstance(routing,dict):
        routing=dict(routing)
        providers=routing.get("providers")
        if isinstance(providers,list):
            routing["providers"]=[
                {k:v for k,v in p.items() if k not in ("health_key","api_key",
                    "secret","token","credentials","access_token")}
                if isinstance(p,dict) else p for p in providers]
        ai["routing"]=routing
    result["ai"]=ai
    return result
