# nirenne：shell 端（WSL / macOS / Linux）
# Source this file from ~/.bashrc or ~/.zshrc. Do not execute it directly.
# 相容 bash 與 zsh：避免使用 zsh 的保留字（例如 status），glob 不符合時不出現錯誤。

: "${AGENT_MANAGER_HOME:=$HOME/.agent-manager}"
# 組隊沙箱內 ~/.agent-manager 唯讀：狀態檔、紀錄一律交給沙箱外的代理程式代寫（NIRENNE_TMUX_PROXY）
_agent_manager_sandboxed() { [ -n "${NIRENNE_TMUX_PROXY:-}" ]; }
if ! _agent_manager_sandboxed; then
  mkdir -p -m 700 "$AGENT_MANAGER_HOME" "$AGENT_MANAGER_HOME/sessions" "$AGENT_MANAGER_HOME/logs"
  chmod 700 "$AGENT_MANAGER_HOME" "$AGENT_MANAGER_HOME/sessions" "$AGENT_MANAGER_HOME/logs" 2>/dev/null || true
fi

# 介面語言：~/.agent-manager/config 的 UI_LANG（在 agents 的冒險手冊按 g 切換）
# 組隊沙箱內讀不到設定檔（grep 回傳 2）：改用組隊時帶入的 NIRENNE_UI_LANG（沙箱外不會設定，行為不變）
_agent_manager_en() {
  grep -qs '^UI_LANG=en$' "$AGENT_MANAGER_HOME/config"
  case $? in 0) return 0 ;; 1) return 1 ;; esac
  [ "${NIRENNE_UI_LANG:-}" = en ]
}
# 依語言輸出一行：_agent_manager_say "中文" "English"
_agent_manager_say() { if _agent_manager_en; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }

_agent_manager_clean() {
  # 去掉控制字元（含 UTF-8 編碼的 C1 控制字元 U+0080～U+009F，例如 U+009B 可當成終端機控制序列的開頭）
  printf '%s' "${1:-}" | LC_ALL=C command tr '\r\n\t' '   ' | LC_ALL=C command tr -d '\000-\037\177' \
    | LC_ALL=C command sed $'s/\xc2[\x80-\x9f]//g'
}

_agent_manager_title() {
  # OSC 0: set terminal title
  printf '\033]0;%s\007' "$(_agent_manager_clean "$1")"
}

_agent_manager_has_cmd() {
  if [ -n "${ZSH_VERSION:-}" ]; then
    whence -p -- "$1" >/dev/null 2>&1
  else
    type -P -- "$1" >/dev/null 2>&1
  fi
}

_agent_manager_update_field() {
  # 更新 session 檔的一個欄位：交給 agents.py 的 update_kv（與 hooks 共用同一個鎖與原子寫入，
  # 不另外寫一套，避免兩邊同時改寫時互相蓋掉；macOS 沒有 flock 指令也一樣安全）
  _agent_manager_sandboxed || [ -f "$1" ] || return 0     # 組隊沙箱內看不到狀態檔，由代理程式確認
  command python3 -I "$HOME/.config/agent-manager/agents.py" set-kv "$1" "$2=$3" >/dev/null 2>&1 || true
}

