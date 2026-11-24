"""複製提示（copied）：用真的 tmux 驗證右下角「已複製 N 行」的行數。
沒有 tmux 時略過。Run with: python3 -m unittest discover -s tests -v"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a

TMUX = shutil.which("tmux")
LINES = [f"line {i:03d}" for i in range(120)]


@unittest.skipUnless(TMUX, "tmux not installed")
class CopiedNoticeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.out = os.path.join(self.dir, "out.txt")
        self.sock = f"nirenne-test-{os.getpid()}"
        for p in (patch.object(a, "SOCKET", self.sock), patch.object(a, "TMUX_BIN", TMUX)):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.t, "kill-server")

    # ---- 輔助
    def start(self, lines, then="", width=80, ready=None):
        """開一個窗格印出 lines（之後執行 then），等內容印完後進入選取模式並捲到最上面。"""
        src = os.path.join(self.dir, "lines.txt")
        with open(src, "w") as f:
            f.write("\n".join(lines) + "\n")
        conf = os.path.join(self.dir, "tmux.conf")
        with open(conf, "w") as f:
            f.write(f"set -g history-limit 50000\nset -s copy-command 'cat > {self.out}'\n")
        self.t("-f", conf, "new-session", "-d", "-s", "t", "-x", str(width), "-y", "20",
               f"cat {src}; {then} exec sleep 600")
        ready = ready or lines[-1]
        for _ in range(200):
            if ready in self.t("capture-pane", "-p", "-t", "t"):
                break
            time.sleep(0.05)
        self.pane = self.t("display", "-p", "-t", "t", "#{pane_id}").strip()
        self.t("copy-mode", "-t", self.pane)
        self.keys("history-top")

    def t(self, *args):
        return subprocess.run([TMUX, "-L", self.sock, *args], capture_output=True, text=True).stdout

    def keys(self, *args):
        self.t("send-keys", "-t", self.pane, "-X", *args)

    def fmt(self, f):
        return self.t("display", "-p", "-t", self.pane, f).strip()

    def copied(self):
        for _ in range(60):
            if os.path.exists(self.out) and os.path.getsize(self.out):
                break
            time.sleep(0.05)
        with open(self.out) as f:
            return f.read().split("\n")

    # ---- 複製提示
    def test_copied_notice_counts_lines_of_new_buffer(self):
        self.start(LINES)
        self.t("set-buffer", "a\nb\nc\n")
        with patch.object(a.os, "fork", return_value=1):
            a.copied_notice("")
        self.assertEqual(self.t("show-option", "-gqv", "@copied_msg").strip(), a.T("copied_n", n=3))

    def test_copied_notice_skips_when_nothing_new(self):
        self.start(LINES)
        with patch.object(a.os, "fork", return_value=1):
            a.copied_notice("")                     # 沒有任何複製內容
        self.assertEqual(self.t("show-option", "-gqv", "@copied_msg").strip(), "")


if __name__ == "__main__":
    unittest.main()
