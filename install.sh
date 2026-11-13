#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
CONF_DIR="$HOME/.config/agent-manager"
DATA_DIR="${AGENT_MANAGER_HOME:-$HOME/.agent-manager}"

# 同時辨識舊版入口；符號連結一律保留，避免寫入連結指向的其他檔案。
is_nirenne_entry() {
  [ -f "$1" ] && [ ! -L "$1" ] &&
    grep -Fxq '# 開啟（或接回）多 Agent 管理畫面' "$1" &&
    grep -Fxq 'PY="$HOME/.config/agent-manager/agents.py"' "$1" &&
    grep -Fxq 'SOCK="${AGENTS_TMUX_SOCKET:-agents}"' "$1"
}
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ---- 參數：--lang en｜zh-TW 指定介面語言（安裝訊息與管理畫面都用這個語言，之後仍可在手冊按 g 切換）----
LANG_OPT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --lang) [ "$#" -ge 2 ] || { echo "--lang needs a value: en or zh-TW / --lang 需要指定 en 或 zh-TW" >&2; exit 2; }
            LANG_OPT="$2"; shift 2 ;;
    --lang=*) LANG_OPT="${1#--lang=}"; shift
              [ -n "$LANG_OPT" ] || { echo "--lang needs a value: en or zh-TW / --lang 需要指定 en 或 zh-TW" >&2; exit 2; } ;;
    -h|--help)
      echo "Usage: ./install.sh [--lang en|zh-TW]"
      echo "  --lang  interface language (default: follow the system language) / 介面語言（預設依系統語系）"
      exit 0 ;;
    *) echo "Unknown option: $1 (use --lang en or --lang zh-TW) / 不支援的參數：$1（可用 --lang en 或 --lang zh-TW）" >&2; exit 2 ;;
  esac
done
case "$LANG_OPT" in
  ""|en|zh-TW) ;;
  *) echo "Unsupported language: $LANG_OPT (use en or zh-TW) / 不支援的語言：$LANG_OPT（請用 en 或 zh-TW）" >&2; exit 2 ;;
esac

# 衝突檢查須在複製程式、修改設定之前完成；這裡只查詢語言、不寫入任何檔案。
# 與管理畫面同一套判斷（agents.py detect-lang：已有設定就照設定，否則依系統語系；WSL 會問 Windows 的介面語言）
if [ -n "$LANG_OPT" ]; then AM_LANG="$LANG_OPT"
else AM_LANG="$(AGENT_MANAGER_HOME="$DATA_DIR" python3 -I "$SCRIPT_DIR/agents.py" detect-lang 2>/dev/null || true)"
fi
case "$AM_LANG" in
  en) AM_EN=1 ;;
  zh-TW) AM_EN="" ;;
  *) case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in zh*) AM_EN="" ;; *) AM_EN=1 ;; esac ;;   # 沒有 python3 時
