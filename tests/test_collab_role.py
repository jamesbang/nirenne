"""協作組隊長／隊員判斷（collab_hook 的 UserPromptSubmit）。
Run with: python3 -m unittest discover -s tests -v"""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a

CTX = {"group": "A", "peer": "web-app", "me": "android-app"}


def peer_msg(body):
    return f'<cross-session-message from-name="web-app-6b">{body}</cross-session-message>'


class CollabRoleTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for p in (patch.object(a, "MGR_HOME", tmp.name), patch.object(a, "still_working", return_value=False)):
            p.start()
            self.addCleanup(p.stop)

    def role(self, prompt, sess):
        upd = {}
        a.collab_hook("UserPromptSubmit", {"prompt": prompt}, sess, upd, 0, CTX)
        return upd.get("COLLAB_ROLE", sess.get("COLLAB_ROLE", ""))

    def test_human_prompt_makes_lead(self):
        self.assertEqual(self.role("幫我修登入", {"COLLAB_ROLE": "support"}), "lead")

    def test_peer_request_or_question_makes_support_when_idle(self):
        # 之前當過隊長、已經做完：夥伴開新的 REQUEST / QUESTION / 沒標籤的訊息 → 這一輪是隊員
        for body in ("[REQ-3][REQUEST] 加一個欄位", "[REQ-3][QUESTION] 你的專案做什麼的？", "請告訴我專案名稱"):
            with self.subTest(body=body):
                self.assertEqual(self.role(peer_msg(body), {"COLLAB_ROLE": "lead"}), "support")

    def test_question_while_leading_keeps_lead(self):
        # 我正在等夥伴回覆時，夥伴反問 → 仍是隊長
        sess = {"COLLAB_ROLE": "lead", "COLLAB_WAIT": "1"}
        self.assertEqual(self.role(peer_msg("[REQ-1][QUESTION] 欄位名稱要用哪個？"), sess), "lead")

    def test_untagged_ack_then_untagged_result_keeps_lead(self):
        # 檢驗員重現的情境：A 交需求給 B → B 回沒標籤的「收到」→ B 回沒標籤的成果，A 應該一直是隊長
        sess = {"COLLAB_ROLE": "lead", "COLLAB_WAIT": "1", "COLLAB_OPEN": "007"}
        upd = {}
        a.collab_hook("UserPromptSubmit", {"prompt": peer_msg("收到，開始處理")}, sess, upd, 0, CTX)
        sess.update(upd)
        self.assertEqual(sess["COLLAB_ROLE"], "lead")
        upd = {}
        a.collab_hook("UserPromptSubmit", {"prompt": peer_msg("做好了，測試都通過")}, sess, upd, 0, CTX)
        self.assertEqual(upd.get("COLLAB_ROLE", sess["COLLAB_ROLE"]), "lead")

    def test_peer_new_request_after_mine_closed_makes_support(self):
        sess = {"COLLAB_ROLE": "lead", "COLLAB_OPEN": "007"}
        upd = {}
        a.collab_hook("UserPromptSubmit", {"prompt": peer_msg("[REQ-007][DONE] 好了")}, sess, upd, 0, CTX)
        self.assertEqual(upd.get("COLLAB_OPEN"), "")
        sess.update(upd)
        self.assertEqual(self.role(peer_msg("[REQ-A1][REQUEST] 換我請你幫忙"), sess), "support")

    def test_peer_new_tagged_request_while_idle_makes_support(self):
        # 我的需求已沒在等（夥伴回了沒標籤的成果，舊編號還留著）：夥伴開了另一個編號 → 隊員
        sess = {"COLLAB_ROLE": "lead", "COLLAB_OPEN": "007"}
        self.assertEqual(self.role(peer_msg("[REQ-A2][QUESTION] 想問你一件事"), sess), "support")

    def test_lead_records_open_request(self):
        sess = {"COLLAB_ROLE": "lead"}
        upd = {}
        data = {"tool_name": "SendMessage", "tool_input": {"to": "web-app-6b", "message": "[REQ-009][REQUEST] 幫忙"}}
        a.collab_hook("PostToolUse", data, sess, upd, 0, CTX)
        self.assertEqual(upd.get("COLLAB_OPEN"), "009")

    def test_done_reply_keeps_role(self):
        sess = {"COLLAB_ROLE": "lead", "COLLAB_WAIT": "1"}
        self.assertEqual(self.role(peer_msg("[REQ-1][DONE] 好了"), sess), "lead")


if __name__ == "__main__":
    unittest.main()
