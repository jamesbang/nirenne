#!/usr/bin/env bash
# 移除 nirenne：還原 shell 設定與 Claude hooks、刪除已安裝的程式。
set -euo pipefail

CONF_DIR="$HOME/.config/agent-manager"

# 同時辨識舊版入口；符號連結一律保留，避免寫入連結指向的其他檔案。
is_nirenne_entry() {
  [ -f "$1" ] && [ ! -L "$1" ] &&
    grep -Fxq '# 開啟（或接回）多 Agent 管理畫面' "$1" &&
    grep -Fxq 'PY="$HOME/.config/agent-manager/agents.py"' "$1" &&
    grep -Fxq 'SOCK="${AGENTS_TMUX_SOCKET:-agents}"' "$1"
}
DATA_DIR="${AGENT_MANAGER_HOME:-$HOME/.agent-manager}"
if grep -qs '^UI_LANG=en$' "$DATA_DIR/config"; then export AM_EN=1; else export AM_EN=""; fi
say() { if [ -n "$AM_EN" ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }

# 1. 管理畫面若還在執行，先詢問是否結束
if command -v tmux >/dev/null 2>&1 && tmux -L "${AGENTS_TMUX_SOCKET:-agents}" has-session -t agents 2>/dev/null; then
  read -r -p "$(say "管理畫面（nirenne）仍在執行，要結束其中所有 Agent 嗎？(y/N) " "The manager (nirenne) is still running. End every agent in it? (y/N) ")" a || a=""
  case "$a" in      # 全形 ｙ 也算（中文輸入法開著時）；不呼叫 agents.py：移除時它可能已經壞掉
    y|Y|ｙ|Ｙ) tmux -L "${AGENTS_TMUX_SOCKET:-agents}" kill-server ;;
    *) say "已取消。請先結束管理畫面再移除。" "Cancelled. Stop the manager before uninstalling."; exit 1 ;;
  esac
fi

# 2. 從 shell 設定檔移除載入區塊（先備份，且確認起訖標記成對且順序正確才移除，避免誤刪後續設定）
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -f "$RC" ] || continue
  if grep -qx "# >>> nirenne >>>" "$RC"; then
    if awk '/^# >>> nirenne >>>$/{if (s) exit 1; s=1; f=1; next} /^# <<< nirenne <<<$/{if (!s) exit 1; s=0; next} END{if (!f || s) exit 1}' "$RC"; then
      REAL_RC="$(python3 -I -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$RC")"
      cp -p "$REAL_RC" "$RC.bak-$(date +%Y%m%d-%H%M%S)"
      cp -p "$REAL_RC" "$REAL_RC.tmp.$$"
      if awk '/^# >>> nirenne >>>$/{skip=1} !skip{print} /^# <<< nirenne <<<$/{skip=0}' "$REAL_RC" > "$REAL_RC.tmp.$$"; then
        mv -f "$REAL_RC.tmp.$$" "$REAL_RC"
        say "已從 $RC 移除載入設定（已備份）" "Removed the loader from $RC (backup kept)"
      else
        rm -f "$REAL_RC.tmp.$$"
      fi
    else
      say "⚠️  $RC 缺少結尾標記 (# <<< nirenne <<<)，為避免誤刪其他設定，請手動移除。" \
          "⚠️  $RC is missing the closing marker (# <<< nirenne <<<); please remove the block by hand."
    fi
  fi
done

# 3. 從 Claude / Codex / Gemini 設定移除 hooks（先備份，並保留符號連結與檔案權限）
python3 -I - <<'PY'
import json, os, shutil, stat, time
import re as _re
# 本工具 hook 的固定格式（install.sh 產生）：只有完全符合的才當成本工具的 hook 刪除
OWN_HOOK_RE = _re.compile(r'test -f "\$HOME/\.config/agent-manager/agents\.py" && (?:python3|/[A-Za-z0-9/._+-]+)(?: -I)? '
                          r'"\$HOME/\.config/agent-manager/agents\.py" (?:claude|codex|gemini|agy)-hook \|\| (?:true|echo "\{\}")')
def is_own_hook(h):
    return (isinstance(h, dict) and set(h) <= {"type", "command", "timeout"} and h.get("type") == "command"
            and isinstance(h.get("command"), str) and OWN_HOOK_RE.fullmatch(h["command"]) is not None)
def looks_like_ours(h):
    return isinstance(h, dict) and "agent-manager/agents.py" in str(h.get("command", "")) and not is_own_hook(h)
