# Usage

**English** | [繁體中文](usage.zh-TW.md)　·　[← Back to README](../README.md)

## Feature details

### The manager

Type `nirenne` to open the manager. The agent list is on the left and the selected agent is on the right. Almost everything can be done with the mouse.

Right-click an agent in the list (or click the ⋮ next to its name) to go to it, set its label, copy its reply, form a party, read its party messages, drink the potion of forgetting, or remove it. You don't have to switch to it first.

When there are many agents, or the terminal window is short, the list switches to a compact layout. If it still doesn't fit, scroll with the mouse wheel or click ▲ / ▼. Agents that are scrolled out of view are highlighted in yellow when they are waiting for you.

### Knowing when an agent is waiting for you

- Claude, Codex, Antigravity, Grok and Gemini report through their official hooks when they finish a reply or need your approval, so the status is accurate. For Antigravity, "waiting for your approval" is detected from the confirmation menu on screen.
- If Gemini CLI is too old to support hooks, an unchanged screen for 8 seconds is treated as "waiting for you". That is a guess and can be wrong now and then. As soon as one report arrives, it switches back to using the reports.

### Status, time and topic

- Each agent shows its current status, such as `✅ Done — your turn`, `✋ Waiting for you`, `⚔ Working` or `⏳ Waiting for xxx`. See [Status](#status) below for the full list.
- It shows how long the current task took, for example `✅ Done — your turn (3m12s)`. While the agent is working, the time updates every second.
- The task topic comes from the conversation title that Claude generates. You can also set your own label; it is only shown on screen and never sent to the agent.
- The status bar at the bottom always shows the current agent's version and model (for example `Claude Code v2.1.322 · Opus 5.5`), its full path and its Git branch.

### Background work and notifications

- Closing the terminal doesn't stop your agents. Type `nirenne` again to come back.
- ⚠️ Shutting down or restarting the computer ends the manager and every agent. Nothing is kept.
- When an agent finishes (✅) or needs your approval (✋), a Windows, macOS or Linux notification pops up. The agent you are looking at doesn't notify you. Notifications also arrive when the terminal is closed and agents are running in the background.
- When the main task hands work to background subtasks (squads), you get a "☑ Squad returned" notification for each squad, noting that the main task isn't done yet. The "done" notification comes only when everything has finished.

### Other

- Parties: pair two Claude agents (for example, a front end and an API) so they message each other to finish your request. Each one can change only its own project and can't see the other's folder. Claude only for now. See [Parties](party.md).
- Hard to close by accident: closing an agent always asks first. Every popup closes with Esc, and shortcuts the tool doesn't use are turned off.
- The interface comes in English and Traditional Chinese. It follows your system language the first time; after that, press g in the handbook ([? Help]) to switch, and every screen updates right away. You can also choose it when installing with `./install.sh --lang en` (or `--lang zh-TW`).
- Your usual workflow still works: `cd project && claude` as before.

## Opening and leaving

```bash
nirenne          # open the manager, or reattach to it
nirenne stop     # stop the manager and every agent in it (asks first)
```

- Click [q Rest] at the top right to go back to your normal terminal. Agents keep running in the background; type `nirenne` to come back.
- Closing Windows Terminal works the same way. Your agents keep going.
- ⚠️ Shutting down or restarting the computer ends the manager and every agent. After starting up again, type `nirenne` and summon your agents; Claude can pick up earlier conversations with `/resume`.

## The sidebar

| Action | Key | What it does |
|---|---|---|
| Click an agent | ↑↓ + Enter, or a number key | Switch to that agent |
| Right-click an agent | | Open that agent's command menu (see below the table) |
| Click the ⋮ next to an agent's name | | Open the same menu |
| `[+ New]` | `n` | Choose an agent type and a project folder to start a new agent |
| `[t Label]` | `t` | Set your own label, to tell agents apart |
| `[x Leave]` | `x` | Close the agent under the cursor (asks again first) |
| `[l Party]` | `l` | Put two Claude agents in a party, or disband it. See [Parties](party.md) |
| `[m Talk]` | `m` | Read a party's messages |
| `[? Help]` | `?` | Open the adventurer's handbook; press g there to switch language |
| `[q Rest]` (top right) | `q` | Leave the screen; agents keep running in the background |
| Mouse wheel, or click `▲` `▼` | | Scroll the list when it doesn't fit |

A few more details:

- The right-click menu has Go to, Set label, Copy reply, Form party, Party messages, Drink the potion of forgetting, and Remove. You don't need to switch first. For example, while you are in agent 1 you can right-click agent 6 and close it.
- Copy reply (Claude, Codex, Grok and Antigravity) lists the agent's latest reply and each code block in it; pick one to copy the original text. Use ←→ to go to earlier replies. To copy just part of it, drag in the preview, or click the first line, scroll, then click the last line. The copied lines are highlighted and the window stays open, so you can copy more; press Esc to close it. This is the easiest way to copy long output such as SQL from Claude Code.
- The potion of forgetting only works for an agent in a party. The agent starts over with a fresh conversation and forgets its old conversation and partners. Messages from earlier parties go into an archive; the current party's messages are kept.
- If your terminal catches the right-click and shows its own menu, click the ⋮ instead.
- Labels are only shown on screen and never sent to the agent. Clear the label and press Enter to go back to the automatic topic.
- Party messages and the handbook cover the whole screen for a while. Press Esc or q to close them.
- Keys only work while the cursor is in the sidebar, so click the sidebar first. Pressing `x` or `q` in an agent pane on the right just types those letters.
- Keys work in upper or lower case, and with full-width characters too, so they still work while a Chinese input method is on.
- Every popup closes with Esc.

## Status

| Status | Meaning |
|---|---|
| `✅ Done — your turn (3m12s)` | Finished and waiting for you; the time in brackets is how long it took |
| `✋ Waiting for you` | The agent needs your approval for something, or is asking you a question |
| `⚔ Working (25s)` | Still working; the time in brackets is how long so far |
| `✨ Summoning` | Just summoned and starting up |
| `💤 Standing by` | Started, but you haven't given it anything to do yet |
| `⏳ Waiting for app` | In a party: waiting for its partner to report back (not for you) |
| `🏹 Squads out ×2` | The main task sent out background subtasks (squads) and is waiting for them (not for you) |

## Other controls

- Scroll up with the mouse wheel to see an agent's earlier output. Claude Code, Codex, Antigravity and Grok handle scrolling themselves. On the home screen and in Gemini, the bottom-right corner shows how many lines you have scrolled up; click the screen, press `q`, or scroll back to the bottom to return.
- Drag with the mouse to select text. It is copied to the clipboard when you let go, and a confirmation shows at the bottom right. Hold the pointer on the top or bottom line of the pane to scroll while selecting.
- To use your terminal's own selection instead, hold Shift while dragging in Windows Terminal, or Option in iTerm2.
- To paste, press Shift + right-click, or Ctrl+V (Windows) / Cmd+V (macOS). A plain right-click in the manager doesn't paste; hold Shift.
- If an agent exits (for example, you pressed Ctrl+C by mistake), its window doesn't close right away. You are asked to press `y` to remove it or `r` to restart it. If you restart it, Claude picks up the conversation it was in.
- To choose which project folders are listed when you summon an agent, add `export AGENTS_PROJECT_DIRS="~/work:~/oss"` to `~/.bashrc`. Separate folders with `:`.

## Using agents without the manager

Agents work as usual in a normal terminal tab, and the project, agent and Git branch are still recorded:

```bash
cd ~/project/my-api
claude          # or codex, gemini, agy (antigravity also works), grok
```

Other commands:

```bash
agent-list                          # list running sessions (-a lists all)
agent-topic "Fix login timeout"     # set the topic of the current session
agent-status CODING "Update auth"   # set the status by hand
agent-clean                         # remove records of finished sessions
agent-open claude                   # open a new Windows Terminal tab in this folder (Windows only)
agent-help                          # list all commands
```

## Taking over a conversation from another tab

An agent that is already running in a normal tab can't be moved into the manager. Claude saves its conversations, though, so you can pick one up again:

1. In the original tab, leave Claude (type `/exit`)
2. In the manager, use [+ New] to start Claude in the same project
3. Type `/resume` and choose that conversation

⚠️ Don't have the same conversation open in two places at once.

## Customizing

| File | Purpose |
|---|---|
| `agents.py` | The manager: sidebar, New menu, parties, Claude hooks |
| `agent-manager.sh` | Shell commands: the wrappers for `claude` and the others, `agent-list` and more |
| `tmux.conf` | tmux settings for the manager: status bar, mouse, keys |
| `agents` | The launcher, installed under two names, `nirenne` and `agents` |

Common tweaks are at the top of `agents.py`:

- `SIDEBAR_W`: the width of the sidebar
- `IDLE_SECS`: how many seconds of an unchanged screen count as "waiting for you"
- `AGENT_TYPES`: the supported agents and their commands. Agents that aren't installed are greyed out in the New menu.

Run `./install.sh` again after making changes.

To turn off notifications, add `export AGENTS_NOTIFY=0` to `~/.bashrc` (for zsh, `~/.zshrc`), run `nirenne stop`, then open `nirenne` again.

## Updating and uninstalling

Run `nirenne --version` or `nirenne -v` to see the installed version. For what changed in each version, and anything to watch out for when updating, see the [changelog](../CHANGELOG.md).

### Update to a new version

```bash
cd ~/nirenne
git pull
./install.sh
```

A running manager switches to the new version by itself, including the sidebar, party proxies, keys, status bar and right-click menu. You don't need to restart it, and your agents keep running.

### What the installer changes

| File | Change |
|---|---|
| `~/.bashrc` or `~/.zshrc` | Adds a loader block, marked with `# >>> nirenne >>>` |
| `~/.claude/settings.json` | Adds hooks, after backing the file up as `settings.json.bak-<date>`. The hooks only act on Claude started by this tool, and Claude keeps working even if they fail |
| `~/.codex/hooks.json` | Adds hooks if Codex is installed (backed up first). Codex may ask you to trust them the first time it starts |
| `~/.gemini/settings.json` | Adds hooks if Gemini CLI is installed (backed up first) |
| `~/.gemini/config/hooks.json` | Adds hooks if Antigravity (`agy`) is installed (backed up first) |
| `~/.config/agent-manager/` | The program and its tmux settings |
| `~/.local/bin/nirenne`, `~/.local/bin/agents` | The launcher, under two names for the same program. If a name is already used by another program, the installer skips it instead of overwriting it |
| `~/.agent-manager/` | Session records and party messages, kept only on your computer. Its `sandbox/` folder holds each agent's private folder for parties, such as caches |

The manager uses its own tmux socket (`agents`) and its own settings file, so your normal tmux setup isn't affected.

### Uninstall

```bash
cd ~/nirenne
./uninstall.sh
```

The uninstaller:

- removes the loader block from your shell settings
- removes this tool's hooks from `~/.claude/settings.json`, `~/.codex/hooks.json`, `~/.gemini/settings.json` and `~/.gemini/config/hooks.json`, backing each one up first
- deletes the installed program
- asks whether to delete the session records
