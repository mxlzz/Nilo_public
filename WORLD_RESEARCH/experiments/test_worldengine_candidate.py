"""Candidato WorldEngine: prueba de generación, serialización y reproducibilidad.

Se ejecuta en un checkout temporal de upstream. No contiene código de
simulación física nuevo ni se incorpora a Nilo.
"""
import hashlib
import json
import numpy as np
from worldengine.plates import world_gen
from worldengine.model.world import World


def digest(w):
    arr = np.asarray(w.layers["elevation"].data)
    assert arr.shape == (16, 32), f"shape: {arr.shape}"
    assert bool(np.isfinite(arr).all()), "non-finite elevations"
    return hashlib.sha256(arr.tobytes()).hexdigest()


def main():
    np.random.seed(1234)
    a = world_gen("evaluation", 32, 16, 7321, verbose=False)
    da = digest(a)

    np.random.seed(1234)
    b = world_gen("evaluation", 32, 16, 7321, verbose=False)
    db = digest(b)
    assert da == db, "same seed and same global rng state differ"

    serialized = a.protobuf_serialize()
    restored = World.protobuf_unserialize(serialized)
    assert digest(restored) == da, "serialization roundtrip differed"

    # Test the hidden-global-RNG dependency WITHOUT assuming that it will fail.
    c = world_gen("evaluation", 32, 16, 7321, verbose=False)
    dc = digest(c)

    print(json.dumps({
        "candidate": "WorldEngine",
        "generator_seed": 7321,
        "initial_numpy_global_seed": 1234,
        "dimensions": [32, 16],
        "reproducible_when_global_rng_reset": da == db,
        "reproducible_without_global_rng_reset": da == dc,
        "protobuf_restoration_preserves_elevation": True,
        "elevation_sha256": da,
        "serialized_bytes": len(serialized),
        "limitation": "Tests only generated elevation and Protobuf, not ongoing evolution."
    }, indent=2))


if __name__ == "__main__":
    main()
