"""文字視窗的換行（wrap_text）：英文單字不切開、標點不放行首、左括號不留行尾、手冊兩欄的續行對齊。
並用固定種子的隨機字串檢查兩個不變式：不丟字（非空白字元一致）、每一行不超過寬度。
Run with: python3 -m unittest discover -s tests -v"""
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents as a


def visible(s):
    return "".join(ch for ch in s if not ch.isspace() and ch != a.HELP_COL and ch >= " ")


class WrapTextTest(unittest.TestCase):
    def wrap(self, text, width, columns=False):
        out = a.wrap_text(text, width, columns)
        self.assertEqual(visible("".join(out)), visible(text.expandtabs(4)), out)
        for line in out:
            self.assertLessEqual(a.str_w(line), max(width, 4), out)
        return out

    def test_english_words_are_not_split(self):
        self.assertEqual(self.wrap("Pair two Claude agents into a party (Claude only), or disband (restarts both)", 40),
                         ["Pair two Claude agents into a party", "(Claude only), or disband (restarts", "both)"])
        self.assertEqual(self.wrap("a" * 10, 4), ["aaaa", "aaaa", "aa"])       # 沒有空白的長字照舊切開
        self.assertEqual(self.wrap("word,", 4), ["word", ","])                 # 放不下時退回逐字

    def test_chinese_and_punctuation(self):
        self.assertEqual(self.wrap("中文中文，。", 6), ["中文中", "文，。"])
        self.assertEqual(self.wrap("右鍵選「喝下忘卻藥水」。", 22), ["右鍵選「喝下忘卻藥", "水」。"])
        self.wrap("，" * 50, 6)                                                # 全是標點：不卡住、不丟字

    def test_punctuation_after_space_or_english(self):
        for line in self.wrap("abc 、。def", 6)[1:]:
            self.assertFalse(line.startswith(" "))
        self.assertTrue(any("hello，world" in x or "hello，" in x for x in self.wrap("xx hello，world", 8)))
        self.assertTrue(any("README.md。" in x for x in self.wrap("see README.md。下一句", 14)))

    def test_runs_of_spaces_at_the_break(self):
        self.assertEqual(self.wrap("aaaa\tbbbb", 5), ["aaaa", "bbbb"])
        self.assertEqual(self.wrap("aaaa  bbbb", 5), ["aaaa", "bbbb"])
        self.assertEqual(self.wrap("中文中文   下一句", 8), ["中文中文", "下一句"])
        out = self.wrap("   abc def ghi jkl", 9)
        self.assertEqual(out[0], "   abc")
        self.assertTrue(all(x.startswith("     ") and x[5] != " " for x in out[1:]), out)

    def test_blank_lines_are_kept(self):
        self.assertEqual(a.wrap_text(" " * 20, 5), [""])
        self.assertEqual(a.wrap_text("\t\t\t", 5), [""])
        self.assertEqual(a.wrap_text("a\n" + " " * 20 + "\nb", 5), ["a", "", "b"])

    def test_open_bracket_not_at_line_end(self):
        for line in self.wrap("foo（bar）baz", 6):
            self.assertFalse(line.endswith("（"))

    def test_indented_continuation(self):
        out = self.wrap("   indented line with several words that will wrap around here", 30)
        self.assertTrue(all(x.startswith("     ") for x in out[1:]))

    def test_help_columns(self):
        self.assertEqual(a.wrap_text("x\x1fy", 20), ["xy"])                    # 一般視窗：分界記號被濾掉
        label = "   k" + " " * 5
        out = self.wrap(label + a.HELP_COL + "說明很長" * 10, 30, True)
        self.assertTrue(all(x.startswith(" " * len(label)) and x[len(label)] != " " for x in out[1:]), out)
        out = self.wrap("k" * 15 + a.HELP_COL + "d " * 30, 20, True)          # 說明欄太靠右：改用一般縮排
        self.assertTrue(all(not x.startswith(" " * 15) for x in out[1:]), out)

    def test_random_invariants(self):
        rnd = random.Random(20261122)
        pool = ["\n"] + list("abcdefg ") * 3 + list("中文字測試") + list("，。、」「（）,.!?") + ["\t", "\x1f", "😀", "  "]
        for _ in range(2000):
            text = "".join(rnd.choice(pool) for _ in range(rnd.randint(0, 60)))
            width, columns = rnd.randint(1, 30), rnd.random() < 0.5
            out = self.wrap(text, width, columns)
            self.assertGreaterEqual(len(out), text.count("\n") + 1)       # 每一行原文至少輸出一行
            # 單行原文換行後，續行不會是空白行（含換行的原文本來就可能有空行）
            if "\n" not in text and text.strip():
                for line in out[1:]:
                    self.assertTrue(line.strip(), (text, width, out))


if __name__ == "__main__":
    unittest.main()