esac
say() { if [ -n "$AM_EN" ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }
# 啟動指令：正式名稱 nirenne，簡稱 agents（同一個啟動程式複製成兩個檔名）。
# 已被其他程式佔用的名稱就跳過、不覆蓋；兩個都被佔用時停止安裝（衝突檢查在任何寫入之前）
ENTRY_NAMES=""
for name in nirenne agents; do
  if { [ -e "$BIN_DIR/$name" ] || [ -L "$BIN_DIR/$name" ]; } && ! is_nirenne_entry "$BIN_DIR/$name"; then
    say "⚠️  $BIN_DIR/$name 已存在，無法確認為 nirenne 的入口；為避免覆蓋，不安裝 $name 這個指令。" \
        "⚠️  $BIN_DIR/$name already exists and could not be identified as nirenne's launcher; the $name command was not installed to avoid overwriting it." >&2
    continue
  fi
  ENTRY_NAMES="$ENTRY_NAMES $name"
  while IFS= read -r entry; do
    [ "$entry" = "$BIN_DIR/$name" ] && continue
    say "⚠️  發現另一個同名指令：$entry。安裝後執行 type -a $name 可確認指令順序。" \
        "⚠️  Another $name command was found: $entry. Run type -a $name after installation to check command precedence."
  done < <(type -a -p "$name" 2>/dev/null || true)
done
if [ -z "$ENTRY_NAMES" ]; then
  say "⚠️  nirenne 與 agents 兩個指令名稱都已被其他程式使用，已停止安裝。請先確認並自行移動或重新命名其中一個。" \
      "⚠️  Both command names, nirenne and agents, are used by other programs. Installation stopped; check them and move or rename one first." >&2
  exit 1
fi
# 只裝上其中一個時：畫面與說明仍會寫 nirenne（或提到可輸入 agents），提醒改用實際裝上的名稱
case "$ENTRY_NAMES" in
  " agents")  say "   畫面與說明中提到 nirenne 時，請改用 agents（nirenne 這個名稱會執行別的程式）。" \
                  "   Wherever the screens and docs say nirenne, use agents instead (the name nirenne runs another program)." >&2 ;;
  " nirenne") say "   請一律使用 nirenne；畫面與說明中提到可以輸入 agents 時，請忽略（agents 這個名稱會執行別的程式）。" \
                  "   Always use nirenne; ignore any mention that agents also works (the name agents runs another program)." >&2 ;;
esac

mkdir -p "$BIN_DIR" "$CONF_DIR"
mkdir -p -m 700 "$DATA_DIR" "$DATA_DIR/sessions" "$DATA_DIR/logs"
chmod 700 "$DATA_DIR" "$DATA_DIR/sessions" "$DATA_DIR/logs" 2>/dev/null || true

# 先複製到暫存檔再改名（原子替換）：執行中的管理畫面每 5 秒檢查一次是否有新版，不會讀到寫一半的檔
install_file() { cp "$1" "$2.tmp.$$" && mv -f "$2.tmp.$$" "$2"; }
install_file "$SCRIPT_DIR/agent-manager.sh" "$CONF_DIR/agent-manager.sh"
install_file "$SCRIPT_DIR/agents.py"        "$CONF_DIR/agents.py"
# tmux.conf 與各 Agent 的 hook 指令改用 Python 的完整路徑（不依 PATH 尋找，PATH 上的同名程式不會被執行到）；
# 路徑含空白等特殊字元時退回 python3
PYBIN="$(command -v python3 2>/dev/null || echo python3)"
case "$PYBIN" in *[!A-Za-z0-9/._+-]*|"") PYBIN=python3 ;; esac
export AM_PYTHON="$PYBIN"
sed "s#python3 #$PYBIN #g" "$SCRIPT_DIR/tmux.conf" > "$CONF_DIR/tmux.conf"
cp "$SCRIPT_DIR/VERSION"          "$CONF_DIR/VERSION"
for name in $ENTRY_NAMES; do
  cp "$SCRIPT_DIR/agents" "$BIN_DIR/$name"
  chmod +x "$BIN_DIR/$name"
done
chmod +x "$CONF_DIR/agents.py"
# 管理畫面的介面語言：有指定 --lang 就照指定寫入（管理畫面開著時立即套用）；
# 否則第一次安裝時依系統語系決定，已有設定則不變（之後在冒險手冊按 g 切換）
if [ -n "$LANG_OPT" ]; then
  AGENT_MANAGER_HOME="$DATA_DIR" python3 -I "$CONF_DIR/agents.py" lang "$LANG_OPT" >/dev/null 2>&1 || true
else
  AGENT_MANAGER_HOME="$DATA_DIR" python3 -I "$CONF_DIR/agents.py" init-lang >/dev/null 2>&1 || true
