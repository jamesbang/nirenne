# Security Policy / 資安政策

[English](#english) | [繁體中文](#繁體中文)

## English

nirenne runs AI coding agents and, in a party (collaboration group), isolates each agent from its partner's project with a sandbox (bubblewrap + Landlock on WSL / Linux, Seatbelt `sandbox-exec` on macOS). Because of this, we treat sandbox weaknesses as security issues.

### Reporting a vulnerability

**Please do not open a public issue.** Report privately through GitHub:

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Describe what an agent in a party can do that it should not, the platform (WSL / Linux / macOS and version), and the steps to reproduce.

You will get a reply when the report has been reviewed. Please give us a reasonable amount of time to fix the issue before you disclose it.

### What counts as a vulnerability

Things an agent in a party (or a message from its partner) can do, for example:

- read or change the partner's project or the partner's Claude conversations;
- make code run outside the sandbox (for example by changing this tool, hook settings, shell startup files, or files that Python or other tools load later);
- impersonate another session's status or control another agent's tmux pane;
- change this tool's settings or the `~/.agent-manager` state of other sessions.

### Known limitations (not vulnerabilities)

The [party documentation](docs/party.md) lists what the sandbox does **not** protect, especially on macOS, where the rules allow by default and block specific locations. For example: reading other places outside the partner's project such as `~/.ssh`, using shared login credentials, sending signals to processes outside the sandbox, and writing to programs installed by Homebrew. A way to bypass a protection that the documentation says **is** in place is a vulnerability.

### Supported versions

Only the latest version receives security fixes.

## 繁體中文

nirenne 用來執行 AI coding agent；組隊（協作組）時，會用沙箱把每個 Agent 與夥伴的專案隔開（WSL / Linux 用 bubblewrap 加 Landlock，macOS 用 Seatbelt 的 `sandbox-exec`）。因此沙箱的弱點一律當成資安問題處理。

### 回報漏洞

**請不要開公開的 issue。** 請透過 GitHub 私下回報：

1. 到 repo 的 **Security** 分頁。
2. 點 **Report a vulnerability**。
3. 說明組隊中的 Agent 能做到什麼不應該做到的事、使用的平台（WSL / Linux / macOS 與版本），以及重現步驟。

檢查完回報後會回覆你。公開細節前，請給我們合理的時間修正。

### 哪些算是漏洞

組隊中的 Agent（或夥伴傳來的訊息）能做到下列這類事情，例如：

- 讀取或修改夥伴的專案，或夥伴的 Claude 對話紀錄；
- 讓程式在沙箱外執行（例如修改本工具、hooks 設定、shell 啟動檔，或 Python 等工具之後會載入的檔案）；
- 冒充其他 Session 的狀態，或控制其他 Agent 的 tmux 畫面；
- 修改本工具的設定，或其他 Session 在 `~/.agent-manager` 的狀態。

### 已知限制（不算漏洞）

[協作組說明](docs/party.zh-TW.md)列出了沙箱**不**保護的範圍，特別是 macOS 採「預設允許、阻擋特定位置」。例如：讀取夥伴專案以外的地方（像 `~/.ssh`）、使用共用的登入憑證、對沙箱外的行程送訊號、寫入 Homebrew 安裝的程式。如果找到方法繞過文件寫明**有**保護的項目，就算是漏洞。

### 支援的版本

只有最新版本會收到資安修正。
