"""H12b: read-only AST audit of native dependencies in official DRYP2.

No code execution, no importing upstream modules, no unpacking to working tree.
"""
import ast
import json
import pathlib
import re
import sys
import zipfile
from collections import Counter
from probe_dryp2_archive_static import audit

def inspect(path):
    first=audit(path)  # checks published Zenodo MD5
    imports=Counter()
    roots=set()
    native=[]
    paths=[]
    with zipfile.ZipFile(path) as z:
        allfiles=[i for i in z.infolist() if not i.is_dir()]
        for info in allfiles:
            q=pathlib.PurePosixPath(info.filename)
            if q.suffix.lower() in (".pyd",".so",".dll",".mod",".o",".pyx",".f90"):
                native.append(info.filename)
            if q.suffix.lower()==".py" and info.file_size<=2_000_000:
                paths.append(info.filename)
                roots.add(q.stem)
                if len(q.parts)>1:roots.add(q.parts[1])
                try:
                    source=z.read(info).decode("utf-8-sig")
                    tree=ast.parse(source,filename=info.filename)
                except (UnicodeDecodeError,SyntaxError):
                    continue
                for item in ast.walk(tree):
                    if isinstance(item,ast.Import):
                        for entry in item.names:
                            imports[entry.name.split(".")[0]]+=1
                    if isinstance(item,ast.ImportFrom) and item.module:
                        imports[item.module.split(".")[0]]+=1
    third_party=[
      {"module":name,"import_statements":count}
      for name,count in imports.most_common()
      if name not in sys.stdlib_module_names and name not in roots
      and name not in {"__future__"} and not name.startswith("_")
    ]
    tags=sorted(set(re.findall(r"cpython-([0-9]+)", "\n".join(native),re.I)))
    return {
        "test":"H12b provenance-restricted DRYP2 static dependency and binary audit",
        "MD5_ok":first["md5_matches_published"],
        "SHA256":first["sha256"],
        "python_files":len(paths),
        "third_party_import_roots":third_party[:60],
        "compiled_module_paths":native[:65],
        "compiled_CPython_tags_detected":tags,
        "test_like_paths":[p for p in paths if "test" in p.lower()][:30],
        "driver_like_paths":[p for p in paths if any(k in p.lower() for k in ("run_","main_","model.py","dryp.py"))][:35],
        "source_roots":[p for p in paths if p.count("/")==1][:25],
        "limitations":"AST cannot verify runtime requirements, wheel compatibility, binary ABI, license permissions or successful DRYP simulation. No third-party code was executed."
    }

if __name__=="__main__":
    result=inspect(pathlib.Path(sys.argv[1]))
    print("WORLD_EVAL_JSON "+json.dumps(result,sort_keys=True))
    assert result["python_files"]>0
