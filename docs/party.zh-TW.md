# 協作組：讓兩個 Agent 互相溝通

[English](party.md) | **繁體中文**　·　[← 回到 README](../README.zh-TW.md)

> 📌 目前只支援 Claude。隊伍的兩位成員都必須是 Claude Code，因為組隊要用到它的跨 Session 傳訊（SendMessage）和接回對話（`--continue`）。Codex、Gemini、Antigravity、Grok 暫時還不能組隊。

舉個例子：前端和 API 各有一個 Claude。把它們綁成一隊之後，你只要跟其中一個說需求，它就會自己傳訊息請另一個幫忙，做完再一起向你回報，最後由你驗收。

## 開始之前

- 在管理畫面開好兩個 Claude。
- WSL / Linux 要先安裝 bubblewrap，做法見 [Windows 安裝教學](install-windows.zh-TW.md#選用要使用協作組功能的話)。
- macOS 不用另外安裝。

## 建立協作組

1. 在左側清單點其中一個 Claude，例如 `app`
2. 點 [l 組隊]
3. 選擇夥伴，例如 `my-api`
4. 看完確認畫面的提醒後，按 `y`（或點 [y 確定組隊]）

組隊後兩個 Agent 會重新啟動，並接回原本的對話。清單上會顯示 `🔗A ↔ 3 my-api`，同一隊用同一個顏色。

新的組隊規則會取代之前的組隊。想讓 Agent 忘掉之前的對話和舊隊友？在它身上按右鍵，選「喝下忘卻藥水」，它就會用全新的對話重新出發。舊對話之後還是可以用 `/resume` 找回來。

## 下需求

直接在其中一個 Agent 輸入需求就好。你找誰下需求，誰就是隊長。

需求進行中，清單會在隊長旁邊顯示 `· 隊長`、另一個顯示 `· 隊員`；做完（✅）之後標籤就會拿掉。

完成時，隊長會交一份報告給你：兩邊各改了什麼、測試結果，以及你可以怎麼驗證。

## 查看往來訊息

點 [m 傳話] 就能看兩個 Agent 之間的對話。

紀錄也存在 `~/.agent-manager/logs/collab-A.log`。喝下忘卻藥水時，之前隊伍的傳話會搬到同一個資料夾的封存檔，檔名是 `collab-A.log.日期-時間`。

## 解除協作組

點其中一個 Agent，再點 [l 組隊]，然後按 `y`。兩個 Agent 會再重新啟動一次。

## 協作規則

組隊時，工具會自動告訴兩個 Agent 這些規則：

- 只能改自己的專案。不能讀取或使用對方專案的任何東西（包括帳號密碼），也不能寫程式繞過。
- 需要對方幫忙時，自己傳訊息給對方。往來訊息可以點 [m 傳話] 查看。
- 同一個需求最多來回 3 輪。遇到資料庫結構變更、刪除資料、部署或合併時，要停下來問你。

## 隔離方式

每個 Agent 外面都包了一層隔離。不管它用什麼工具或程式，都讀不到、也改不到夥伴的專案。

### WSL / Linux：寫入採白名單

[bubblewrap](https://github.com/containers/bubblewrap) 先把整個系統變成唯讀，再由 Linux 核心的 Landlock 限制 Agent 只能寫入這幾個地方：

- 自己的專案資料夾
- 自己專用的 `/tmp`
- Claude 自己的資料：這個 Agent 專用的一份設定，加上自己專案的對話紀錄
- 建置工具的專用快取（見下方）

讀取則是反過來，只擋特定的地方：夥伴的專案、夥伴的對話紀錄和提示詞歷史、`~/.agent-manager`、`~/.claude.json`，以及 Windows 磁碟（自己的專案除外）。想透過 `/proc` 或符號連結繞過去也一樣會被擋。

除了這些，其他地方還是讀得到，詳見下方的[無法隔離的部分](#無法隔離的部分)。

### macOS

使用系統內建的 Seatbelt（`sandbox-exec`）。讀寫夥伴的專案會出現 `Operation not permitted`。

另外這些也受到保護：

- 不能修改：本工具、各 Agent 的 hooks 設定、shell 啟動檔
- 不能讀寫：`~/.agent-manager`、真正的 `~/.claude`、夥伴的 Claude 暫存資料夾。組隊中的 Claude 會改用一份專用設定，這點和 Linux 一樣。
- 不能執行：`open`、`osascript`、`crontab`、`launchctl`

macOS 的做法是「預設允許、擋住特定位置」，保護範圍比 Linux 小，詳見下方的 [macOS 的限制](#macos-的限制)。

### tmux

組隊中的 Agent 只能查自己在哪個畫面，看不到、也控制不了夥伴的畫面。

## 組隊中寫不到的地方（WSL / Linux）

Agent 想寫入家目錄或其他工具的設定時，會出現 `Permission denied` 或 `Read-only file system`。這時 Agent 會用白話告訴你「組隊中無法寫入某某位置」。

這是故意的：避免它留下之後會在沙箱外被執行的東西，例如 `~/.bashrc` 或 `~/.gradle/init.d`。

### 建置工具的快取

Gradle、Maven、npm、yarn、pnpm、pip、NuGet、dotnet、Android 和 `~/.cache` 的快取，組隊時會自動改用這個 Agent 專用的資料夾，所以可以照常建置。你原本的 `~/.gradle`、`~/.m2`、`~/.npm` 不會被改到。

### 自己加入專用資料夾

如果其他工具也需要寫入，例如 Rust 的 `~/.cargo`，在 `~/.agent-manager/config` 加一行，再重新組隊就好。多個資料夾用 `:` 分隔：

```
COLLAB_PRIVATE_DIRS=~/.cargo:~/.rustup
```

第一次組隊時，工具會複製一份原本的資料夾給這個 Agent 專用。之後 Agent 只會寫它自己那份，你原本的資料夾不受影響。

這些路徑不能加入：家目錄本身和家目錄以外的位置、自己或夥伴的專案（包括它們的上層）、`~/.agent-manager`、`~/.config/agent-manager`、`~/.claude`、`~/.claude.json`、`~/.local/bin`、`/tmp`，以及符號連結。

### 專用資料夾放在哪裡

位置是 `~/.agent-manager/sandbox/<專案名稱>-<編號>/`，裡面有快取、專用的 `/tmp`、Claude 的專用設定，以及你自己加入的資料夾。

解散後會保留，下次組隊繼續用。想清掉的話，先解散隊伍，再刪除整個資料夾，例如：

```bash
rm -rf ~/.agent-manager/sandbox/my-api-1a2b3c4d
```

### 其他

- 組隊中的 Agent 不能執行 Windows 程式，例如 `dotnet.exe` 或 Visual Studio 建置。
- 組隊中的 Agent 看不到 `/mnt/c` 等 Windows 磁碟上的其他檔案。要給它看的檔案，請先放進專案資料夾。專案本身放在 C 槽也可以組隊。
- 如果 `~/.claude` 底下的 `settings.json`、`CLAUDE.md`、`skills` 等是符號連結（例如用 dotfiles 管理），組隊時會改成唯讀掛入連結的目標。目標不存在、擁有者不是你，或在專案、`/tmp`、`~/.agent-manager` 這類不能掛入的位置時，會略過不掛；被略過的項目會列在組隊成功的訊息裡。

## 注意事項

- ⚠️ 組隊和解散都會重新啟動兩個 Agent。正在進行的工作會中斷，它們啟動的背景程式（例如測試服務）也會關閉。請在兩個 Agent 都沒在工作時操作。
- 隔離是防止 Agent 自己去讀或改夥伴的專案。如果你自己把夥伴的程式碼複製到別處，再明確叫 Agent 去讀，它可能會照做，因為它會把你的明確要求當成你的決定。想讓 Agent 直接看夥伴的程式碼，建議先解散組隊，或另外召喚一個沒組隊的 Agent。
- WSL / Linux 需要 Linux 核心支援 Landlock。不支援時無法組隊，畫面會提示你更新 WSL（在 Windows 的 PowerShell 執行 `wsl --update`）。
- 沙箱外的 Session 不能主動傳訊息給組隊中的 Agent，但反過來可以。

### 組隊中的 Claude 用的是專用設定

組隊中的 Claude 使用這個 Agent 專用的一份設定，放在 `~/.agent-manager/sandbox/…/claude-config`。所以：

- 組隊中輸入的提示詞不會寫回 `~/.claude/history.jsonl`。第一次組隊時，只會帶入自己專案的紀錄。
- 組隊中改的 MCP 設定只會存在專用的 `.claude.json`，下次組隊時會被 `~/.claude.json` 的內容蓋掉。要調整 MCP，請先解散組隊。
- 組隊中用 `/config` 改的設定，不會存回 `~/.claude/settings.json`。

## 無法隔離的部分

- 讀取只擋夥伴的專案和上面列出的位置。第三個人的專案、`~/.ssh`、`~/.aws`、`~/.config/gh` 等，組隊中的 Agent 都讀得到。帳號密碼、金鑰這類機密，不要放在專案以外的共用位置。
- ssh-agent、`gh` 等登入憑證在同一個使用者帳號下是共用的，組隊中的 Agent 一樣能用。
- 為了讓組隊訊息正常運作，行程沒有隔離，所以 Agent 可以結束沙箱外的程式，例如夥伴的 Agent。這只會中斷工作，改不到任何檔案。
- 傳訊用的 Session 登記（`~/.claude/sessions`）和通訊端資料夾是共用、可寫的。組隊中的 Agent 可以改寫其他 Session 的登記，或攔截、冒充傳給它們的訊息，但改不到檔案。
- 登入憑證（`~/.claude/.credentials.json`）在沙箱裡是可寫的，因為 Claude 需要更新權杖。所以組隊中的 Agent 可以讀取或覆寫它。
- 如果夥伴的專案是 git worktree，主儲存庫的 `.git` 不在保護範圍內。

## macOS 的限制

- 組隊中不能執行 `open`、`osascript`，也不能送出 Apple Events 或透過 LaunchServices 開啟程式，所以 Claude 不會自動開瀏覽器。⚠️ 請在組隊前先完成登入（Claude 的 `/login`、`gh auth login` 等），或改成手動把網址複製到瀏覽器。
- 組隊中的 Claude 會沿用原本的登入（鑰匙圈），不需要重新登入。萬一還是要求 `/login`，瀏覽器不會自己開，請手動複製畫面上的網址。
- 組隊中的 Claude 已經在 `sandbox-exec` 裡，請不要再開 Claude Code 自己的 `/sandbox`。macOS 不允許沙箱裡再開沙箱，指令會失敗。
- 這些位置之後會在沙箱外被執行，所以組隊中寫不進去：`~/Library/LaunchAgents`、`~/.gradle/init.d`、`~/.gradle/init.gradle`、`~/.gradle/gradle.properties`、`~/.m2/settings.xml`、`~/.npmrc`、`~/.yarnrc`、`~/.yarnrc.yml`，以及 VS Code 的使用者設定和擴充套件。也不能執行 `crontab`、`launchctl`。
- macOS 沒有專用快取，所以 `~/.gradle`、`~/.m2` 的其他位置還是寫得進去，建置才能正常進行。
- 受保護位置的每一層上層資料夾，都不能改名、刪除或換成連結，但裡面還是可以正常建立檔案。
- 本工具用到的 Python 的標準函式庫、套件資料夾，以及 `~/Library/Python` 都寫不進去。Homebrew 安裝的其他程式（`/opt/homebrew`）則還是寫得進去。
- 組隊時，工具會先幫忙建立 `~/.gradle`、`~/.m2` 等工具需要、但還不存在的上層資料夾。全部隊伍解散後，如果它們還是空的，就會自動刪除。
- `open` 這類程式是用固定路徑擋的。實測把它複製到別處再執行，會被系統直接結束。
- 整體來說，macOS 採「預設允許」：上面沒列出的位置都還讀寫得到，保護範圍比 Linux 小。需要嚴格隔離的情境，請不要依賴它。