fi
if grep -qs '^UI_LANG=en$' "$DATA_DIR/config"; then export AM_EN=1; else export AM_EN=""; fi
say() { if [ -n "$AM_EN" ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }

# ---- 依使用的 shell 選擇設定檔：zsh → ~/.zshrc，其他 → ~/.bashrc ----
case "${SHELL:-}" in
  */zsh)  RC="$HOME/.zshrc" ;;
  */bash) RC="$HOME/.bashrc" ;;
  *)      RC="$HOME/.bashrc"
          say "⚠️  目前的 shell 是 ${SHELL:-（未知）}；本工具只支援 bash 與 zsh，設定會寫進 ~/.bashrc，請在 bash 或 zsh 中使用。" \
              "⚠️  Your shell is ${SHELL:-(unknown)}; this tool supports bash and zsh only. Settings go to ~/.bashrc; use it from bash or zsh." ;;
esac
touch "$RC"
# 已加過就不重複加入
if ! grep -Fxq "# >>> nirenne >>>" "$RC" 2>/dev/null; then
  cat >> "$RC" <<'EOF'

# >>> nirenne >>>
export PATH="$HOME/.local/bin:$PATH"
[ -f "$HOME/.config/agent-manager/agent-manager.sh" ] && source "$HOME/.config/agent-manager/agent-manager.sh"
# <<< nirenne <<<
EOF
  say "已在 $RC 加入載入設定" "Added the loader to $RC"
fi

command -v tmux >/dev/null 2>&1 || say "⚠️  找不到 tmux：WSL/Ubuntu 執行 sudo apt install tmux；macOS 執行 brew install tmux" \
  "⚠️  tmux not found: on WSL/Ubuntu run sudo apt install tmux; on macOS run brew install tmux"
command -v python3 >/dev/null 2>&1 || say "⚠️  找不到 python3，請先安裝 Python 3" "⚠️  python3 not found; install Python 3 first"
if [ "$(uname)" = "Linux" ] && ! command -v bwrap >/dev/null 2>&1; then
  say "ℹ️  選用：協作組功能需要 bubblewrap，要使用時再安裝：sudo apt install bubblewrap" \
    "ℹ️  Optional: parties (collaboration groups) need bubblewrap; install it when needed: sudo apt install bubblewrap"
fi