agent-run() {
  local agent="${1:-}"
  [ "$#" -ge 1 ] && shift
  [ "${1:-}" = "command" ] && shift
  if [ -z "$agent" ] || [ "$#" -lt 1 ] || [ -z "${1:-}" ]; then
    echo "Usage: agent-run <Claude|Codex|Gemini|Antigravity|Grok> <command> [args...]" >&2
    return 2
  fi

  local cmd="$1"; shift

  # 已經在某個 Agent 裡面（例如 Agent 在工作中自己執行 claude --version）：直接執行原本的指令，
  # 不建立新的狀態檔、不改視窗設定與標題，否則管理畫面會以為這個視窗換了一個 Agent
  if [ -n "${NIRENNE_IN_AGENT:-}" ]; then
    # 層級加一：這個 Agent 的 hooks 會看到自己不是第 1 層而略過，不會改到上層 Agent 的狀態
    NIRENNE_AGENT_LEVEL=$(( ${NIRENNE_AGENT_LEVEL:-1} + 1 )) command "$cmd" "$@"
    return
  fi

  if ! _agent_manager_has_cmd "$cmd"; then
    _agent_manager_say "找不到 CLI：$cmd。請確認已安裝，或調整 Agent 指令對照。" \
      "CLI not found: $cmd. Make sure it is installed." >&2
    return 127
  fi

  local project branch cwd id start title session_file rc st
  cwd="$PWD"
  project="$(basename "$PWD")"
  branch="$(git -C "$PWD" branch --show-current 2>/dev/null || true)"
  [ -n "$branch" ] || branch="no-git"
  id="$(date +%Y%m%d-%H%M%S)-$$-$RANDOM"
  start="$(date '+%F %T')"
  session_file="$AGENT_MANAGER_HOME/sessions/$id.env"

  # Short unique suffix distinguishes two Claude tabs in the same project.
  title="[$project][$agent][$branch][${id##*-}]"
  local tty_dev
  tty_dev="$(tty 2>/dev/null || true)"; case "$tty_dev" in /dev/*) ;; *) tty_dev= ;; esac
  export AGENT_SESSION_ID="$id"
  export AGENT_SESSION_FILE="$session_file"
  export AGENT_PROJECT="$project"
  export AGENT_NAME="$agent"

  if _agent_manager_sandboxed; then
    command python3 -I "$HOME/.config/agent-manager/agents.py" sandbox-session "$id" "$agent" "$branch" "$tty_dev" \
      || _agent_manager_say "（組隊沙箱：無法建立狀態檔，管理畫面不會顯示這個 Agent 的狀態）" \
                            "(Party sandbox: could not create the status file; the manager will not show this agent's status)" >&2
  else
  (umask 077; cat > "$session_file" <<EOF
ID=$(_agent_manager_clean "$id")
PROJECT=$(_agent_manager_clean "$project")
AGENT=$(_agent_manager_clean "$agent")
BRANCH=$(_agent_manager_clean "$branch")
DIRECTORY=$(_agent_manager_clean "$cwd")
TASK=尚未辨識
STATUS=RUNNING
START=$(_agent_manager_clean "$start")
END=
PID=$$
TTY=$(_agent_manager_clean "$tty_dev")
PANE=${TMUX_PANE:-}
ACTIVITY=
TASK_SOURCE=
EOF
  )
  fi

  # 在 agents 管理畫面（tmux）內啟動時，把 Session 綁到目前視窗，供左側清單讀取。
  # 只在「管理畫面的 tmux」裡才綁定：TMUX 的通訊端名稱必須是管理畫面的（避免在別的 tmux 裡執行時，
  # 因繼承了 AGENT_MANAGER_TMUX 而改到管理畫面上同編號的窗格）
  local tmux_sock="${TMUX%%,*}"
  if [ "${AGENT_MANAGER_TMUX:-}" = "1" ] && [ -n "${TMUX_PANE:-}" ] && [ "${tmux_sock##*/}" = "${AGENTS_TMUX_SOCKET:-agents}" ]; then
    tmux -L "${AGENTS_TMUX_SOCKET:-agents}" set-option -w -t "$TMUX_PANE" @agent_session "$id" 2>/dev/null || true
    tmux -L "${AGENTS_TMUX_SOCKET:-agents}" set-option -w -t "$TMUX_PANE" @agent_name "$agent" 2>/dev/null || true
  fi

  _agent_manager_sandboxed || (umask 077; printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(_agent_manager_clean "$start")" "$(_agent_manager_clean "$id")" \
    "$(_agent_manager_clean "$project")" "$(_agent_manager_clean "$agent")" \
    "$(_agent_manager_clean "$branch")" "RUNNING" \
    >> "$AGENT_MANAGER_HOME/logs/history.tsv")

  _agent_manager_title "${title}[RUNNING]"
  echo "----------------------------------------"
  echo " Agent Manager"
  _agent_manager_say " 專案：$(_agent_manager_clean "$project")" " Project: $(_agent_manager_clean "$project")"
  _agent_manager_say " Agent：$agent" " Agent: $agent"
  _agent_manager_say " Branch：$(_agent_manager_clean "$branch")" " Branch: $(_agent_manager_clean "$branch")"
  _agent_manager_say " Session：$id" " Session: $id"
  echo "----------------------------------------"

  # Claude 預設會把 Tab 標題改成對話主題並蓋掉專案名稱；
  # 改由 hooks（agents.py claude-hook）組合「[專案][Agent] 主題」寫入標題。
  # Antigravity 預設為 inline 模式（不接管滑鼠滾輪，在 tmux 中捲動會進入選取模式）；
  # 在管理畫面中改以 altScreenMode=always 啟動，讓滾輪與 Claude 一樣直接捲動對話內容。
  rc=0
  if [ "$agent" = "Claude" ]; then
    NIRENNE_IN_AGENT=1 NIRENNE_AGENT_LEVEL=1 CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1 command "$cmd" "$@" || rc=$?
  elif [ "$agent" = "Antigravity" ] && [ "${AGENT_MANAGER_TMUX:-}" = "1" ]; then
    NIRENNE_IN_AGENT=1 NIRENNE_AGENT_LEVEL=1 command "$cmd" --settings '{"altScreenMode":"always"}' "$@" || rc=$?
  else
    NIRENNE_IN_AGENT=1 NIRENNE_AGENT_LEVEL=1 command "$cmd" "$@" || rc=$?
  fi

  if [ "$rc" -eq 0 ]; then st="EXITED"; else st="ERROR"; fi
  _agent_manager_update_field "$session_file" STATUS "$st"
  _agent_manager_update_field "$session_file" END "$(date '+%F %T')"
  _agent_manager_title "${title}[$st]"
  echo
  _agent_manager_say "Agent 程式已結束：$st (exit=$rc)" "Agent exited: $st (exit=$rc)"
  _agent_manager_say "Session：$id" "Session: $id"
  return "$rc"
}

