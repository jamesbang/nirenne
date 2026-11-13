#!/usr/bin/env python3
"""產生 README 用的管理畫面示意圖（SVG）：docs/screenshot.zh-TW.svg、docs/screenshot.en.svg。

README 原本用 ASCII 畫框，但中文與 emoji 在各平台字型寬度不一，框線會歪掉；
SVG 中每段文字都以座標定位，不依賴字型寬度，在任何地方顯示都一樣。
修改文字後執行：python3 docs/make_screenshot.py
"""
import os
from html import escape

# 配色與管理工具一致（tmux.conf / agents.py 的 256 色）
BG, PANEL, TEXT, DIM = "#1c1c1c", "#303030", "#dadada", "#949494"
CYAN, YELLOW, GREEN, BLUE, BORDER = "#5fd7ff", "#ffd700", "#5fd787", "#005fd7", "#00afd7"
FONT = ("ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, "
        "'Noto Sans Mono CJK TC', 'PingFang TC', 'Microsoft JhengHei', monospace")

W, H = 960, 510
TOP = 36            # 視窗標題列高度
SIDE = 300          # 左側清單寬度
STATUS_H = 30       # 底部狀態列高度
LH = 24             # 行高

TEXTS = {
    "zh-TW": {
        "window": "nirenne · my-api",
        "party": "⚔ 冒險隊伍", "rest": "[q 休息]", "waiting": "1 位隊員在等你",
        "home": "0 村莊（首頁）",
        "agents": [
            ("1 my-api", "Claude", ("✅ 我好了，你人呢？ (3分12秒)", GREEN), "修正登入逾時", True),
            ("2 web-portal", "Gemini", ("⚔ 戰鬥中 (45秒)", CYAN), "調整首頁排版", False),
            ("3 billing-svc", "Codex", ("✋ 等待你的指示", YELLOW), "新增退款 API", False),
        ],
        "buttons": ["[+ 召喚]  [t 標籤]  [x 離隊]", "[? 手冊]  [l 組隊]  [m 傳話]"],
        "pane_title": " [my-api][Claude] 修正登入逾時 ",
        "pane": [
            ("> 登入超過 30 秒會逾時，幫我找原因並修正", TEXT),
            ("", None),
            ("● 找到原因：token 驗證每次都重新連線資料庫", DIM),
            ("● 修改 src/auth/session.ts，改用連線池", DIM),
            ("● 執行測試：24 passed", GREEN),
            ("", None),
            ("已修正，登入時間從 31 秒降到 0.4 秒。", TEXT),
        ],
        "status_left": "Claude Code v2.1.322 · Opus 5.5   路徑 /home/me/project/my-api   分支 main",
        "status_right": "✅ 1 位隊員在等你",
    },
    "en": {
        "window": "nirenne · my-api",
        "party": "⚔ Party", "rest": "[q Rest]", "waiting": "1 agent is waiting for you",
        "home": "0 Village (home)",
        "agents": [
            ("1 my-api", "Claude", ("✅ Done — your turn (3m12s)", GREEN), "Fix login timeout", True),
            ("2 web-portal", "Gemini", ("⚔ Working (45s)", CYAN), "Tweak home page layout", False),
            ("3 billing-svc", "Codex", ("✋ Waiting for you", YELLOW), "Add refund API", False),
        ],
        "buttons": ["[+ New]   [t Label] [x Leave]", "[? Help]  [l Party] [m Talk]"],
        "pane_title": " [my-api][Claude] Fix login timeout ",
        "pane": [
            ("> Login times out after 30s, find the cause and fix it", TEXT),
            ("", None),
            ("● Cause: token check opens a new DB connection every time", DIM),
            ("● Edited src/auth/session.ts to use the connection pool", DIM),
            ("● Ran tests: 24 passed", GREEN),
            ("", None),
            ("Fixed — login went from 31s to 0.4s.", TEXT),
        ],
        "status_left": "Claude Code v2.1.322 · Opus 5.5   path /home/me/project/my-api   branch main",
        "status_right": "✅ 1 agent is waiting for you",
    },
}


