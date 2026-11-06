"""Normalización y temas de investigación reproducibles y compartidos."""
from __future__ import annotations
import re
import unicodedata

def canonical(text):
    s = ''.join(c for c in unicodedata.normalize('NFKD', str(text).lower()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', s))


def topic(text):
    s=canonical(text)
    # No confundir refugio como construcción con un estudio de recuperación.
    if any(k in s for k in ('descans', 'recuper', 'repos', 'dorm', 'energia', 'fatiga')) and any(
        k in s for k in ('refugio', 'intemperie', 'aire libre', 'arboleda', 'arenal', 'entorno', 'sue')
    ):
        return 'recuperacion_energia'
    return ''