# These wrappers preserve the familiar commands. `command` bypasses the function
# and resolves the actual executable, preventing recursion.
# 用 function 關鍵字定義：使用者已有同名 alias（例如 Claude 本機安裝會加 alias claude=…）時，
# name() { … } 的寫法會被 alias 展開而整份設定檔語法錯誤；這種寫法不會（此時 alias 優先，不追蹤狀態）
function claude      { agent-run Claude command claude "$@"; }
function gemini      { agent-run Gemini command gemini "$@"; }
# Antigravity CLI 的實際指令是 agy；antigravity 保留為別名。
function agy         { agent-run Antigravity command agy "$@"; }
function antigravity { agy "$@"; }
function codex       { agent-run Codex command codex "$@"; }
function grok        { agent-run Grok command grok "$@"; }

agent-topic() {
  local topic
  topic="$(_agent_manager_clean "${*:-}")"
  [ -n "${topic// /}" ] || { _agent_manager_say "Usage: agent-topic <目前任務主題>" "Usage: agent-topic <task topic>"; return 2; }
  [ -n "${AGENT_SESSION_FILE:-}" ] && { _agent_manager_sandboxed || [ -f "$AGENT_SESSION_FILE" ]; } || {
    _agent_manager_say "目前 Shell 沒有由 Agent Manager 啟動的 Session。" \
      "This shell has no session started by Agent Manager."; return 1;
  }
  _agent_manager_update_field "$AGENT_SESSION_FILE" TASK "$topic"
  # 手動設定的主題優先，hooks 不會再自動覆蓋
  _agent_manager_update_field "$AGENT_SESSION_FILE" TASK_SOURCE manual
  local project="${AGENT_PROJECT:-project}" agent="${AGENT_NAME:-Agent}"
  _agent_manager_title "[$project][$agent] $topic"
  _agent_manager_say "工作主題已更新：$topic" "Task topic updated: $topic"
}

