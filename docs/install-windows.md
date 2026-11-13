# Step-by-step install (Windows)

**English** | [繁體中文](install-windows.zh-TW.md)　·　[← Back to README](../README.md)

> Every step ends with "✅ What success looks like". Only move on when your screen matches.

## Step 1: Install WSL (Linux inside Windows)

1. Press the **Windows key** and type `PowerShell`
2. **Right-click** "Windows PowerShell" → **Run as administrator** → click "Yes" (Command Prompt / cmd run as administrator works too)
3. Type the following line and press Enter:
   ```powershell
   wsl --install
   ```
4. When it finishes, **restart your computer**
5. After the restart an Ubuntu window opens automatically (if not, press the Windows key, type `Ubuntu` and open it). When it finishes installing, it asks you to:
   - `Enter new UNIX username:` → type a lowercase user name (e.g. `amy`) and press Enter
   - `New password:` → type a password and press Enter. **Nothing appears on screen while you type. That's normal**
   - `Retype new password:` → type the same password again

   You will need this password whenever you run a `sudo` command, so write it down.

✅ What success looks like: a line such as `amy@your-pc:~$` with a blinking cursor.

## Step 2: Open Ubuntu in Windows Terminal

- **Windows 11**: Windows Terminal is already installed
- **Windows 10**: open the Microsoft Store, search for `Windows Terminal`, click "Get"

To open it: press the Windows key, type `Terminal`, open Windows Terminal → click the **⌄ arrow** next to the tabs → choose **Ubuntu**.

✅ What success looks like: the new tab shows `amy@your-pc:~$`. **Type every command from now on in an Ubuntu tab like this** (not in PowerShell or cmd).

**Another way in**: type `wsl` in PowerShell or Command Prompt (cmd), then `cd ~` to go to your Linux home folder.

> ⚠️ Keep your projects in the Linux home folder (e.g. `~/project`), not under `/mnt/c/...` (Windows folders); otherwise agents read and write files much more slowly.

## Step 3: Install the required tools

In the Ubuntu tab (it asks for the password from step 1):

```bash
sudo apt update && sudo apt install -y git tmux python3
```

Check the version:

```bash
tmux -V
```

✅ What success looks like: `tmux 3.2a` or a higher number (e.g. `tmux 3.4`).

> If you get an error such as `404 Not Found`, the package list is out of date: run `sudo apt update` and try again.

## Step 4: Install at least one AI agent (Claude Code as an example)

> Claude Code requires a Pro, Max, Ultra, Team or Enterprise plan, or a Console account; the free claude.ai plan does not include it. It can also be used through Amazon Bedrock, Google Cloud or Microsoft Foundry. Plans may change; see the [official setup guide](https://code.claude.com/docs/en/setup).

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

The installer shows no progress while downloading, so just wait for it to finish. Then **close this tab and open a new Ubuntu tab**, and run:

```bash
claude
```

The first time, it asks you to log in: follow the prompts and sign in with your browser. Once you see Claude's input box, type `/exit` and press Enter.

✅ What success looks like: `claude --version` prints a version number (e.g. `2.1.211 (Claude Code)`).

> If you see `claude: command not found`, make sure you opened a **new** tab; if it still fails, see the official [installation troubleshooting](https://code.claude.com/docs/en/troubleshoot-install).
>
> The install method may change; the official docs are authoritative: [Claude Code setup](https://code.claude.com/docs/en/setup).
> Install the other agents (Codex, Gemini, Antigravity, Grok) following their official instructions, and run each once in a normal tab to log in.

## Step 5: Install nirenne

Run these lines one by one:

```bash
git clone https://github.com/jamesbang/nirenne.git ~/nirenne
cd ~/nirenne
./install.sh
source ~/.bashrc
```

✅ What success looks like: the last lines read "Installation complete" followed by short descriptions of `nirenne` and `agent-help`.

## Step 6: Open the manager

```bash
nirenne
```

The shorter `agents` works exactly the same.

✅ What success looks like: the agent list on the left and the "NIRENNE" title screen on the right. Continue with [First use](../README.md#first-use).

## Optional: for parties

(This is for WSL / Linux; macOS needs nothing extra, since the built-in `sandbox-exec` provides the isolation.)

```bash
sudo apt install -y bubblewrap
bwrap --version
```

✅ What success looks like: a version such as `bubblewrap 0.6.1`.
