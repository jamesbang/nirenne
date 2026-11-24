"""右鍵選單「複製回覆」：從 Claude 對話紀錄取出回覆與程式碼區塊、只讀這個 Agent 自己專案的紀錄、清理複製內容。
Run with: python3 -m unittest discover -s tests -v"""
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a

SID = "a001adf4-a87b-4085-9946-e7022511f56b"
PARTNER_SID = "11111111-2222-3333-4444-555555555555"


def rec(kind, content, **extra):
    return json.dumps({"type": kind, "message": {"content": content}, **extra}, ensure_ascii=False)


def log(*lines):
    return "\n".join(lines) + "\n"


class ParseTest(unittest.TestCase):
    def test_replies_are_grouped_by_user_prompt(self):
        text = log(
            rec("user", "第一個問題"),
            rec("assistant", [{"type": "thinking", "thinking": "略"}]),
            rec("assistant", [{"type": "text", "text": "先看一下"}]),
            rec("assistant", [{"type": "tool_use", "name": "Bash", "input": {}}]),
            rec("user", [{"type": "tool_result", "content": "ok"}]),      # 工具結果不算新的一輪
            rec("assistant", [{"type": "text", "text": "結果如下"}]),
            rec("user", [{"type": "text", "text": "第二個問題"}]),
            rec("assistant", [{"type": "text", "text": "第二則回覆"}], isSidechain=False),
            rec("assistant", [{"type": "text", "text": "子任務的文字"}], isSidechain=True),
            "{壞掉的一行",
        )
        self.assertEqual(a.load_replies(text), ["先看一下\n\n結果如下", "第二則回覆"])

    def test_system_messages_do_not_split_a_reply(self):
        text = log(
            rec("user", "問題"),
            rec("assistant", [{"type": "text", "text": "前半"}]),
            rec("user", [{"type": "text", "text": "[Request interrupted by user for tool use]"}]),
            rec("user", "<task-notification>done</task-notification>"),
            rec("user", "摘要", isCompactSummary=True),
            rec("user", "<local-command-stdout>x</local-command-stdout>"),
            rec("assistant", [{"type": "text", "text": "後半"}]),
        )
        self.assertEqual(a.load_replies(text), ["前半\n\n後半"])

    def test_codex_replies(self):
        def ev(kind, **p):
            return json.dumps({"type": kind, "payload": p}, ensure_ascii=False)
        text = log(
            ev("session_meta", cwd="/x"),
            ev("event_msg", type="task_started", turn_id="t1"),
            ev("response_item", type="message", role="user", content=[{"type": "input_text", "text": "<environment_context>"}]),
            ev("response_item", type="message", role="user", content=[{"type": "input_text", "text": "問題"}]),
            ev("response_item", type="message", role="assistant", phase="commentary",
               content=[{"type": "output_text", "text": "先看一下"}]),
            ev("response_item", type="custom_tool_call", name="exec"),
            ev("response_item", type="message", role="assistant", phase="final_answer",
               content=[{"type": "output_text", "text": "答案\n```sql\nSELECT 1;\n```"}]),
            ev("event_msg", type="task_complete"),
            ev("event_msg", type="task_started", turn_id="t2"),
            ev("response_item", type="message", role="assistant", content=[{"type": "output_text", "text": "第二則"}]),
        )
        self.assertEqual(a.load_replies(text, "Codex"), ["先看一下\n\n答案\n```sql\nSELECT 1;\n```", "第二則"])

    def test_grok_replies(self):
        def g(kind, content, **extra):
            return json.dumps({"type": kind, "content": content, **extra}, ensure_ascii=False)
        text = log(
            g("system", "You are Grok"),
            g("user", [{"type": "text", "text": "<user_info>OS</user_info>"}]),
            g("user", [{"type": "text", "text": "<user_query>問題</user_query>"}]),
            g("assistant", "我先看一下", tool_calls=[{}]),
            g("tool_result", "ok"),
            g("assistant", "", tool_calls=[{}]),
            g("user", [{"type": "text", "text": "<system-reminder>x</system-reminder>"}]),   # 系統訊息不分輪
            g("assistant", "結果如下"),
            g("user", [{"type": "text", "text": "<user_query>第二個</user_query>"}]),
            g("assistant", "第二則"),
        )
        self.assertEqual(a.load_replies(text, "Grok"), ["我先看一下\n\n結果如下", "第二則"])
        listed = log(g("user", [{"type": "text", "text": "<user_query>q</user_query>"}]),
                     g("assistant", [{"type": "text", "text": "陣列格式"}]))
        self.assertEqual(a.load_replies(listed, "Grok"), ["陣列格式"])

    def test_antigravity_replies(self):
        def st(kind, **f):
            return json.dumps({"type": kind, "status": "DONE", **f}, ensure_ascii=False)
        text = log(
            st("USER_INPUT", source="USER_EXPLICIT", content="<USER_REQUEST> 問題 </USER_REQUEST> <ADDITIONAL_METADATA>"),
            st("PLANNER_RESPONSE", source="MODEL", thinking="想一下", tool_calls=[{}]),
            st("GENERIC", source="MODEL", content="工具輸出，不是回覆"),
            st("PLANNER_RESPONSE", source="MODEL", content="答案\n```sql\nSELECT 1;\n```", thinking="x"),
            st("USER_INPUT", source="USER_EXPLICIT", content="<USER_REQUEST> 第二個 </USER_REQUEST>"),
            st("PLANNER_RESPONSE", source="MODEL", content="第二則"),
        )
        self.assertEqual(a.load_replies(text, "Antigravity"), ["答案\n```sql\nSELECT 1;\n```", "第二則"])
        cut = log(st("USER_INPUT", content="<USER_REQUEST> q </USER_REQUEST>"),
                  st("PLANNER_RESPONSE", content="很長的回覆…", truncated_fields=["content"]))
        self.assertEqual(a.load_replies(cut, "Antigravity"), ["很長的回覆…\n" + a.T("reply_truncated")])

    def test_empty(self):
        self.assertEqual(a.load_replies(""), [])
        self.assertEqual(a.load_replies(None), [])
        self.assertEqual(a.load_replies(log(rec("user", "hi"))), [])

    def test_code_blocks_keep_original_text(self):
        text = ("說明\n  ```sql\n  SELECT a,\n    b\n  FROM t;\n  ```\n其他\n"
                "~~~\nplain\n~~~\n````md\n```inner```\n````")
        self.assertEqual(a.code_blocks(text), [("sql", "SELECT a,\n  b\nFROM t;"), ("", "plain"),
                                               ("md", "```inner```")])

    def test_code_block_edge_cases(self):
        self.assertEqual(a.code_blocks("```py\nx = 1\ny = 2"), [("py", "x = 1\ny = 2")])     # 沒有結尾
        self.assertEqual(a.code_blocks("```\na\n    ```\nb\n```"), [("", "a\n    ```\nb")])  # 縮排 4 格不算結尾
        self.assertEqual(a.code_blocks("```bash``` 是指令\n文字"), [])                         # 不是 fence
        self.assertEqual(a.code_blocks("```\n\n```"), [])                                     # 空區塊略過

    def test_items(self):
        items = a.reply_items("看這段\n```sql\nSELECT 1;\n```")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0][1], "看這段\n```sql\nSELECT 1;\n```")
        self.assertEqual(items[1][1], "SELECT 1;")
        self.assertIn("SELECT 1;", items[1][0])

    def test_safe_text_removes_hidden_and_control_characters(self):
        raw = ("SELECT 1;\x1b[201~rm -rf ~\r\n\tok\u202eabc\u200b\U000e0041\x9b"
               "\u2060\u061c\u3164\u2028x\u2029y")
        self.assertEqual(a.reply_safe(raw), "SELECT 1;[201~rm -rf ~\n\tokabc\nx\ny")


class TranscriptLookupTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = os.path.realpath(tmp.name)
        self.home = os.path.join(self.root, "home")
        self.claude = os.path.join(self.home, ".claude")
        self.sess_dir = os.path.join(self.root, "sessions")
        os.makedirs(self.sess_dir)
        self.sess = os.path.join(self.sess_dir, "s1.env")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
        for p in (patch.dict(os.environ, env, clear=True), patch.object(a, "HOME", self.home),
                  patch.object(a, "valid_session_file", lambda p: p),
                  patch.object(a, "session_path", lambda sid: os.path.join(self.sess_dir, sid + ".env"))):
            p.start()
            self.addCleanup(p.stop)
        self.own = os.path.join(self.root, "own")
        self.partner = os.path.join(self.root, "partner")
        self.win = {"session": "s1", "dir": self.own, "name": "Claude"}

    def set_sid(self, sid):
        with open(self.sess, "w") as f:
            f.write(f"CLAUDE_SID={sid}\n")

    def logdir(self, proj, base=None):
        d = os.path.join(base or self.claude, "projects", re.sub(r"[^A-Za-z0-9]", "-", proj))
        os.makedirs(d, exist_ok=True)
        return d

    def make(self, proj, sid, text, base=None):
        p = os.path.join(self.logdir(proj, base), sid + ".jsonl")
        with open(p, "w") as f:
            f.write(text)
        return p

    def test_reads_this_agents_own_transcript(self):
        self.make(self.own, PARTNER_SID, "OTHER")             # 同資料夾的其他 Claude
        self.make(self.own, SID, "MINE")
        self.set_sid(SID)
        self.assertEqual(a.claude_transcript(self.win), "MINE")

    def test_no_sid_or_bad_sid(self):
        self.make(self.own, SID, "MINE")
        self.assertIsNone(a.claude_transcript(self.win))          # 還沒記下對話編號
        for bad in ("../../etc/passwd", "*", SID + "/../x", ""):
            self.set_sid(bad)
            self.assertIsNone(a.claude_transcript(self.win), bad)

    def test_partner_project_sid_is_not_found(self):
        # 沙箱回報夥伴的對話編號：只在自己專案找，讀不到夥伴的紀錄
        self.make(self.partner, PARTNER_SID, "PARTNER SECRET")
        self.set_sid(PARTNER_SID)
        self.assertIsNone(a.claude_transcript(self.win))

    def test_symlink_or_hardlink_to_partner_is_rejected(self):
        secret = self.make(self.partner, PARTNER_SID, "PARTNER SECRET")
        d = self.logdir(self.own)
        os.symlink(secret, os.path.join(d, SID + ".jsonl"))
        self.set_sid(SID)
        self.assertIsNone(a.claude_transcript(self.win))
        os.unlink(os.path.join(d, SID + ".jsonl"))
        os.link(secret, os.path.join(d, SID + ".jsonl"))
        self.assertIsNone(a.claude_transcript(self.win))

    def test_claude_config_dir_only_outside_party(self):
        custom = os.path.join(self.root, "custom")
        self.make(self.own, SID, "CUSTOM", base=custom)
        self.make(self.own, SID, "HOME")
        self.set_sid(SID)
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": custom}):
            self.assertEqual(a.claude_transcript(self.win), "CUSTOM")
            self.assertEqual(a.claude_transcript(dict(self.win, group="g1")), "HOME")
        os.unlink(os.path.join(self.logdir(self.own, custom), SID + ".jsonl"))
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": custom}):
            self.assertEqual(a.claude_transcript(self.win), "HOME")       # 自訂資料夾沒有：改找 ~/.claude

    def test_codex_and_grok_lookup(self):
        import urllib.parse
        # Codex：$CODEX_HOME/sessions/年/月/日/rollout-*-<編號>.jsonl，編號記在 CODEX_THREAD
        codex = os.path.join(self.root, "codex")
        d = os.path.join(codex, "sessions", "2026", "11", "22")
        os.makedirs(d)
        with open(os.path.join(d, f"rollout-2026-11-22T09-36-33-{SID}.jsonl"), "w") as f:
            f.write("CODEX")
        with open(self.sess, "w") as f:
            f.write(f"CODEX_THREAD={SID}\nCLAUDE_SID={PARTNER_SID}\n")
        with patch.dict(os.environ, {"CODEX_HOME": codex}):
            self.assertEqual(a.claude_transcript(dict(self.win, name="Codex")), "CODEX")
        # Grok：~/.grok/sessions/<專案路徑>/<編號>/chat_history.jsonl，編號記在 CLAUDE_SID
        gd = os.path.join(self.home, ".grok", "sessions", urllib.parse.quote(os.path.realpath(self.own), safe=""),
                          PARTNER_SID)
        os.makedirs(gd)
        with open(os.path.join(gd, "chat_history.jsonl"), "w") as f:
            f.write("GROK")
        self.assertEqual(a.claude_transcript(dict(self.win, name="Grok")), "GROK")
        # 編號不合格式時不找
        with open(self.sess, "w") as f:
            f.write("CODEX_THREAD=../../x\nCLAUDE_SID=*\n")
        with patch.dict(os.environ, {"CODEX_HOME": codex}):
            self.assertIsNone(a.claude_transcript(dict(self.win, name="Codex")))
        self.assertIsNone(a.claude_transcript(dict(self.win, name="Grok")))

    def test_antigravity_lookup(self):
        logs = os.path.join(self.home, ".gemini", "antigravity-cli", "brain", SID, ".system_generated", "logs")
        os.makedirs(logs)
        with open(os.path.join(logs, "transcript.jsonl"), "w") as f:
            f.write("COMPACT")
        with open(self.sess, "w") as f:
            f.write(f"AGY_CONV={SID}\n")
        self.assertEqual(a.claude_transcript(dict(self.win, name="Antigravity")), "COMPACT")
        with open(os.path.join(logs, "transcript_full.jsonl"), "w") as f:
            f.write("FULL")
        self.assertEqual(a.claude_transcript(dict(self.win, name="Antigravity")), "FULL")    # 優先用完整版
        with open(self.sess, "w") as f:
            f.write("AGY_CONV=../x\n")
        self.assertIsNone(a.claude_transcript(dict(self.win, name="Antigravity")))

    def test_party_window_renamed_to_grok_reads_claude_log(self):
        # 組隊中的 Claude 把視窗改名成 Grok：仍只讀 Claude 自己專案的紀錄，不改讀 ~/.grok
        import urllib.parse
        gd = os.path.join(self.home, ".grok", "sessions", urllib.parse.quote(os.path.realpath(self.own), safe=""), SID)
        os.makedirs(gd)
        with open(os.path.join(gd, "chat_history.jsonl"), "w") as f:
            f.write("GROK SECRET")
        self.make(self.own, SID, "MINE")
        self.set_sid(SID)
        self.assertEqual(a.claude_transcript(dict(self.win, name="Grok", group="g1")), "MINE")
        with patch.object(a, "collab_proxy_alive", lambda pane: True):        # 解散後仍在沙箱裡執行
            self.assertEqual(a.claude_transcript(dict(self.win, name="Grok", pane="%1")), "MINE")

    def test_codex_picks_newest_rollout(self):
        codex = os.path.join(self.root, "codex")
        for day, text in (("21", "OLD"), ("22", "NEW")):
            d = os.path.join(codex, "sessions", "2026", "11", day)
            os.makedirs(d)
            with open(os.path.join(d, f"rollout-2026-11-{day}T09-00-00-{SID}.jsonl"), "w") as f:
                f.write(text)
        with open(self.sess, "w") as f:
            f.write(f"CODEX_THREAD={SID}\n")
        with patch.dict(os.environ, {"CODEX_HOME": codex}):
            self.assertEqual(a.claude_transcript(dict(self.win, name="Codex")), "NEW")

    def test_large_transcript_reads_the_end(self):
        line = rec("assistant", [{"type": "text", "text": "x"}])
        with patch.object(a, "REPLY_TAIL_BYTES", 300):
            self.make(self.own, SID, log(*[rec("user", f"q{i}") for i in range(50)], line))
            self.set_sid(SID)
            text = a.claude_transcript(self.win)
        self.assertLessEqual(len(text.encode()), 300)
        self.assertTrue(text.endswith(line + "\n"))
        self.assertEqual(a.load_replies(text), ["x"])


if __name__ == "__main__":
    unittest.main()