agent-status() {
  local id="${1:-}" st="${2:-}" note="${3:-}"
  # Convenience: in current session, first arg can be the status.
  case "$id" in
    ANALYZING|CODING|TESTING|WAITING|RUNNING|DONE|ERROR|EXITED)
      note="$st"
      st="$id"
      id="${AGENT_SESSION_ID:-}"
      ;;
  esac
  case "$id" in ''|*/*|.*) id="" ;; esac
  [ -n "$id" ] && [ -n "$st" ] || {
    echo "Usage: agent-status <session-id> <ANALYZING|CODING|TESTING|WAITING|RUNNING|DONE|ERROR> [note]"
    _agent_manager_say "也可在目前 Agent Tab 執行：agent-status CODING '修改登入功能'" \
      "In the current agent tab you can also run: agent-status CODING 'Fix login'"
    return 2
  }
  local file="$AGENT_MANAGER_HOME/sessions/$id.env"
  _agent_manager_sandboxed || [ -f "$file" ] || { _agent_manager_say "找不到 Session：$id" "Session not found: $id"; return 1; }
  case "$st" in ANALYZING|CODING|TESTING|WAITING|RUNNING|DONE|ERROR|EXITED) ;; *)
    _agent_manager_say "不支援的狀態：$st" "Unsupported status: $st"; return 2;; esac
  _agent_manager_update_field "$file" STATUS "$st"
  case "$st" in DONE|ERROR|EXITED)
    _agent_manager_update_field "$file" END "$(date '+%F %T')" ;;
  esac
  if _agent_manager_sandboxed; then
    command python3 -I "$HOME/.config/agent-manager/agents.py" sandbox-history "$id" "$st" "$note" >/dev/null 2>&1 || true
  else
    (umask 077; printf '%s\t%s\t%s\t%s\n' "$(date '+%F %T')" "$(_agent_manager_clean "$id")" "$st" "$(_agent_manager_clean "$note")" \
      >> "$AGENT_MANAGER_HOME/logs/history.tsv")
  fi
  echo "Session $id → $st"
}

_agent_manager_field() {
  command awk -v k="$1" 'index($0, k "=") == 1 { print substr($0, length(k) + 2); exit }' "$2" 2>/dev/null
}

# 判斷 session 的 shell 是否還活著；Tab 被直接關掉時狀態不會更新，靠 PID 判斷。
_agent_manager_alive() {
  local file="$1" pid
  pid="$(_agent_manager_field PID "$file")"
  # 舊版 .txt 沒有 PID 欄位，ID 尾碼就是 shell PID
  if [ -z "$pid" ]; then
    pid="$(_agent_manager_field ID "$file")"
    pid="${pid##*-}"
  fi
  case "$pid" in ''|*[!0-9]*|0) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null
}

# 回傳實際狀態：已結束的照舊；標示執行中但程式已不在的回傳 STALE
_agent_manager_effective_status() {
  local file="$1" st
  st="$(_agent_manager_field STATUS "$file")"
  case "$st" in
    DONE|EXITED|ERROR) printf '%s' "$st" ;;
    *) if _agent_manager_alive "$file"; then printf '%s' "$st"; else printf 'STALE'; fi ;;
  esac
}

agent-list() {
  # agent-list      只列出執行中的 Session
  # agent-list -a   列出全部（含已結束、STALE）
  if [ -n "${ZSH_VERSION:-}" ]; then setopt local_options null_glob no_nomatch; fi
  local _ng=0 _fg=0
  if [ -n "${BASH_VERSION:-}" ]; then
    shopt -q nullglob || { _ng=1; shopt -s nullglob; }
    shopt -q failglob && { _fg=1; shopt -u failglob; }
  fi
  local all=0 file shown=0
  local id project agent st branch task
  if [ "${1:-}" = "-a" ] || [ "${1:-}" = "--all" ]; then all=1; fi
  printf '%-30s %-16s %-13s %-14s %-12s %s\n' "SESSION" "PROJECT" "AGENT" "STATUS" "BRANCH" "TASK"
  printf '%s\n' "--------------------------------------------------------------------------------------------------------"
  for file in "$AGENT_MANAGER_HOME"/sessions/*.env "$AGENT_MANAGER_HOME"/sessions/*.txt; do
    [ -f "$file" ] || continue
    st="$(_agent_manager_effective_status "$file")"
    if [ "$st" = "RUNNING" ]; then
      case "$(_agent_manager_field ACTIVITY "$file")" in
        WAITING) st="WAITING" ;; WORKING) st="WORKING" ;; APPROVAL) st="APPROVAL" ;;
      esac
    fi
    if [ "$all" -eq 0 ]; then
      case "$st" in DONE|EXITED|ERROR|STALE) continue ;; esac
    fi
    id="$(_agent_manager_field ID "$file")"
    project="$(_agent_manager_field PROJECT "$file")"
    agent="$(_agent_manager_field AGENT "$file")"
    branch="$(_agent_manager_field BRANCH "$file")"
    task="$(_agent_manager_field TASK "$file")"
    printf '%-30s %-16s %-13s %-14s %-12s %s\n' \
      "$(_agent_manager_clean "${id:0:30}")" "$(_agent_manager_clean "${project:0:16}")" \
      "$(_agent_manager_clean "${agent:0:13}")" "${st:0:14}" "$(_agent_manager_clean "${branch:0:12}")" \
      "$(_agent_manager_clean "$task")"
    shown=$((shown+1))
  done
  if [ "$_ng" -eq 1 ]; then shopt -u nullglob; fi
  if [ "$_fg" -eq 1 ]; then shopt -s failglob; fi
  [ "$all" -eq 1 ] || [ "$shown" -gt 0 ] || _agent_manager_say "（目前沒有執行中的 Session；agent-list -a 可查看全部）" \
    "(No running sessions; agent-list -a shows all)"
}

agent-clean() {
  # 刪除已結束（DONE/EXITED/ERROR）與 STALE 的 Session 紀錄；history 紀錄保留
  if [ -n "${ZSH_VERSION:-}" ]; then setopt local_options null_glob no_nomatch; fi
  local _ng=0 _fg=0
  if [ -n "${BASH_VERSION:-}" ]; then
    shopt -q nullglob || { _ng=1; shopt -s nullglob; }
    shopt -q failglob && { _fg=1; shopt -u failglob; }
  fi
  local file st n=0
  for file in "$AGENT_MANAGER_HOME"/sessions/*.env "$AGENT_MANAGER_HOME"/sessions/*.txt; do
    [ -f "$file" ] || continue
    st="$(_agent_manager_effective_status "$file")"
    case "$st" in DONE|EXITED|ERROR|STALE) rm -f "$file" "$file.lock"; n=$((n+1)) ;; esac
  done
  if [ "$_ng" -eq 1 ]; then shopt -u nullglob; fi
  if [ "$_fg" -eq 1 ]; then shopt -s failglob; fi
  _agent_manager_say "已清除 $n 筆已結束的 Session（logs/ 歷史紀錄保留）" "Removed $n finished sessions (logs/ history kept)"
}

agent-open() {
  # Open a NEW Windows Terminal tab in the current WSL directory.
  # Usage: agent-open <claude|codex|gemini|agy|grok>
  local agent="${1:-}"
  [ -n "$agent" ] || { echo "Usage: agent-open <claude|codex|gemini|agy|grok>"; return 2; }
  local distro
  distro="${WSL_DISTRO_NAME:-Ubuntu}"
  local project branch title
  project="$(basename "$PWD")"
  branch="$(git branch --show-current 2>/dev/null || true)"
  [ -n "$branch" ] || branch="no-git"
  case "$agent" in
    claude) title="[$project][Claude][$branch]" ;;
    gemini) title="[$project][Gemini][$branch]" ;;
    codex) title="[$project][Codex][$branch]" ;;
    grok) title="[$project][Grok][$branch]" ;;
    agy|antigravity) agent=agy; title="[$project][Antigravity][$branch]" ;;
    *) _agent_manager_say "不支援的 Agent：$agent" "Unsupported agent: $agent"; return 2 ;;
  esac

  if [ "$(uname -s)" = "Darwin" ]; then
    _agent_manager_say "agent-open 僅支援 Windows Terminal（WSL）。macOS 請改用 nirenne 管理畫面。" \
      "agent-open only works with Windows Terminal (WSL). On macOS use nirenne instead."
    return 1
  fi
  if ! command -v wt.exe >/dev/null 2>&1; then
    _agent_manager_say "找不到 wt.exe。請確認 Windows Terminal 已安裝，且 WSL 可呼叫 Windows 執行檔。" \
      "wt.exe not found. Make sure Windows Terminal is installed and WSL can run Windows programs."
    return 1
  fi

  # wsl.exe starts a fresh login shell in this distro and directory.
  # wt.exe 把 ; 視為子命令分隔符號，需先處理避免被拆成多個指令
  local sh_bin="bash"
  case "${SHELL:-}" in */zsh) sh_bin="zsh" ;; esac
  local wt_title wt_pwd="${PWD//;/\\;}"
  wt_title="$(_agent_manager_clean "${title//;/ }")"
  wt.exe -w 0 new-tab --title "$wt_title" wsl.exe -d "$distro" --cd "$wt_pwd" --exec "$sh_bin" -lic "$agent"
}