EN = bool(os.environ.get("AM_EN"))
for path in [os.path.expanduser("~/.claude/settings.json"), os.path.expanduser("~/.codex/hooks.json"),
             os.path.expanduser("~/.gemini/settings.json")]:
    real_path = os.path.realpath(path)
    if not os.path.exists(real_path):
        continue
    mode = stat.S_IMODE(os.stat(real_path).st_mode) or 0o600
    with open(real_path, encoding="utf-8", errors="replace") as f:
        txt = f.read().strip()
    if not txt:
        continue
    try:
        data = json.loads(txt)
    except ValueError as e:
        print(f"⚠️  Skipped {path}: invalid JSON ({e})" if EN else f"⚠️  略過 {path}：JSON 格式有誤（{e}）")
        continue
    if not isinstance(data, dict):
        continue
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        continue
    changed = False
    for ev in list(hooks):
        if not isinstance(hooks[ev], list):
            continue
        groups = []
        for g in hooks[ev]:
            if not isinstance(g, dict) or not isinstance(g.get("hooks"), list):
                groups.append(g)
                continue
            hs = [h for h in g["hooks"] if not is_own_hook(h)]
            for h in g["hooks"]:
                if looks_like_ours(h):
                    print(f"⚠️  Kept a {ev} hook in {path} that mentions agent-manager/agents.py but is not in this tool's format; please check it: {h.get('command')}"
                          if EN else f"⚠️  {path} 的 {ev} 有一個提到 agent-manager/agents.py、但格式不是本工具產生的 hook，已保留，請自行確認：{h.get('command')}")
            if len(hs) != len(g["hooks"]):
                changed = True
            if hs:
                groups.append({**g, "hooks": hs})
        if groups:
            hooks[ev] = groups
        else:
            del hooks[ev]
    if not hooks:
        data.pop("hooks", None)
    if changed:
        bak = f"{path}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(real_path, bak)
        os.chmod(bak, mode)
        if not data:
            # 移除 hooks 後是空的設定檔（多半是安裝時新建的）：直接刪除，不留下 {}（原內容仍在 .bak 備份）
            os.remove(real_path)
            print(f"Removed {path} (it only contained our hooks; backup kept)" if EN
                  else f"已刪除 {path}（裡面只有本工具的 hooks；已備份）")
            continue
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
        print(f"Removed hooks from {path} (backup kept)" if EN else f"已從 {path} 移除 hooks（已備份）")

agy_path = os.path.expanduser("~/.gemini/config/hooks.json")
real_agy = os.path.realpath(agy_path)
if os.path.exists(real_agy):
    mode = stat.S_IMODE(os.stat(real_agy).st_mode) or 0o600
    with open(real_agy, encoding="utf-8", errors="replace") as f:
        txt = f.read().strip()
    if txt:
        try:
            data = json.loads(txt)
        except ValueError as e:
            print(f"⚠️  Skipped {agy_path}: invalid JSON ({e})" if EN else f"⚠️  略過 {agy_path}：JSON 格式有誤（{e}）")
            data = None
        if isinstance(data, dict) and "agent-manager" in data:
            del data["agent-manager"]
            bak = f"{agy_path}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(real_agy, bak)
            os.chmod(bak, mode)
            tmp = f"{real_agy}.tmp{os.getpid()}"
            try:
                fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                os.chmod(tmp, mode)
                os.replace(tmp, real_agy)
            except BaseException:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
            print(f"Removed hooks from {agy_path} (backup kept)" if EN else f"已從 {agy_path} 移除 hooks（已備份）")
PY

# 4. 刪除已安裝的程式
for ENTRY in "$HOME/.local/bin/nirenne" "$HOME/.local/bin/agents"; do   # 正式名稱與簡稱
  if is_nirenne_entry "$ENTRY"; then
    rm -f "$ENTRY"
    say "已刪除 $ENTRY" "Deleted $ENTRY"
  elif [ -e "$ENTRY" ] || [ -L "$ENTRY" ]; then
    say "⚠️  無法確認 $ENTRY 為 nirenne 的入口，已保留。" \
        "⚠️  Could not identify $ENTRY as nirenne's launcher; it was kept."
  fi
done
# 組隊時代為建立的空檔與資料夾：程式刪除前先清掉（agents stop 沒經過解散時會留下）
[ -f "$CONF_DIR/agents.py" ] && python3 -I "$CONF_DIR/agents.py" collab-cleanup >/dev/null 2>&1 || true
rm -rf "$CONF_DIR"
say "已刪除 $CONF_DIR" "Deleted $CONF_DIR"

# 5. Session 紀錄是否一併刪除
if [ -d "$DATA_DIR" ]; then
  read -r -p "$(say "要一併刪除 Session 紀錄 $DATA_DIR 嗎？裡面也包含 sandbox/：組隊用的專用資料夾副本（COLLAB_PRIVATE_DIRS）、建置快取、組隊中的提示詞歷史。(y/N) " "Also delete the session records in $DATA_DIR? It also holds sandbox/: the party's private folder copies (COLLAB_PRIVATE_DIRS), build caches and prompt history from parties. (y/N) ")" a || a=""
  case "$a" in
    y|Y|ｙ|Ｙ)
      # 防呆：只刪看起來是本工具資料的資料夾（有 sessions 子資料夾），絕不刪家目錄或根目錄
      real_data="$(cd "$DATA_DIR" 2>/dev/null && pwd -P)"
      real_home="$(cd "$HOME" 2>/dev/null && pwd -P)"
      if [ -z "$real_data" ] || [ "$real_data" = "/" ] || [ "$real_data" = "$real_home" ] || [ ! -d "$DATA_DIR/sessions" ]; then
        say "⚠️  $DATA_DIR 看起來不是 nirenne 的資料資料夾，已保留。" "⚠️  $DATA_DIR does not look like nirenne's data folder; it was kept."
      else
        rm -rf "$DATA_DIR"; say "已刪除 $DATA_DIR" "Deleted $DATA_DIR"
      fi ;;
  esac
fi

say "移除完成。請開新的終端機分頁讓設定生效。" "Uninstall complete. Open a new terminal tab for the change to take effect."
