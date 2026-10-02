# SPDX-License-Identifier: GPL-3.0-only
"""Exercise offline CLI contracts with public synthetic fixtures only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

def invoke(args, expected=0):
    process = subprocess.run([sys.executable, str(ROOT / "app.py"), *args], cwd=ROOT,
                             capture_output=True, text=True, timeout=15)
    assert process.returncode == expected, (process.returncode, process.stderr)
    if expected == 2:
        assert not process.stdout
        return None
    return json.loads(process.stdout)

report = invoke(["--input", "examples/demo.json"])
assert report["optimized"]["total_value"] == 13
assert report["optimized"]["used_units"] == 10
assert report["first_fit"]["total_value"] == 6
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "invalid.json"
    path.write_text('{"budget":true,"chunks":[]}', encoding="utf-8")
    invoke(["--input", str(path)], 2)
    assert path.read_text(encoding="utf-8") == '{"budget":true,"chunks":[]}'
    invoke(["--input", str(Path(directory) / "missing.json")], 2)
print("3 offline CLI contracts passed; synthetic packing evidence only")
