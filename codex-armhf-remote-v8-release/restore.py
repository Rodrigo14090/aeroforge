#!/usr/bin/env python3
"""Restore exact, previously tested Cloud files, without rebuilding binaries."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
manifest=json.loads((root/'delivery-manifest.json').read_text())
out=Path(sys.argv[1] if len(sys.argv)>1 else root/'dist')
out.mkdir(parents=True,exist_ok=True)
for entry in manifest['files']:
    target=out/entry['name']
    if target.exists():raise FileExistsError(f'Refusing to overwrite {target}')
    size=0
    sha=hashlib.sha256()
    with target.open('xb') as dst:
        for part in entry['parts']:
            with (root/part).open('rb') as src:
                while block:=src.read(1024*1024):
                    dst.write(block);sha.update(block);size+=len(block)
    assert size==entry['bytes'] and sha.hexdigest()==entry['sha256'],entry['name']
    print(f"Verified {entry['name']} ({size} bytes)")
subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=out,check=True)