# ---- 各 Agent 的 hooks：回報「等你回覆／工作中」與自動主題 ----
# 只在由管理工具啟動的 Agent 中生效；指令以 `|| true`（或輸出 {}）結尾，hook 壞掉也不會影響 Agent。
# 所有 Agent 共用同一段註冊程式（讀檔、檢查、備份、原子寫入），只有參數不同：
#   $1 顯示名稱  $2 設定檔（~ 開頭）  $3 hook 子指令  $4 格式：events（Claude 式的 hooks 物件）／spec（Antigravity）
#   $5 要註冊的事件（逗號分隔）  $6 需要 matcher "*" 的事件  $7 hook 失敗時的輸出（true 或 echo "{}"）
#   $8 逾時（各 Agent 單位不同：Claude／Codex 是秒，Gemini 是毫秒）  $9／$10 加入成功後的附註（中文／英文，可省略）
register_hooks() {
AM_LABEL="$1" AM_PATH="$2" AM_SUB="$3" AM_STYLE="$4" AM_EVENTS="$5" AM_MATCHER="$6" AM_FALLBACK="$7" \
AM_TIMEOUT="$8" AM_NOTE_ZH="${9:-}" AM_NOTE_EN="${10:-}" python3 - <<'PY'
import json, os, shutil, stat, sys, time
import re as _re
# 本工具 hook 的固定格式（install.sh 產生）：只有完全符合的才當成本工具的 hook 處理
OWN_HOOK_RE = _re.compile(r'test -f "\$HOME/\.config/agent-manager/agents\.py" && (?:python3|/[A-Za-z0-9/._+-]+)(?: -I)? '
                          r'"\$HOME/\.config/agent-manager/agents\.py" (?:claude|codex|gemini|agy)-hook \|\| (?:true|echo "\{\}")')
def is_own_hook(h):
    return (isinstance(h, dict) and set(h) <= {"type", "command", "timeout"} and h.get("type") == "command"
            and isinstance(h.get("command"), str) and OWN_HOOK_RE.fullmatch(h["command"]) is not None)
def looks_like_ours(h):
    return isinstance(h, dict) and "agent-manager/agents.py" in str(h.get("command", "")) and not is_own_hook(h)
EN = bool(os.environ.get("AM_EN"))
E = os.environ
label, path = E["AM_LABEL"], os.path.expanduser(E["AM_PATH"])
real_path = os.path.realpath(path)
os.makedirs(os.path.dirname(real_path), mode=0o700, exist_ok=True)
data = {}
mode = 0o600
if os.path.exists(real_path):
    mode = stat.S_IMODE(os.stat(real_path).st_mode) or 0o600
    with open(real_path, encoding="utf-8", errors="replace") as f:
        txt = f.read().strip()
    if txt:
        try:
            data = json.loads(txt)
        except ValueError as e:
            print(f"⚠️  Skipped {path}: invalid JSON ({e})" if EN else f"⚠️  略過 {path}：JSON 格式有誤（{e}）")
            sys.exit(0)
if not isinstance(data, dict):
    print(f"⚠️  Skipped {path}: top-level JSON is not an object" if EN else f"⚠️  略過 {path}：最外層不是 JSON 物件")
    sys.exit(0)
CMD = ('test -f "$HOME/.config/agent-manager/agents.py" && '
       f'{E.get("AM_PYTHON") or "python3"} -I "$HOME/.config/agent-manager/agents.py" {E["AM_SUB"]} || {E["AM_FALLBACK"]}')
handler = {"type": "command", "command": CMD, "timeout": int(E["AM_TIMEOUT"])}
events = [x for x in E["AM_EVENTS"].split(",") if x]
with_matcher = {x for x in E["AM_MATCHER"].split(",") if x}
changed = False
if E["AM_STYLE"] == "spec":
    spec = {ev: ([{"matcher": "*", "hooks": [handler]}] if ev in with_matcher else [handler]) for ev in events}
    if data.get("agent-manager") != spec:
        data["agent-manager"] = spec
        changed = True
else:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks
    # 先移除舊版留下的本工具 hooks（與 uninstall.sh 相同的判斷：指令含 agent-manager/agents.py），
    # 指令或事件清單日後改了，舊的才不會殘留而讓 hook 執行兩次
    for ev in list(hooks):
        if not isinstance(hooks[ev], list):
            continue
        kept = []
        for g in hooks[ev]:
            if isinstance(g, dict) and isinstance(g.get("hooks"), list):
                hs = [h for h in g["hooks"] if not (is_own_hook(h) and (h.get("command") != CMD or ev not in events))]
                for h in g["hooks"]:
                    if looks_like_ours(h):
                        print(f"⚠️  {path} 的 {ev} 有一個提到 agent-manager/agents.py、但格式不是本工具產生的 hook，已保留，請自行確認：{h.get('command')}"
                              if not EN else f"⚠️  Kept a {ev} hook in {path} that mentions agent-manager/agents.py but is not in this tool's format; please check it: {h.get('command')}")
                if len(hs) != len(g["hooks"]):
                    changed = True
                if not hs:
                    continue
                g = {**g, "hooks": hs}
            kept.append(g)
        if kept:
            hooks[ev] = kept
        else:
            del hooks[ev]
    for ev in events:
        groups = hooks.get(ev)
        if not isinstance(groups, list):
            groups = []
            hooks[ev] = groups
        if any(isinstance(g, dict) and isinstance(g.get("hooks"), list)
               and any(isinstance(h, dict) and h.get("command") == CMD for h in g["hooks"])
               for g in groups):
            continue
        g = {"hooks": [dict(handler)]}
        if ev in with_matcher:
            g = {"matcher": "*", **g}
        groups.append(g)
        changed = True
if changed:
    if os.path.exists(real_path):
        bak = f"{path}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(real_path, bak)
        os.chmod(bak, mode)
        print(f"Backed up {label} settings: {bak}" if EN else f"已備份 {label} 設定：{bak}")
    tmp = f"{real_path}.tmp{os.getpid()}"
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, real_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    note = E.get("AM_NOTE_EN" if EN else "AM_NOTE_ZH", "")
    print(f"Added Agent Manager hooks to {E['AM_PATH']}{note}" if EN
          else f"已在 {E['AM_PATH']} 加入 Agent Manager hooks{note}")
else:
    print(f"{label} hooks already present, skipped" if EN else f"{label} hooks 已存在，略過")
PY
}

