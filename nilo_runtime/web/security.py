"""Frontera del servidor local: bloquear origen remoto y entrada inesperada.

La interfaz sólo es accesible por loopback; bloquear Host ajeno y Origin
cross-site reduce DNS rebinding y solicitudes desde sitios de terceros.
"""
from __future__ import annotations

import json
from urllib.parse import urlsplit

LOOPBACK=frozenset(("127.0.0.1","localhost","::1"))
MAX_JSON=65000


class RequestError(ValueError):
    def __init__(self,message,status=400):
        super().__init__(message)
        self.status=status


def _authority(value,port,scheme=None):
    if not value or len(value)>300:
        return False
    try:
        parts=urlsplit(value if scheme else "http://"+value)
        specified_port=parts.port
    except (ValueError,TypeError):
        return False
    return (parts.hostname in LOOPBACK
            and specified_port==port
            and not parts.username and not parts.password
            and not parts.path.strip("/")
            and not parts.query and not parts.fragment
            and (scheme is None or parts.scheme=="http"))


def authorize(headers,port):
    """Browser local o CLI sin Origin. Nunca confiar en nombres DNS externos."""
    hosts=headers.get_all("Host",[]) if hasattr(headers,"get_all") else [headers.get("Host","")]
    if len(hosts)!=1 or not _authority(hosts[0],port):
        raise RequestError("Host local inválido",403)
    origin=headers.get("Origin")
    if origin is not None and not _authority(origin,port,scheme="http"):
        raise RequestError("Origen no autorizado",403)
    referer=headers.get("Referer")
    if referer is not None:
        try:
            p=urlsplit(referer)
            authority=p.netloc
            allowed=(p.scheme=="http" and _authority(authority,port))
        except (ValueError,TypeError):
            allowed=False
        if not allowed:raise RequestError("Referencia no autorizada",403)
    if headers.get("Sec-Fetch-Site","").lower()=="cross-site":
        raise RequestError("Solicitud de otro sitio",403)


def parse_body(headers,stream,maximum=3000):
    if headers.get("Transfer-Encoding"):
        raise RequestError("Transfer-Encoding no admitido")
    ct=headers.get("Content-Type","").lower()
    media,*params=[v.strip() for v in ct.split(";")]
    if media!="application/json" or any(
            p not in ("charset=utf-8",'charset="utf-8"') for p in params):
        raise RequestError("Se requiere Content-Type: application/json",415)
    lengths=(headers.get_all("Content-Length",[])
             if hasattr(headers,"get_all") else [headers.get("Content-Length","")])
    if len(lengths)!=1 or not lengths[0].isascii() or not lengths[0].isdecimal():
        raise RequestError("Content-Length inválido")
    if len(lengths[0])>12:
        raise RequestError("Solicitud demasiado grande o vacía",413)
    size=int(lengths[0])
    if size<1 or size>maximum:
        raise RequestError("Solicitud demasiado grande o vacía",413)
    try:
        raw=stream.read(size)
        if len(raw)!=size:raise RequestError("Cuerpo incompleto")
        data=json.loads(raw.decode("utf-8"),
                        parse_constant=lambda v: (_ for _ in ()).throw(
                            ValueError("Número no finito en JSON")))
    except (UnicodeError,ValueError) as exc:
        if isinstance(exc,RequestError):raise
        raise RequestError("JSON inválido") from exc
    if not isinstance(data,dict):
        raise RequestError("Se esperaba un objeto JSON")
    return data
