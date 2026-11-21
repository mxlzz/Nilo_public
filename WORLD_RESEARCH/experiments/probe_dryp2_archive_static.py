"""H12a: metadata-only, read-only audit of the published DRYP 2.0 ZIP.

This script NEVER executes, imports, or extracts upstream code. It only reads
the downloaded Zenodo archive in memory and emits provenance/compatibility
indicators. It does not redistribute source files.

Protocol: WORLD_RESEARCH/ETAPA_0_8_DRYp_ALTERNATIVAS_Y_H11C_PLAN.md
Source: https://doi.org/10.5281/zenodo.17451148
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import sys
import zipfile
from collections import Counter

EXPECTED_MD5 = "f1c491b001755a22c90214d609c0d51b"
MAX_UNCOMPRESSED_BYTES = 100_000_000
MAX_FILE_BYTES = 2_000_000
MAX_FILES = 10_000


def audit(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    md5 = hashlib.md5(data).hexdigest()  # provenance checksum, not security
    sha256 = hashlib.sha256(data).hexdigest()
    if md5 != EXPECTED_MD5:
        raise AssertionError(
            f"Zenodo MD5 mismatch, reject unknown archive: {md5}"
        )
    with zipfile.ZipFile(path) as z:
        files = [v for v in z.infolist() if not v.is_dir()]
        total_bytes = sum(v.file_size for v in files)
        if len(files) > MAX_FILES or total_bytes > MAX_UNCOMPRESSED_BYTES:
            raise AssertionError("Archive too large to audit safely")
        if any(
            pathlib.PurePosixPath(v.filename).is_absolute()
            or ".." in pathlib.PurePosixPath(v.filename).parts
            for v in files
        ):
            raise AssertionError("Archive contains unexpected traversal names")

        modules = []
        syntax_errors = []
        requires = []
        licenses = []
        data_types = Counter()
        for info in files:
            name = info.filename
            suffix = pathlib.PurePosixPath(name).suffix.lower()
            data_types[suffix or "(none)"] += 1
            basename = pathlib.PurePosixPath(name).name.lower()
            if info.file_size > MAX_FILE_BYTES:
                continue
            if suffix == ".py":
                raw = z.read(info)
                try:
                    src = raw.decode("utf-8-sig")
                    compile(src, name, "exec")
                except (UnicodeDecodeError, SyntaxError) as ex:
                    syntax_errors.append({
                        "file":name,"type":type(ex).__name__,
                        "line":getattr(ex,"lineno",None),
                        "description":str(ex)[:200],
                    })
                modules.append(name)
            if basename.startswith(("requirements", "pyproject", "setup.", "environment")):
                requires.append(name)
            if basename in ("license","license.txt","license.md","copying",
                            "license.rst","licence","licence.txt"):
                lines = z.read(info).decode("utf-8",errors="replace").splitlines()
                licenses.append({
                    "file":name,
                    "first_lines":[x[:180] for x in lines[:4]],
                    "contains_mit_label":any("mit license" in x.lower() for x in lines[:12])
                })

        return {
            "test":"H12a source-only static ZIP inspection, not model execution",
            "source":"Zenodo DOI 10.5281/zenodo.17451148",
            "md5_matches_published":True,
            "sha256":sha256,
            "zip_size_bytes":len(data),
            "file_count":len(files),
            "uncompressed_bytes":total_bytes,
            "python_file_count":len(modules),
            "python_syntax_failures":syntax_errors[:25],
            "python_syntax_failure_count":len(syntax_errors),
            "discovered_package_configuration":requires[:40],
            "license_files_inside_zip":licenses[:15],
            "file_type_counts":dict(data_types.most_common(16)),
            "sample_python_paths":modules[:35],
            "notes":"No imports, no dependency resolution, no running external code, and no redistribution. External Zenodo LICENSE credits CornishLeo; provenance requires further review."
        }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: probe_dryp2_archive_static.py /path/dryp.zip")
    output = audit(pathlib.Path(sys.argv[1]))
    print("WORLD_EVAL_JSON " + json.dumps(output,sort_keys=True))
    assert output["python_file_count"]>0, "H12a ZIP contains no Python"
    # Do NOT fail on old syntax: record that evidence for the architecture gate.
