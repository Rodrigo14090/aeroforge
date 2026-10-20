#!/usr/bin/env python3
"""Restore the original Cloud artifacts and verify every byte against SHA-256."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

base = Path(__file__).resolve().parent
manifest = json.loads((base / 'delivery-manifest.json').read_text())
output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else base / 'dist'
output.mkdir(parents=True, exist_ok=True)
for artifact in manifest['artifacts']:
    name = artifact['name']
    assert Path(name).name == name
    destination = output / name
    digest = hashlib.sha256()
    total = 0
    with destination.open('wb') as target:
        for segment in artifact['segments']:
            source = (base / segment).resolve()
            assert source.is_relative_to(base)
            with source.open('rb') as stream:
                while data := stream.read(1024 * 1024):
                    target.write(data)
                    digest.update(data)
                    total += len(data)
    assert total == artifact['bytes'], name
    assert digest.hexdigest() == artifact['sha256'], name
    print(f'{name}: SHA-256 OK ({total} bytes)')
subprocess.run(['sha256sum', '-c', 'SHA256SUMS'], cwd=output, check=True)
