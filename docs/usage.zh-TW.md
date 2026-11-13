# 使用說明

[English](usage.md) | **繁體中文**　·　[← 回到 README](../README.zh-TW.md)

## 功能細節

### 管理畫面

輸入 `nirenne` 就會打開管理畫面：左邊是 Agent 清單，右邊是目前選中的 Agent。幾乎所有操作都能用滑鼠完成。

在清單上的 Agent 按右鍵（或點名稱右邊的 ⋮），可以前往、設定標籤、組隊、查看隊伍傳話、喝下忘卻藥水、離隊。不用先切換過去。

Agent 很多、或終端機視窗太矮時，清單會自動改成精簡顯示。還是放不下的話，可以用滾輪或點 ▲／▼ 捲動；被藏起來的隊員在等你時，會用黃色提醒。

### 自動判斷 Agent 是不是在等你

- Claude、Codex、Antigravity、Grok、Gemini 都透過官方 hooks 回報：回答完、或需要你核准時會通知管理畫面，判斷很準。Antigravity 的「等你核准」是從畫面上的確認選單判斷的。
- Gemini CLI 如果版本太舊、還不支援 hooks，就改成「畫面 8 秒沒變化就當作在等你」。這是推測，偶爾會不準。只要收到過一次回報，就會自動改回用回報判斷。

### 狀態、時間與主題

