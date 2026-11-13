"""macOS 組隊沙箱設定檔（SBPL）與 L1／L2 的單元測試（在 Linux 上也能跑；不代表 Seatbelt 實際接受這些語法）。
Run with: python3 -m unittest discover -s tests -v"""
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a

STR_RE = re.compile(r'"(?:[^"\\]|\\.)*"')


def sbpl(x):
    return a.sbpl_str(x)


class MacProfileTest(unittest.TestCase):
    def setUp(self):
        # 不放在 /tmp 底下：/tmp 裡的連結目標本來就不會被掛入（claude_shared_items）
        tmp = tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(__file__)))
        self.addCleanup(tmp.cleanup)
        # 家目錄含空白與引號：確認跳脫正確
        self.home = os.path.join(os.path.realpath(tmp.name), 'my "home" dir')
        self.mgr = os.path.join(self.home, ".agent-manager")
        for d in ("work/A", "work/B", ".claude/projects", ".claude/skills", ".claude/sessions", "dotfiles"):
            os.makedirs(os.path.join(self.home, d))
        Path(self.home, ".claude.json").write_text('{"projects": {}}')
        Path(self.home, "dotfiles", "settings.json").write_text("{}")
        os.symlink(os.path.join(self.home, "dotfiles", "settings.json"), os.path.join(self.home, ".claude", "settings.json"))
        for p in (patch.object(a, "HOME", self.home), patch.object(a, "MGR_HOME", self.mgr),
                  patch.object(a, "SANDBOX_ROOT", os.path.join(self.mgr, "sandbox")),
                  patch.dict(os.environ, {"TMPDIR": "/var/folders/xy/T/"})):
            p.start()
            self.addCleanup(p.stop)
        self.A, self.B = os.path.join(self.home, "work", "A"), os.path.join(self.home, "work", "B")
        self.claude_dirs = a.claude_project_dirs(self.B)
        self.cfg, self.shared = a.prepare_claude_config(self.A, self.B, self.claude_dirs)
        a.mac_link_shared(self.shared)
        self.tmux_dir = os.path.join(self.mgr, "run", "collab-bin")
        self.proxy_root = os.path.join(self.mgr, "run", "collab-proxy")
        self.own_proxy = os.path.join(self.proxy_root, "1")
        self.ro_dirs = [self.tmux_dir, self.mgr, os.path.join(self.home, ".ssh")]
        self.ro_files = [os.path.join(self.home, ".zshrc")]
        self.profile = a.mac_sandbox_profile(self.B, self.claude_dirs, self.ro_dirs, self.ro_files, "/private/tmp/tmux-501",
                                             self.proxy_root, self.own_proxy, self.tmux_dir, self.cfg, self.shared)

    def test_syntax_balanced(self):
        rest = STR_RE.sub("S", self.profile)
        self.assertNotIn('"', rest)                       # 每個字串都正確結束（引號有跳脫）
        depth = 0
        for ch in rest:
            depth += {"(": 1, ")": -1}.get(ch, 0)
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)
        self.assertIn(r'my \"home\" dir', self.profile)

    def test_new_rules_present(self):
        p = self.profile
        for exe in a.MAC_DENY_EXEC:
            self.assertIn(f"(literal {sbpl(exe)})", p)
        self.assertIn("(deny process-exec ", p)
        self.assertIn("(deny appleevent-send)(deny lsopen)", p)
        for d in a.MAC_RO_DIRS:
            self.assertIn(f"(subpath {sbpl(os.path.join(self.home, d))})", p)
        for f in a.MAC_RO_FILES:
            self.assertIn(f"(literal {sbpl(os.path.join(self.home, f))})", p)
        self.assertIn(f"(subpath {sbpl(os.path.join(self.home, 'Library/Application Support/Code/User'))})", p)
        # D1：~/.agent-manager、~/.claude、~/.claude.json 不能讀寫
        self.assertIn(f"(deny file-read* file-write* (subpath {sbpl(self.mgr)})", p)
        self.assertIn(f"(literal {sbpl(os.path.join(self.home, '.claude.json'))})", p)
        # D3：夥伴的 Claude 暫存資料夾（/tmp、/private/tmp、$TMPDIR）
        enc = re.sub(r"[^A-Za-z0-9]", "-", self.B)
        for base in ("/tmp", "/private/tmp", "/var/folders/xy/T"):
            self.assertIn(f"(subpath {sbpl(os.path.join(base, f'claude-{os.getuid()}', enc))})", p)
        # 不擋整個 ~/.gradle、~/.m2
        self.assertNotIn(f"(subpath {sbpl(os.path.join(self.home, '.gradle'))})", p)
        self.assertNotIn(f"(subpath {sbpl(os.path.join(self.home, '.m2'))})", p)

    def test_allow_after_deny(self):
        p = self.profile
        deny_mgr = p.index(f"(deny file-read* file-write* (subpath {sbpl(self.mgr)})")
        allow_bin = p.index(f"(allow file-read* (subpath {sbpl(self.tmux_dir)}))")
        allow_cfg = p.index(f"(allow file-read* file-write* (subpath {sbpl(self.cfg)}))")
        # 自己的代理程式資料夾：只能讀與連線，不能寫（不能換成連結或改 pid 檔）
        allow_proxy = p.index(f"(allow file-read* (subpath {sbpl(self.own_proxy)}))")
        self.assertNotIn(f"(allow file-read* file-write* (subpath {sbpl(self.own_proxy)}))", p)
        block = " ".join(f"(subpath {sbpl(x)})" for x in a.path_variants(["/private/tmp/tmux-501", self.proxy_root]))
        deny_proxy_root = p.index(f"(deny file-read* file-write* {block})")
        self.assertLess(deny_mgr, allow_bin)
        self.assertLess(deny_mgr, allow_cfg)
        self.assertLess(deny_proxy_root, allow_proxy)
        # 共用項目：sessions 可讀寫、settings.json（連結目標）唯讀，且都排在禁止 ~/.claude 之後
        sessions = os.path.join(self.home, ".claude", "sessions")
        target = os.path.join(self.home, "dotfiles", "settings.json")
        rw = p.index("(allow file-read* file-write* ", allow_cfg + 1)
        self.assertLess(deny_mgr, rw)
        self.assertIn(f"(subpath {sbpl(sessions)})", p[rw:p.index("(allow file-read* ", rw + 1)])
        allow_ro = p.index("(allow file-read* ", allow_cfg)
        self.assertIn(f"(literal {sbpl(target)})", p[allow_ro:])
        # 最後一條規則：唯讀共用項目禁止寫入；夥伴的禁止排在所有放行之後
        # 唯讀共用項目的禁止寫入排在所有放行之後
        self.assertGreater(p.rindex(f"(literal {sbpl(target)})"), p.rindex("(allow "))
        self.assertGreater(p.rindex("(deny file-write* "), p.rindex("(allow "))
        last_allow = p.rindex("(allow ")
        peer = p.rindex(f"(subpath {sbpl(self.B)})")
        self.assertGreater(peer, last_allow)
        self.assertGreater(p.rindex("(deny file-read* file-write* ", 0, peer), last_allow)

    def test_links_in_private_config(self):
        settings = os.path.join(self.cfg, "settings.json")
        self.assertEqual(os.readlink(settings), os.path.join(self.home, "dotfiles", "settings.json"))
        enc = re.sub(r"[^A-Za-z0-9]", "-", self.A)
        self.assertEqual(os.readlink(os.path.join(self.cfg, "projects", enc)),
                         os.path.join(self.home, ".claude", "projects", enc))
        # 沙箱內把連結換成一般檔案：下次組隊改回連結；真正的資料夾改名保留、不刪除
        os.unlink(settings)
        Path(settings).write_text("tampered")
        sessions = os.path.join(self.cfg, "sessions")
        os.unlink(sessions)
        os.mkdir(sessions)
        Path(sessions, "keep.json").write_text("x")
        a.mac_link_shared(self.shared)
        self.assertTrue(os.path.islink(settings))
        self.assertTrue(os.path.islink(sessions))
        kept = [n for n in os.listdir(self.cfg) if n.startswith("sessions.bak-")]
        self.assertEqual(len(kept), 1)
        self.assertTrue(os.path.exists(os.path.join(self.cfg, kept[0], "keep.json")))

    def test_private_claude_json_only_own_project(self):
        Path(self.home, ".claude.json").write_text(
            '{"projects": {"%s": {"x": 1}, "%s": {"y": 2}}}' % (self.A.replace('"', '\\"'), self.B.replace('"', '\\"')))
        cfg, _ = a.prepare_claude_config(self.A, self.B, self.claude_dirs)
        text = Path(cfg, ".claude.json").read_text()
        self.assertIn('"x": 1', text)
        self.assertNotIn('"y": 2', text)