def t(x, y, s, fill=TEXT, size=15, weight="normal", anchor="start"):
    # xml:space="preserve"：保留連續空白（按鈕與狀態列靠空白排版）
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" xml:space="preserve">{escape(s)}</text>')


def build(lang):
    d = TEXTS[lang]
    body_top, body_bot = TOP, H - STATUS_H
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>',
           # 視窗標題列
           f'<path d="M0 10 a10 10 0 0 1 10 -10 h{W - 20} a10 10 0 0 1 10 10 v{TOP - 10} h-{W} z" fill="#2b2b2b"/>']
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{20 + i * 20}" cy="{TOP / 2}" r="6" fill="{c}"/>')
    out.append(t(W / 2, TOP / 2 + 5, d["window"], DIM, 13, anchor="middle"))

    # ---- 左側清單
    x0, y = 14, body_top + 26
    out.append(t(x0, y, d["party"], CYAN, weight="bold"))
    out.append(t(SIDE - 14, y, d["rest"], CYAN, weight="bold", anchor="end"))
    y += LH
    out.append(t(x0, y, d["waiting"], YELLOW))
    y += 12
    out.append(f'<line x1="8" y1="{y}" x2="{SIDE - 8}" y2="{y}" stroke="{DIM}" stroke-width="1"/>')
    y += LH
    out.append(t(x0, y, d["home"], TEXT, weight="bold"))
    y += LH + 8
    for name, kind, (state, color), task, current in d["agents"]:
        if current:
            out.append(f'<rect x="4" y="{y - 17}" width="{SIDE - 8}" height="{LH}" rx="3" fill="{BLUE}"/>')
        out.append(t(x0, y, ("▶" if current else " ") + name, "#ffffff" if current else TEXT, weight="bold"))
        out.append(t(SIDE - 14, y, kind + " ⋮", "#ffffff" if current else TEXT, weight="bold", anchor="end"))
        out.append(t(x0 + 26, y + LH, state, color, weight="bold" if color != CYAN else "normal"))
        out.append(t(x0 + 26, y + LH * 2, task, DIM))
        y += LH * 3 + 10
    by = body_bot - LH * 2 - 12
    out.append(f'<line x1="8" y1="{by - 20}" x2="{SIDE - 8}" y2="{by - 20}" stroke="{DIM}" stroke-width="1"/>')
    for i, b in enumerate(d["buttons"]):
        out.append(t(x0, by + i * LH, b, TEXT, 14))

    # ---- 分隔線與右側 Agent 畫面
    out.append(f'<line x1="{SIDE}" y1="{body_top}" x2="{SIDE}" y2="{body_bot}" stroke="{BORDER}" stroke-width="1.5"/>')
    ty = body_top + 14
    out.append(f'<line x1="{SIDE}" y1="{ty}" x2="{W - 10}" y2="{ty}" stroke="{BORDER}" stroke-width="1.5"/>')
    tw = 10 + len(d["pane_title"]) * (9 if lang == "en" else 12)
    out.append(f'<rect x="{SIDE + 24}" y="{ty - 10}" width="{tw}" height="20" fill="{BG}"/>')
    out.append(t(SIDE + 30, ty + 5, d["pane_title"].strip(), CYAN, 14))
    py = ty + 40
    for line, color in d["pane"]:
        if line:
            out.append(t(SIDE + 24, py, line, color, 14))
        py += LH

    # ---- 底部狀態列
    out.append(f'<path d="M0 {H - STATUS_H} h{W} v{STATUS_H - 10} a10 10 0 0 1 -10 10 h-{W - 20} '
               f'a10 10 0 0 1 -10 -10 z" fill="{PANEL}"/>')
    out.append(t(14, H - 10, d["status_left"], TEXT, 13))
    out.append(t(W - 14, H - 10, d["status_right"], YELLOW, 13, "bold", "end"))
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for lang in TEXTS:
        path = os.path.join(here, f"screenshot.{lang}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(lang))
        print("寫入", path)
