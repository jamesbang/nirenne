# 常見問題

[English](faq.md) | **繁體中文**　·　[← 回到 README](../README.zh-TW.md)

## 輸入 `nirenne` 出現 `command not found`

關掉終端機分頁、再開一個新的就好。或者執行安裝完成時畫面上提示的 `source` 指令。

本工具支援 bash 和 zsh（Ubuntu 預設是 bash，macOS 預設是 zsh）。fish 等其他 shell 目前還不支援。

## 出現「你已經在管理畫面裡了」

代表你已經在管理畫面裡面，不需要再開一次。

## [+ 召喚] 裡的 Agent 是灰色的（尚未加入公會）

代表找不到這個 Agent 的指令，可能還沒安裝。選它會顯示安裝方式。

裝好後，先在一般分頁輸入版本指令確認（例如 `claude --version`），再回來召喚。

## [+ 召喚] 裡找不到我的專案資料夾

選清單最下面的「其他路徑…（手動輸入）」，自己輸入路徑。

也可以設定 `AGENTS_PROJECT_DIRS`，讓清單多列出你常用的資料夾，做法見[其他操作](usage.zh-TW.md#其他操作)。

## 按右鍵不能貼上

管理畫面支援滑鼠操作，單按右鍵會被管理畫面接收，用來開選單。

要貼上的話，請按 Shift + 右鍵（Windows Terminal 原本的貼上方式），或 Ctrl+V。

## 按鍵（n、x、t…）沒反應

先用滑鼠點一下左側清單，讓游標停在清單上，再按按鍵。

## 狀態一直不更新

只有從管理畫面啟動、或用本工具包裝過的指令（例如 `claude`）啟動的 Agent，才會回報狀態。

如果還是不對：

1. 重新執行一次 `./install.sh`。
2. 仍然不對的話，看 `~/.agent-manager/logs/hooks.log` 的最後幾行。有事件紀錄，代表 hooks 有在執行；出現 `skip=` 或 `error=` 時，後面會寫略過的原因或出錯的位置。回報問題時請附上這幾行。

## 中文變成亂碼

輸入 `echo $LANG`，結果應該要有 `UTF-8`。如果沒有，執行：

```bash
echo 'export LANG=C.UTF-8' >> ~/.bashrc && source ~/.bashrc
```

## 改變視窗大小時，彈出視窗閃一下或被關閉

有些系統在改變視窗大小時，會把彈出視窗關掉。各種視窗的情況如下：

- 冒險手冊和隊伍傳話：會直接跟著調整大小。
- 招募說明：會用新的大小自動重新開啟，並停在原本捲到的位置。
- 召喚、設定標籤、組隊這類要輸入的視窗：會被關掉，重新開啟就好。
- 右鍵選單：會被關掉，再按一次右鍵就好。

## [l 組隊] 顯示「找不到 bwrap」

執行 `sudo apt install -y bubblewrap`。只有 WSL / Linux 需要。

## [l 組隊] 顯示「Linux 核心不支援 Landlock」

在 Windows 的 PowerShell 執行 `wsl --update`，重新開啟 WSL 後再試一次。

## [l 組隊] 顯示「目前只支援 Claude」

協作組只能把兩個 Claude 綁在一起。Codex、Gemini、Antigravity、Grok 目前還不能組隊。

## 我想完全結束所有 Agent

在一般的終端機（不是管理畫面裡面）輸入 `nirenne stop`，再按 `y` 確認。

## iTerm2 按右鍵跳出 iTerm2 自己的選單

1. 打開 Settings → Profiles → Terminal，勾選 Enable mouse reporting 和 Report mouse clicks & drags。
2. 如果你是用 Control + 點按當右鍵，還要到 Settings → Pointer，勾選 Ctrl-click reported to apps, does not open menu。
3. 還是不行的話，直接點 Agent 名稱右邊的 ⋮，一樣能打開選單。

## 沒有收到通知

### Windows

通知是以「Windows PowerShell」的名義送出的。請到「設定 → 系統 → 通知」確認通知有開啟，而且沒有開「勿打擾」。

### macOS

通知是以「指令碼編寫程式（Script Editor）」的名義送出的。第一次請到「系統設定 → 通知」允許它。

開著專注模式（勿擾、個人、睡眠等）時，通知會被擋下來。請到「系統設定 → 專注模式 → 該模式 → 允許的通知 → App」，把「指令碼編寫程式」加進去。

也可以執行 `brew install terminal-notifier`。裝好後會自動改用它送出通知，記得在通知和專注模式的設定裡允許「terminal-notifier」。

### Linux

需要桌面環境和 `notify-send`（`sudo apt install libnotify-bin`）。

## 已知限制

- Gemini CLI 版本太舊、還不支援 hooks 時，「在等你」只能看畫面有沒有變化來推測，可能不準。更新方法：執行 `npm install -g @google/gemini-cli`，再重新執行 `./install.sh`。
- 在管理畫面裡按 Shift+Enter 換行可能沒效果。Claude 可以改用 `\` 再按 Enter。
- tmux 3.2 的彈出視窗外框沒辦法顯示標題，3.3 以上才支援。
- 改變終端機視窗大小時，有些彈出視窗會被關掉，詳見上面的[改變視窗大小時，彈出視窗閃一下或被關閉](#改變視窗大小時彈出視窗閃一下或被關閉)。
- 在一般分頁執行中的 Agent，不會出現在管理畫面的清單裡。
- 協作組目前只支援 Claude。WSL / Linux 需要 bubblewrap 和支援 Landlock 的核心；macOS 用內建的 sandbox-exec，保護範圍比較小。