class ProjectDirsTest(unittest.TestCase):
    """L1：同層資料夾的名稱在專案名稱後接非 ASCII 字元（/w/app中x），編碼後也是 -，要算同層。"""

    def test_non_ascii_sibling(self):
        with tempfile.TemporaryDirectory() as t:
            t = os.path.realpath(t)
            w = os.path.join(t, "w")
            os.makedirs(os.path.join(w, "app"))
            os.makedirs(os.path.join(w, "app中x"))
            enc = re.sub(r"[^A-Za-z0-9]", "-", os.path.join(w, "app"))
            for name in (enc, enc + "-x", enc + "-sub"):
                os.makedirs(os.path.join(t, ".claude", "projects", name))
            with patch.object(a, "HOME", t):
                dirs = {os.path.basename(x) for x in a.claude_project_dirs(os.path.join(w, "app"))}
            self.assertIn(enc, dirs)
            self.assertIn(enc + "-sub", dirs)
            self.assertNotIn(enc + "-x", dirs)          # /w/app中x 的紀錄不算 /w/app 的


class UiLangTest(unittest.TestCase):
    """L2：讀不到設定檔時改用 NIRENNE_UI_LANG；沒有這個變數時照舊（中文）。"""

    def lang(self, env):
        with tempfile.TemporaryDirectory() as t, patch.object(a, "CONFIG_FILE", os.path.join(t, "missing")), \
                patch.dict(a._lang_cache, {"lang": None, "mtime": None}), patch.dict(os.environ, env, clear=False):
            if not env:
                os.environ.pop("NIRENNE_UI_LANG", None)
            return a.ui_lang()

    def test_fallback(self):
        self.assertEqual(self.lang({"NIRENNE_UI_LANG": "en"}), "en")
        self.assertEqual(self.lang({}), "zh-TW")
        self.assertEqual(self.lang({"NIRENNE_UI_LANG": "xx"}), "zh-TW")


