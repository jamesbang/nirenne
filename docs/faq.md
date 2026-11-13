# Troubleshooting

**English** | [繁體中文](faq.zh-TW.md)　·　[← Back to README](../README.md)

## `nirenne` says `command not found`

Close the terminal tab and open a new one. Or run the `source` command shown at the end of the installation.

This tool supports bash and zsh (bash is the default on Ubuntu, zsh on macOS). Other shells, such as fish, aren't supported yet.

## "You are already inside the manager"

You're already in the manager, so there's no need to open it again.

## An agent is grey in [+ New] ("not in your guild yet")

Its command can't be found, so it probably isn't installed. Select it to see how to install it.

Once it is installed, check it in a normal tab with its version command (for example `claude --version`), then come back and summon it.

## My project folder isn't listed in [+ New]

Choose the last entry, "Other path… (type it)", and type the path yourself.

You can also set `AGENTS_PROJECT_DIRS` so the list includes the folders you use most. See [Other controls](usage.md#other-controls).

## Right-click doesn't paste

The manager can be used with the mouse, so a plain right-click goes to the manager and opens its menu.

To paste, press Shift + right-click (Windows Terminal's usual paste) or Ctrl+V.

## Keys (n, x, t…) do nothing

Click the sidebar first so the cursor is in the list, then press the key.

## The status never updates

Only agents started from the manager, or through this tool's wrapped commands such as `claude`, report their status.

If it still looks wrong:

1. Run `./install.sh` again.
2. If that doesn't help, look at the last few lines of `~/.agent-manager/logs/hooks.log`. If events are being logged, the hooks are running. A `skip=` or `error=` entry says why something was skipped or where it failed. Please include these lines when you report a problem.

## Chinese text looks garbled

Run `echo $LANG`. The output should include `UTF-8`. If it doesn't, run:

```bash
echo 'export LANG=C.UTF-8' >> ~/.bashrc && source ~/.bashrc
```

## Popups flicker or close when the window is resized

Some systems close popups when the window size changes. Here is what happens to each kind:

- The handbook and party messages resize along with the window.
- The recruit help reopens at the new size and keeps its scroll position.
- Popups where you type something, such as New, Label and Party, close. Just open them again.
- The right-click menu closes. Right-click again.

## [l Party] says bwrap was not found

Run `sudo apt install -y bubblewrap`. Only WSL / Linux needs it.

## [l Party] says the Linux kernel doesn't support Landlock

Run `wsl --update` in Windows PowerShell, open WSL again and try once more.

## [l Party] says only Claude is supported

A party can only join two Claude agents. Codex, Gemini, Antigravity and Grok can't join a party yet.

## I want to stop every agent

In a normal terminal (not inside the manager), run `nirenne stop` and press `y` to confirm.

## Right-click opens iTerm2's own menu

1. Open Settings → Profiles → Terminal and check Enable mouse reporting and Report mouse clicks & drags.
2. If you right-click with Control + click, also go to Settings → Pointer and check Ctrl-click reported to apps, does not open menu.
3. If it still doesn't work, click the ⋮ next to the agent's name. It opens the same menu.

## Not getting notifications

### Windows

Notifications are sent as "Windows PowerShell". Check that they are turned on in Settings → System → Notifications, and that Do Not Disturb is off.

### macOS

Notifications are sent as "Script Editor". Allow it once in System Settings → Notifications.

A Focus mode (Do Not Disturb, Personal, Sleep and so on) blocks them. Go to System Settings → Focus → that mode → Allowed Notifications → Apps, and add Script Editor.

You can also run `brew install terminal-notifier`. Once it is installed, notifications are sent through it instead; remember to allow "terminal-notifier" in the Notifications and Focus settings.

### Linux

You need a desktop session and `notify-send` (`sudo apt install libnotify-bin`).

## Known limitations

- If Gemini CLI is too old to support hooks, "waiting for you" can only be guessed from whether the screen changes, so it may be wrong. To update, run `npm install -g @google/gemini-cli`, then run `./install.sh` again.
- Shift+Enter may not insert a new line inside the manager. In Claude, type `\` and then press Enter instead.
- tmux 3.2 can't show titles on popup borders. tmux 3.3 and later can.
- Some popups close when the terminal window is resized. See [Popups flicker or close when the window is resized](#popups-flicker-or-close-when-the-window-is-resized) above.
- Agents running in a normal terminal tab don't appear in the manager's list.
- Parties support Claude only. WSL / Linux needs bubblewrap and a kernel with Landlock; macOS uses the built-in sandbox-exec, which protects less.
