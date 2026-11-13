# 完整安裝教學（Windows）

[English](install-windows.md) | **繁體中文**　·　[← 回到 README](../README.zh-TW.md)

> 每一步都有「✅ 成功的樣子」，看到一樣的畫面再做下一步。

## 步驟 1：安裝 WSL（在 Windows 裡執行 Linux）

1. 按鍵盤的 **Windows 鍵**，輸入 `PowerShell`。
2. 在「Windows PowerShell」上按**滑鼠右鍵** →「**以系統管理員身分執行**」→ 按「是」。用「命令提示字元」（cmd）以系統管理員身分執行也可以。
3. 在視窗裡輸入下面這行，按 Enter：
   ```powershell
   wsl --install
   ```
4. 等它跑完，**重新開機**。
5. 重新開機後會自動跳出 Ubuntu 視窗（沒有的話，按 Windows 鍵輸入 `Ubuntu` 開啟）。等它安裝完，會要你設定：
   - `Enter new UNIX username:` → 輸入英文小寫的使用者名稱（例如 `amy`），按 Enter
   - `New password:` → 輸入密碼，按 Enter。**打字時畫面不會出現任何字，這是正常的**，照打就好
   - `Retype new password:` → 再輸入一次同樣的密碼

   這組密碼之後執行 `sudo` 指令時會用到，請記下來。

✅ 成功的樣子：出現像 `amy@電腦名稱:~$` 的文字，最後有一個游標在閃。

## 步驟 2：用 Windows Terminal 開啟 Ubuntu

- **Windows 11**：已經內建 Windows Terminal
- **Windows 10**：開啟「Microsoft Store」，搜尋 `Windows Terminal`，按「取得」安裝

開啟方式：按 Windows 鍵，輸入 `Terminal`，開啟「終端機（Windows Terminal）」→ 點上方分頁旁的 **⌄ 小箭頭** → 選 **Ubuntu**。

✅ 成功的樣子：新分頁出現 `amy@電腦名稱:~$`。**之後所有指令都在這種 Ubuntu 分頁輸入**（不是 PowerShell 或 cmd）。

也可以這樣進入：在 PowerShell 或命令提示字元（cmd）輸入 `wsl`，再輸入 `cd ~` 回到 Linux 家目錄。

> ⚠️ 專案請放在 Linux 家目錄（例如 `~/project`），不要放在 `/mnt/c/...`（Windows 的資料夾），否則 Agent 讀寫檔案會很慢。

## 步驟 3：安裝必要工具

在 Ubuntu 分頁輸入（會問密碼，輸入步驟 1 設定的密碼）：

```bash
sudo apt update && sudo apt install -y git tmux python3
```

確認版本：

```bash
tmux -V
```

✅ 成功的樣子：顯示 `tmux 3.2a` 或更大的數字（例如 `tmux 3.4`）。

> 如果出現 `404 Not Found` 之類的錯誤，通常是套件清單太舊，先執行 `sudo apt update` 再重試一次。

## 步驟 4：安裝至少一個 AI Agent（以 Claude Code 為例）

> Claude Code 需要 Pro、Max、Ultra、Team、Enterprise 等付費方案或 Console 帳號，免費的 claude.ai 方案不能使用。也可以透過 Amazon Bedrock、Google Cloud 或 Microsoft Foundry 等雲端服務使用。方案內容可能調整，以 [官方說明](https://code.claude.com/docs/en/setup) 為準。

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

下載時畫面不會顯示進度，請耐心等它跑完。裝好後**關掉這個分頁，再開一個新的 Ubuntu 分頁**，輸入：

```bash
claude
```

第一次會要你登入：照畫面指示，在瀏覽器登入你的帳號。登入完成、看到 Claude 的輸入框後，輸入 `/exit` 按 Enter 離開。

✅ 成功的樣子：輸入 `claude --version` 會顯示版本號（例如 `2.1.211 (Claude Code)`）。

> 如果顯示 `claude: command not found`：先確認你開的是**新的**分頁。還是不行的話，請參考官方的 [安裝問題排除](https://code.claude.com/docs/en/troubleshoot-install)。
>
> 安裝方式可能會更新，以官方文件為準：[Claude Code 安裝說明](https://code.claude.com/docs/en/setup)。
> 其他 Agent（Codex、Gemini、Antigravity、Grok）請依各自官方說明安裝，裝好後同樣先在一般分頁執行一次、完成登入。

## 步驟 5：安裝 nirenne

一行一行輸入：

```bash
git clone https://github.com/jamesbang/nirenne.git ~/nirenne
cd ~/nirenne
./install.sh
source ~/.bashrc
```

✅ 成功的樣子：最後出現「安裝完成。」以及 `nirenne`、`agent-help` 的說明。

## 步驟 6：開啟管理畫面

```bash
nirenne
```

也可以輸入較短的 `agents`，兩者完全相同。

✅ 成功的樣子：畫面左邊出現 Agent 清單，右邊是「NIRENNE」標題畫面。接著看[第一次使用](../README.zh-TW.md#第一次使用)。

## 選用：要使用協作組功能的話

（這是 WSL / Linux 的做法；macOS 不需要另外安裝，系統內建的 `sandbox-exec` 就能隔離。）

```bash
sudo apt install -y bubblewrap
bwrap --version
```

✅ 成功的樣子：顯示 `bubblewrap 0.6.1` 之類的版本號。
