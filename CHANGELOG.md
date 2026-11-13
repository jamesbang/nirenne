# Changelog

**English** | [繁體中文](CHANGELOG.zh-TW.md)

Version numbers use the `major.minor.patch` format. Fixes increase the patch number and new features increase the minor number. Incompatible changes are listed in that version's update notes. While the version is `0.x`, features and controls may still change.

## 0.1.0 — 2026-11-13

Initial release.

### The manager

- Manage Claude Code, Codex CLI, Gemini CLI, Antigravity CLI and Grok CLI in one terminal screen, and switch between them with the mouse.
- See each agent's project, Git branch, task topic, status and time spent.
- The status bar shows the current agent's version and model. When you scroll up, it also shows how far.
- Right-click an agent, or click the ⋮ next to its name, to open its command menu. The ⋮ is there for terminals that catch the right-click.
- Long text windows, such as party messages, scroll smoothly and close right away.
- A farewell screen appears when an agent leaves the party, with a face picked at random from (つд⊂)ｴｰﾝ, (ಥ_ಥ) and ( ;´༎ຶД༎ຶ`).
- The interface comes in Traditional Chinese and English, and you can switch in the handbook. Choose one when installing with `--lang en` or `--lang zh-TW`; otherwise it follows the system language.
- Works with macOS terminal colors, pane borders and window resizing, and handles special characters, paths and missing locales.

### Status and notifications

- When an agent finishes or needs your approval, a Windows (WSL), macOS or Linux notification pops up. On macOS, terminal-notifier is used when it is installed.
- See the progress of background subtasks (squads), with a notification each time one finishes.
- When Codex reports through a shared background service, its events are matched to the right session by conversation ID. If the match isn't clear, it doesn't guess.

### Parties

- Two Claude agents can form a party and message each other to finish your request, while each is kept away from the other's project.
- On WSL / Linux, bubblewrap and Landlock isolate the agents. An agent can write only to its own project, a private `/tmp` and private caches.
- On macOS, the built-in sandbox-exec isolates the agents:
  - They can't read `~/.agent-manager`, the real `~/.claude` or the partner's Claude temporary folder. Claude in a party uses a private copy of its settings.
  - They can't run `open`, `osascript`, `crontab` or `launchctl`.
  - They can't write to places such as LaunchAgents that would later run outside the sandbox, or to the standard library and package folders of the Python this tool uses (including `~/Library/Python`).
  - They can't rename the folders above a protected location or replace them with links, and they can't change their own proxy folder.
- Whoever receives your request becomes the leader. Leader and member are worked out from the request ID (REQ-…), even when the partner's message has no tag, and are shown only while the request is in progress.
- "Drink the potion of forgetting" 🧪(｀・ω・´) in the right-click menu: an agent in a party starts over with a fresh conversation and forgets its old conversation and partners. Messages from earlier parties move to an archive file and can be recovered; the current party's messages are kept.

### Installing and updating

- The launcher is `nirenne`, and the shorter `agents` works exactly the same. If a name is already used by another program, the installer skips it instead of overwriting it, and the uninstaller leaves unrecognized launchers alone.
- Run `nirenne --version` or `nirenne -v` to see the version. Unsupported arguments show the usage instead of opening the manager by mistake.
- The installer ends by listing the common commands, including `nirenne stop` and `nirenne --help`; `agent-help` lists every command.
- After an update (re-running install.sh), the sidebar and a party's proxies switch to the new version within a few seconds. You don't need to restart the manager or form the party again. The new version is loaded once as a check first, and the old one keeps running if that fails.
- The installer replaces files in one step, so a running manager never reads a half-written file. A broken agent settings file doesn't stop installation or uninstallation.
- Every call to this tool outside the sandbox runs Python with `-I`, so packages the user installed aren't loaded.

### Update notes

- Parties support Claude only. WSL / Linux needs bubblewrap and a kernel with Landlock. macOS uses the built-in sandbox-exec, which was tested on a real Mac on 2026-11-13 but protects less than Linux. Don't turn on Claude Code's `/sandbox` while in a party.
- If Gemini CLI is too old to support hooks, "waiting for you" can only be guessed from screen changes, so it may be wrong.
- Agents keep running after you close the terminal, but not after the computer shuts down or restarts.