- 每個 Agent 會顯示目前的狀態，例如 `✅ 我好了，你人呢？`、`✋ 等待你的指示`、`⚔ 戰鬥中`、`⏳ 等 xxx 回報`。所有狀態的意思見下方的[狀態說明](#狀態說明)。
- 會顯示這次工作花了多久，例如 `✅ 我好了，你人呢？ (3分12秒)`。工作中則每秒更新。
- 任務主題會自動抓 Claude 產生的對話標題。你也可以自己設定標籤；標籤只是顯示用，不會傳給 Agent。
- 底部狀態列隨時顯示目前 Agent 的版本與模型（例如 `Claude Code v2.1.322 · Opus 5.5`）、完整路徑和 Git 分支。

### 背景執行與通知

- 關掉終端機，Agent 也不會中斷，再輸入 `nirenne` 就能接回。
- ⚠️ 電腦關機或重新開機後，管理畫面和所有 Agent 都會結束，不會保留。
- Agent 做完（✅）或需要你核准（✋）時，會跳出 Windows、macOS 或 Linux 的系統通知。你正在看的那個 Agent 不會通知。關掉終端機、Agent 在背景跑時也一樣會通知。
- 主任務把工作分給背景子任務（分隊）時，每支分隊回來都會通知「☑ 分隊凱旋」，並註明主任務還沒完成；全部做完才會通知「我好了」。

### 其他

- 協作組：把兩個 Claude（例如前端和 API）綁成一隊，互相傳訊息完成你的需求。各自只能改自己的專案，也看不到對方的資料夾。目前只支援 Claude，詳見[協作組](party.zh-TW.md)。
- 防誤關：關閉 Agent 一定會先確認。所有彈出視窗都可以按 Esc 關掉，用不到的快速鍵和選單也已經停用。
- 介面有繁體中文和英文。第一次使用時會依系統語系自動選擇，之後在冒險手冊（[? 手冊]）按 g 就能切換，所有畫面會立刻更新。安裝時也可以用 `./install.sh --lang en`（或 `--lang zh-TW`）指定。
- 原本的用法不受影響：`cd 專案 && claude` 照常可用。

## 開啟與離開

```bash
nirenne          # 開啟管理畫面，或接回原本的畫面
nirenne stop     # 結束管理畫面與其中所有 Agent（會先確認）
```

- 點右上角的 [q 休息] 會回到一般終端機，Agent 繼續在背景執行。再輸入 `nirenne` 就能接回。
- 直接關掉 Windows Terminal 也一樣，Agent 不會中斷。
- ⚠️ 電腦關機或重新開機後，管理畫面和所有 Agent 都會結束。開機後重新輸入 `nirenne`、再召喚 Agent 就好；Claude 可以用 `/resume` 接回之前的對話。

## 左側清單

| 操作 | 按鍵 | 說明 |
|---|---|---|
| 點一下 Agent | ↑↓ + Enter，或數字鍵 | 切換到該 Agent |
| 在 Agent 上按右鍵 | | 開啟該 Agent 的指令選單（見表格下方） |
| 點 Agent 名稱右邊的 ⋮ | | 開啟同一份選單 |
| `[+ 召喚]` | `n` | 選擇 Agent 類型和專案資料夾，開一個新的 Agent |
| `[t 標籤]` | `t` | 自己設定標籤，方便分辨每個 Agent 在做什麼 |
| `[x 離隊]` | `x` | 關閉游標所在的 Agent，會再確認一次 |
| `[l 組隊]` | `l` | 把兩個 Claude 綁成協作組，或解除，見[協作組](party.zh-TW.md) |
| `[m 傳話]` | `m` | 查看協作組的往來訊息 |
| `[? 手冊]` | `?` | 打開冒險手冊；在手冊裡按 g 切換語言 |
| `[q 休息]`（右上角） | `q` | 離開畫面，Agent 繼續在背景執行 |
| 滾輪，或點 `▲` `▼` | | Agent 太多放不下時，捲動清單 |

幾點補充：

- 右鍵選單有：前往、設定標籤、組隊、隊伍傳話、喝下忘卻藥水、離隊。不用先切換過去，例如你在 Agent 1，也可以直接在 Agent 6 上按右鍵把它關掉。
- 喝下忘卻藥水只有組隊中才能用：Agent 會用全新的對話重新出發，忘掉舊對話和舊隊友。之前隊伍的傳話會收進封存卷軸，目前這一隊的會保留。
- 如果你的終端機把右鍵攔下來、跳出它自己的選單，就改點 ⋮。
- 標籤只是顯示用，不會傳給 Agent。清空後按 Enter，就會改回自動抓取主題。
- 傳話和手冊會暫時蓋滿整個畫面，按 Esc 或 q 關閉。
- 按鍵只在游標停在左側清單時有效，請先用滑鼠點一下清單。在右邊的 Agent 畫面按 `x`、`q`，只是一般的打字。
- 按鍵不分大小寫，也不分全形半形，所以開著中文輸入法也能用。
- 所有彈出視窗都可以按 Esc 關閉。

## 狀態說明

| 狀態 | 意思 |
|---|---|
| `✅ 我好了，你人呢？ (3分12秒)` | 做完了，在等你；括號是這次花的時間 |
| `✋ 等待你的指示` | Agent 要你核准某個操作，或在問你問題 |
| `⚔ 戰鬥中 (25秒)` | 還在處理，括號是目前已花的時間 |
| `✨ 召喚中` | Agent 剛召喚出來，正在啟動 |
| `💤 待命中` | 已啟動，還沒交代工作，等你輸入 |
| `⏳ 等 app 回報` | 組隊中：在等隊友回報（不是在等你） |
| `🏹 分隊出征中 ×2` | 主任務派出背景子任務（分隊），正在等它們回來（不是在等你） |

## 其他操作

- 滾輪往上：查看 Agent 之前的輸出。Claude Code、Codex、Antigravity、Grok 會自己處理捲動。首頁和 Gemini 往上捲時，右下角會顯示捲了多少行；點一下畫面、按 `q` 或捲回最底下，就會回到底部。
- 用滑鼠拖曳選取文字，放開就會複製到剪貼簿。
- 想用終端機原本的選取方式：Windows Terminal 按住 Shift 拖曳，iTerm2 按住 Option 拖曳。
- 貼上：按 Shift + 右鍵，或 Ctrl+V（Windows）／Cmd+V（macOS）。在管理畫面裡單按右鍵不會貼上，要按住 Shift。
- Agent 結束時（例如不小心按了 Ctrl+C），視窗不會直接關掉，而是問你要按 `y` 讓它離隊，還是按 `r` 重新啟動。重新啟動的話，Claude 會接回剛才的對話。
- 想自訂召喚時列出的專案資料夾，在 `~/.bashrc` 加入 `export AGENTS_PROJECT_DIRS="~/work:~/oss"`，多個資料夾用 `:` 分隔。

## 不用管理畫面也可以

在一般的終端機分頁照常使用，工具一樣會自動記錄專案、Agent 和 Git 分支：

```bash
cd ~/project/my-api
claude          # 或 codex、gemini、agy（antigravity 也可）、grok
```

其他指令：

```bash
agent-list                          # 列出執行中的 Session（-a 列出全部）
agent-topic "修正登入逾時"            # 手動設定目前 Session 的主題
agent-status CODING "修改驗證流程"    # 手動更新狀態
agent-clean                         # 清除已結束的 Session 紀錄
agent-open claude                   # 在目前資料夾開新的 Windows Terminal 分頁（僅 Windows）
agent-help                          # 顯示所有指令
```

## 接手在其他分頁執行中的對話

已經在一般分頁執行的 Agent，沒辦法直接搬進管理畫面。不過 Claude 的對話會存檔，可以這樣接回來：

1. 在原本的分頁離開 Claude（輸入 `/exit`）
2. 在管理畫面用 [+ 召喚] 開同一個專案的 Claude
3. 輸入 `/resume`，選擇那段對話

⚠️ 同一段對話不要同時在兩個地方開著。

## 自訂

| 檔案 | 用途 |
|---|---|
| `agents.py` | 管理畫面：左側清單、新增選單、協作組、Claude hooks |
| `agent-manager.sh` | shell 指令：包裝 `claude` 等指令、`agent-list` 等 |
| `tmux.conf` | 管理畫面的 tmux 設定：狀態列、滑鼠、快速鍵 |
| `agents` | 啟動指令，安裝成 `nirenne` 和 `agents` 兩個名稱 |

常見的調整都在 `agents.py` 開頭：

- `SIDEBAR_W`：清單寬度
- `IDLE_SECS`：畫面幾秒沒變化就當作在等你
- `AGENT_TYPES`：支援哪些 Agent 和對應的指令。沒安裝的 Agent 在新增選單裡會顯示成灰色。

改完重新執行 `./install.sh` 就好。

想關閉系統通知，在 `~/.bashrc`（zsh 是 `~/.zshrc`）加入 `export AGENTS_NOTIFY=0`，再執行 `nirenne stop`，然後重新開啟 `nirenne`。

## 更新與移除

用 `nirenne --version` 或 `nirenne -v` 可以查看已安裝的版本。各版本改了什麼、更新時要注意什麼，請看[更新紀錄](../CHANGELOG.zh-TW.md)。

### 更新到新版

```bash
cd ~/nirenne
git pull
./install.sh
```

執行中的管理畫面會在幾秒內自動換成新版（左側清單和組隊的代理程式），Agent 不會中斷。

只有 tmux 設定（快速鍵、狀態列、右鍵選單）的變更，要重新開啟才會套用：先輸入 `nirenne stop`，再輸入 `nirenne`。⚠️ `nirenne stop` 會結束所有 Agent，請先確認沒有工作正在進行。需要這樣做的版本，會在更新紀錄的「更新提醒」裡註明。

### 安裝會修改哪些檔案

| 檔案 | 內容 |
|---|---|
| `~/.bashrc` 或 `~/.zshrc` | 加入一段載入設定，前後以 `# >>> nirenne >>>` 標記 |
| `~/.claude/settings.json` | 加入 hooks，修改前會自動備份成 `settings.json.bak-日期`。hooks 只對本工具啟動的 Claude 生效，就算出錯也不會影響 Claude |
| `~/.codex/hooks.json` | 有安裝 Codex 時加入 hooks（先備份）。第一次啟動 Codex 時，可能要你同意信任這些 hooks |
| `~/.gemini/settings.json` | 有安裝 Gemini CLI 時加入 hooks（先備份） |
| `~/.gemini/config/hooks.json` | 有安裝 Antigravity（`agy`）時加入 hooks（先備份） |
| `~/.config/agent-manager/` | 程式和 tmux 設定 |
| `~/.local/bin/nirenne`、`~/.local/bin/agents` | 啟動指令，兩個名稱是同一個程式。如果名稱已經被其他程式用掉，安裝時會跳過、不會覆蓋 |
| `~/.agent-manager/` | Session 紀錄和協作組的訊息紀錄，只存在你的電腦上。裡面的 `sandbox/` 是組隊時各 Agent 的專用資料夾，放快取等東西 |

管理畫面使用獨立的 tmux socket（`agents`）和獨立的設定檔，不會影響你原本的 tmux 設定。

### 移除

```bash
cd ~/nirenne
./uninstall.sh
```

移除時會：

- 拿掉 shell 設定裡的載入區塊
- 拿掉 `~/.claude/settings.json`、`~/.codex/hooks.json`、`~/.gemini/settings.json`、`~/.gemini/config/hooks.json` 裡本工具的 hooks，都會先備份
- 刪除已安裝的程式
- 詢問你要不要刪除 Session 紀錄
