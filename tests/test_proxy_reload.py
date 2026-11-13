"""自動換版：偵測 agents.py 更新（code_ready_to_reload）與實際載入檢查（code_selfcheck）。
Run with: python3 -m unittest discover -s tests -v"""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a

GOOD = "import sys\nif sys.argv[1:] == ['selfcheck']:\n    print('ok')\n"
# 能編譯、但一載入就出錯（例如 3.10 才支援的寫法在 3.9 上）
BROKEN_AT_LOAD = "raise TypeError('unsupported operand')\n"


class ProxyReloadTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.src = os.path.join(tmp.name, "agents.py")
        self.write(GOOD, age=10)
        for p in (patch.object(a, "SELF", self.src), patch.object(a, "_selfcheck_cache", {}),
                  patch.object(a, "hook_log")):
            p.start()
            self.addCleanup(p.stop)
        self.sig = a.code_signature()

    def write(self, text, age):
        with open(self.src, "w") as f:
            f.write(text)
        t = time.time() - age
        os.utime(self.src, (t, t))

    def test_unchanged_does_not_reload(self):
        self.assertIsNone(a.code_ready_to_reload(self.sig))

    def test_updated_and_loadable_reloads(self):
        self.write(GOOD + "# v2\n", age=10)
        self.assertEqual(a.code_ready_to_reload(self.sig), a.code_signature())

    def test_just_written_waits(self):
        self.write(GOOD + "# v2\n", age=0)
        self.assertIsNone(a.code_ready_to_reload(self.sig))

    def test_syntax_error_keeps_old_code(self):
        self.write("def broken(:\n", age=10)
        self.assertIsNone(a.code_ready_to_reload(self.sig))

    def test_fails_at_load_keeps_old_code(self):
        self.write(BROKEN_AT_LOAD, age=10)
        self.assertIsNone(a.code_ready_to_reload(self.sig))

    def test_failed_version_is_checked_once(self):
        self.write(BROKEN_AT_LOAD, age=10)
        with patch.object(a.subprocess, "run", wraps=a.subprocess.run) as run:
            a.code_ready_to_reload(self.sig)
            a.code_ready_to_reload(self.sig)
        self.assertEqual(run.call_count, 1)

    def test_missing_file_keeps_old_code(self):
        os.unlink(self.src)
        self.assertIsNone(a.code_ready_to_reload(self.sig))


if __name__ == "__main__":
    unittest.main()
