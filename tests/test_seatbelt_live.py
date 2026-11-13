"""macOS 組隊沙箱的實機測試：用 sandbox-exec 實際執行產生的設定檔（只在 macOS 執行，其他系統略過）。
單元測試只能檢查設定檔的文字，這裡確認 Seatbelt 真的接受這些語法，而且擋得住。
全部在暫存資料夾裡進行，不會動到真正的設定。
Run with: python3 -m unittest discover -s tests -v"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("sandbox-exec"), "只在 macOS 執行")
class SeatbeltLiveTest(unittest.TestCase):
    def setUp(self):
        # 放在家目錄底下（不放 /tmp）：比較接近實際使用的位置
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="nirenne-seatbelt-", dir=os.path.expanduser("~")))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.own = os.path.join(self.base, "work", "A")
        self.peer = os.path.join(self.base, "work", "B")
        self.conf = os.path.join(self.base, "cfgroot", "agent-manager")
        self.py = os.path.join(self.base, "py", "site-packages")
        for d in (self.own, self.peer, self.conf, self.py):
            os.makedirs(d)
        with open(os.path.join(self.peer, "secret.txt"), "w") as f:
            f.write("secret")
        with open(os.path.join(self.conf, "agents.py"), "w") as f:
            f.write("real")
        self.profile = a.mac_sandbox_profile(self.peer, [], [self.conf], [], "", "", "", "",
                                             os.path.join(self.base, "cfg"), [], py_dirs=[self.py], own_dir=self.own)

    def sh(self, cmd):
        r = subprocess.run(["sandbox-exec", "-p", self.profile, "/bin/sh", "-c", cmd],
                           capture_output=True, text=True, cwd=self.own, timeout=30)
        return r.returncode == 0, r.stdout + r.stderr

    def test_profile_is_accepted(self):
        ok, out = self.sh("true")
        self.assertTrue(ok, out)

    def test_peer_project_is_blocked(self):
        self.assertFalse(self.sh(f"cat '{self.peer}/secret.txt'")[0])
        self.assertFalse(self.sh(f"echo x > '{self.peer}/new.txt'")[0])
        self.assertFalse(self.sh(f"ls '{self.peer}'")[0])

    def test_protected_folder_is_read_only(self):
        self.assertFalse(self.sh(f"echo x > '{self.conf}/agents.py'")[0])
        self.assertFalse(self.sh(f"touch '{self.py}/evil.pth'")[0])

    def test_parent_rename_and_link_swap_are_blocked(self):
        # 把上層改名、刪掉換成連結：之前可用來讓沙箱外執行假的程式，或改名後讀夥伴的專案
        self.assertFalse(self.sh(f"mv '{self.base}/cfgroot' '{self.base}/cfgroot.bak'")[0])
        self.assertFalse(self.sh(f"mv '{self.base}/work' '{self.base}/work2'")[0])
        self.sh(f"mkdir -p '{self.base}/x/agent-manager' && rm -rf '{self.base}/cfgroot' && ln -s '{self.base}/x' '{self.base}/cfgroot'")
        with open(os.path.join(self.conf, "agents.py")) as f:
            self.assertEqual(f.read(), "real")

    def test_normal_work_is_allowed(self):
        ok, out = self.sh(f"echo x > f.txt && mkdir d && mv d d2 && echo y > '{self.base}/work/new.txt'")
        self.assertTrue(ok, out)


if __name__ == "__main__":
    unittest.main()