class MacAncestorTest(unittest.TestCase):
    """S1：受保護路徑的上層資料夾不能改名或換成連結；S2：Python 載入程式的位置不能寫。"""

    def test_ancestors_exclude_root_and_own_project(self):
        anc = a.path_ancestors(["/Users/x/Documents/Code/B/src", "/Users/x/.config/agent-manager"],
                               own_dir="/Users/x/Documents/Code/A")
        for d in ("/Users/x/Documents/Code/B", "/Users/x/Documents/Code", "/Users/x/Documents", "/Users/x",
                  "/Users/x/.config", "/Users"):
            self.assertIn(d, anc)
        self.assertNotIn("/", anc)
        self.assertFalse(any(x.startswith("/Users/x/Documents/Code/A") for x in anc))

    def test_profile_denies_ancestors_last(self):
        with tempfile.TemporaryDirectory() as t:
            t = os.path.realpath(t)
            peer, own = os.path.join(t, "work", "B"), os.path.join(t, "work", "A")
            pydir = os.path.join(t, "py", "lib", "site-packages")
            for d in (peer, own, pydir):
                os.makedirs(d)
            p = a.mac_sandbox_profile(peer, [], [], [], "", "", "", "", os.path.join(t, "cfg"), [],
                                      py_dirs=[pydir], own_dir=own)
            anc = p[p.rindex("(deny file-write* "):]
            self.assertGreater(p.rindex("(deny file-write* "), p.rindex("(allow "))
            for d in (os.path.join(t, "work"), os.path.join(t, "py", "lib")):
                self.assertIn(f"(literal {sbpl(d)})", anc)
            self.assertNotIn(f"(literal {sbpl(own)})", anc)
            self.assertIn(f"(subpath {sbpl(pydir)})", p)

    def test_python_dirs_skip_own_project_and_home(self):
        with patch.object(a, "HOME", "/Users/x"), \
             patch.object(a.subprocess, "run") as run, patch.object(a.os.path, "exists", return_value=True):
            run.return_value.stdout = '["/Users/x/Documents/Code/A/.venv", "/Users/x", "/opt/py/lib/python3.12"]'
            dirs = a.python_dirs("/Users/x/Documents/Code/A")
        self.assertIn("/opt/py/lib/python3.12", dirs)
        self.assertIn("/Users/x/Library/Python", dirs)
        self.assertNotIn("/Users/x", dirs)
        self.assertNotIn("/Users/x/Documents/Code/A/.venv", dirs)


if __name__ == "__main__":
    unittest.main()
