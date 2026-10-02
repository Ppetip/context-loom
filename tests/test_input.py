# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import tempfile
import unittest
from io_utils import load

class InputTests(unittest.TestCase):
    def test_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "input.json"
            for value in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}'):
                p.write_text(value, encoding="utf-8")
                with self.assertRaises(ValueError): load(p)

    def test_oversized_and_invalid_utf8_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "input.json"
            for raw in (b" " * 1048577, b"\xff"):
                p.write_bytes(raw)
                with self.assertRaises(ValueError): load(p)

    def test_bom_and_valid_json_load_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "input.json"
            raw = b'\xef\xbb\xbf{"valid":true}'
            p.write_bytes(raw)
            self.assertEqual(load(p), {"valid": True})
            self.assertEqual(p.read_bytes(), raw)