register_hooks "Claude" "~/.claude/settings.json" claude-hook events \
  "SessionStart,UserPromptSubmit,PreToolUse,PostToolUse,PermissionRequest,Notification,Stop,SubagentStop" \
  "PreToolUse,PostToolUse,PermissionRequest" true 5
# Codex：格式與 Claude 相同
if command -v codex >/dev/null 2>&1; then
  register_hooks "Codex" "~/.codex/hooks.json" codex-hook events \
    "SessionStart,UserPromptSubmit,PermissionRequest,PreToolUse,PostToolUse,Stop" \
    "PreToolUse,PostToolUse,PermissionRequest" true 5 \
    "（第一次啟動 Codex 時可能需要你同意信任這些 hooks）" " (Codex may ask you to trust them on first start)"
fi
# Gemini CLI：寫在 ~/.gemini/settings.json 的 hooks；輸出必須是 JSON，逾時單位是毫秒；工具事件不加 matcher（代表全部）
if command -v gemini >/dev/null 2>&1; then
  register_hooks "Gemini" "~/.gemini/settings.json" gemini-hook events \
    "SessionStart,BeforeAgent,AfterAgent,BeforeTool,AfterTool,Notification" "" 'echo "{}"' 5000
fi
# Antigravity：依官方規格寫入 ~/.gemini/config/hooks.json 的 "agent-manager"
if command -v agy >/dev/null 2>&1; then
  register_hooks "Antigravity" "~/.gemini/config/hooks.json" agy-hook spec \
    "SessionStart,PreInvocation,PostToolUse,Stop" "PostToolUse" 'echo "{}"' 5
fi

case "$RC" in "$HOME"/*) RC_SHOW="~${RC#"$HOME"}" ;; *) RC_SHOW="$RC" ;; esac   # 顯示成 ~/.zshrc 這種寫法
MAIN_CMD="${ENTRY_NAMES# }"; MAIN_CMD="${MAIN_CMD%% *}"   # 正式名稱 nirenne；被佔用時是 agents
case "$ENTRY_NAMES" in *nirenne*agents*) ALSO_EN="  (the shorter agents also works)"; ALSO_ZH="（也可以輸入較短的 agents）" ;; *) ALSO_EN=""; ALSO_ZH="" ;; esac
if [ -n "$AM_EN" ]; then
cat <<EOF

Installation complete. To start using it, open a new terminal tab,
or run this in the current window:
  source $RC_SHOW

Commands:
  $(printf '%-20s' "$MAIN_CMD") open the multi-agent manager$ALSO_EN
  $(printf '%-20s' "$MAIN_CMD stop") stop the manager and every agent in it
  $(printf '%-20s' "$MAIN_CMD --help") show the manager's usage
  agent-help           list all commands

Your usual workflow still works: cd into a project and run claude / codex / gemini / agy / grok.
The manager's language can be switched in its handbook ([? Help], then g).
EOF
exit 0
fi
cat <<EOF

安裝完成。請開新的終端機分頁，或在目前的視窗執行下面這行，就能開始使用：
  source $RC_SHOW

指令：
  $(printf '%-20s' "$MAIN_CMD") 開啟多 Agent 管理畫面$ALSO_ZH
  $(printf '%-20s' "$MAIN_CMD stop") 結束管理畫面與其中所有 Agent
  $(printf '%-20s' "$MAIN_CMD --help") 顯示管理畫面的用法
  agent-help           查看所有指令

原本的用法不變：cd 專案目錄後輸入 claude / codex / gemini / agy / grok。
管理畫面的介面語系可在冒險手冊（[? 手冊]）按 g 切換。
EOF