agent-help() {
  # agent-open 只在 WSL 有用（開 Windows Terminal 分頁）：其他系統不列出
  local wsl=""
  case "$(uname -r 2>/dev/null)" in *[Mm]icrosoft*) wsl=1 ;; esac
  if _agent_manager_en; then
    cat <<'EOF'
nirenne (multi-agent manager)
  claude [args...]       Start Claude in this tab, tracked by the manager
  gemini [args...]       Start Gemini in this tab, tracked by the manager
  agy [args...]          Start Antigravity in this tab (same as antigravity)
  codex [args...]        Start Codex in this tab, tracked by the manager
  grok [args...]         Start Grok in this tab, tracked by the manager
  nirenne                Open the multi-agent manager (sidebar, click to switch; agents also works)
  nirenne stop           Stop the manager and every agent in it
  nirenne --help         Show the manager's usage (nirenne --version shows the version)
EOF
    [ -n "$wsl" ] && echo "  agent-open <agent>     Open a new Windows Terminal tab in this project"
    cat <<'EOF'
  agent-topic <topic>    Set the task topic and tab title of this session
  agent-status <status>  Set the status of this session
  agent-list [-a]        List running sessions (-a includes finished)
  agent-clean            Remove finished / stale session records
  agent-help             Show this help

Status: ANALYZING / CODING / TESTING / WAITING / RUNNING / DONE / ERROR
Tip: you can run several of the same agent in one project; the session ID suffix tells them apart.
EOF
    return
  fi
  cat <<'EOF'
