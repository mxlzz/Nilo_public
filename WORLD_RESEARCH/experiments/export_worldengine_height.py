"""Exporta exclusivamente un heightmap generado por WorldEngine; no crea un motor.

Se ejecuta con Python 3.11 y su entorno propio, sin Landlab instalado.
"""
import hashlib
import json
import sys
import numpy as np
from worldengine.plates import world_gen


def main(path):
    global_seed=1234
    generation_seed=7321
    np.random.seed(global_seed)
    w=world_gen("world-research",32,16,generation_seed,verbose=False)
    elevation=np.asarray(w.layers["elevation"].data,dtype="<f8")
    assert elevation.shape==(16,32)
    assert np.isfinite(elevation).all()
    digest=hashlib.sha256(elevation.tobytes()).hexdigest()
    np.savez_compressed(path,elevation=elevation,
        generator_seed=np.array([generation_seed],dtype=np.int64),
        global_seed=np.array([global_seed],dtype=np.int64))
    print("WORLD_EVAL_JSON "+json.dumps({
        "candidate":"WorldEngine",
        "output_file":path,
        "size":list(elevation.shape),
        "seed":generation_seed,"numpy_global_seed":global_seed,
        "height_min":float(elevation.min()),
        "height_max":float(elevation.max()),
        "height_sha256":digest,
        "meaning":"WorldEngine elevation units are not assumed to be physical meters."
    },sort_keys=True))


if __name__=="__main__":
    main(sys.argv[1])