nirenne（多 Agent 管理工具）
  claude [args...]       在目前 Tab 啟動並自動管理 Claude
  gemini [args...]       在目前 Tab 啟動並自動管理 Gemini
  agy [args...]          在目前 Tab 啟動並自動管理 Antigravity（antigravity 同義）
  codex [args...]        在目前 Tab 啟動並自動管理 Codex
  grok [args...]         在目前 Tab 啟動並自動管理 Grok
  nirenne                開啟多 Agent 管理畫面（左側清單、滑鼠切換；也可以輸入 agents）
  nirenne stop           結束管理畫面與其中所有 Agent
  nirenne --help         顯示管理畫面的用法（nirenne --version 顯示版本）
EOF
  [ -n "$wsl" ] && echo "  agent-open <agent>     在目前專案目錄開新 Windows Terminal Tab"
  cat <<'EOF'
  agent-topic <主題>     更新目前 Session 的任務主題與 Tab 標題
  agent-status <狀態>    更新目前 Session 狀態
  agent-list [-a]        列出執行中的 Session（-a 含已結束）
  agent-clean            清除已結束／已失效的 Session 紀錄
  agent-help             顯示說明

狀態：ANALYZING / CODING / TESTING / WAITING / RUNNING / DONE / ERROR
提示：同專案可同時開多個相同 Agent；Session ID 尾碼用來區分。
EOF
}
