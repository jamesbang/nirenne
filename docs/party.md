# Parties: letting two agents talk to each other

**English** | [繁體中文](party.zh-TW.md)　·　[← Back to README](../README.md)

> 📌 Parties work with Claude only. Both members must be Claude Code, because a party relies on its cross-session messaging (SendMessage) and on resuming a conversation (`--continue`). Codex, Gemini, Antigravity and Grok can't join a party yet.

Here is an example. You have one Claude working on a web front end and another on its API. Put them in a party, then give your request to either one. It will message the other when it needs help, and when the work is done it reports back so you can check the result.

## Before you start

- Open two Claude agents in the manager.
- On WSL / Linux, install bubblewrap first. See the [Windows guide](install-windows.md#optional-for-parties).
- On macOS there is nothing to install.

## Forming a party

1. Click one of the Claude agents in the sidebar, for example `app`
2. Click [l Party]
3. Choose its partner, for example `my-api`
4. Read the reminder on the confirmation screen, then press `y` (or click [y Form party])

Both agents restart and pick up their previous conversations. The sidebar shows `🔗A ↔ 3 my-api`, and both members of a party share the same color.

A new party replaces any earlier one. If you want an agent to forget its earlier conversation and old partners, right-click it and choose "Drink the potion of forgetting". It starts over with a fresh conversation. You can still find the old one later with `/resume`.

## Giving a request

Type your request into either agent. Whoever you give it to becomes the leader.

While the request is in progress, the sidebar shows `· leader` next to that agent and `· member` next to the other. The labels go away once the work is done (✅).

When it is finished, the leader gives you a report: what changed on each side, the test results, and how you can verify the work.

## Reading the messages

Click [m Talk] to see what the two agents said to each other.

The messages are also saved to `~/.agent-manager/logs/collab-A.log`. When an agent drinks the potion of forgetting, the messages from earlier parties move to an archive file in the same folder, named `collab-A.log.<date>-<time>`.

## Disbanding a party

Click one of the agents, click [l Party], then press `y`. Both agents restart once more.

## The rules

When a party is formed, both agents are told these rules automatically:

- Change only your own project. Don't read or use anything from the partner's project, including passwords, and don't write code to get around this.
- When you need the partner's help, send it a message. You can read these messages with [m Talk].
- A request can go back and forth at most 3 times. Stop and ask the human before database schema changes, deleting data, deploying or merging.

## How the isolation works

Each agent runs inside its own sandbox. Whatever tool or program it uses, it can't read or change the partner's project.

### WSL / Linux: only listed places are writable

[bubblewrap](https://github.com/containers/bubblewrap) makes the whole system read-only, and the Landlock feature of the Linux kernel then lets the agent write only to:

- its own project folder
- its own private `/tmp`
- Claude's own data: a private copy of the settings for this agent, plus the conversation history of its own project
- private caches for build tools (see below)

Reading works the other way around: only specific places are blocked. These are the partner's project, the partner's conversation and prompt history, `~/.agent-manager`, `~/.claude.json`, and the Windows drives (except the agent's own project). Going through `/proc` or a symbolic link is blocked too.

Everything else can still be read. See [What is not isolated](#what-is-not-isolated) below.

### macOS

macOS uses its built-in Seatbelt (`sandbox-exec`). Reading or writing the partner's project fails with `Operation not permitted`.

These are protected as well:

- Can't be changed: this tool, the hook settings of each agent, and shell startup files
- Can't be read or written: `~/.agent-manager`, the real `~/.claude`, and the partner's Claude temporary folder. As on Linux, Claude in a party uses a private copy of its settings.
- Can't be run: `open`, `osascript`, `crontab` and `launchctl`

On macOS everything is allowed by default and only specific places are blocked, so it protects less than Linux does. See [Limits on macOS](#limits-on-macos) below.

### tmux

An agent in a party can only ask tmux where it is itself. It can't see or control its partner's pane.

## Places an agent can't write to (WSL / Linux)

When an agent tries to write to your home folder or to another tool's settings, it gets `Permission denied` or `Read-only file system`. The agent then tells you in plain words that it can't write to that place while in a party.

This is on purpose. It keeps the agent from leaving behind something that would later run outside the sandbox, such as `~/.bashrc` or `~/.gradle/init.d`.

### Build tool caches

The caches of Gradle, Maven, npm, yarn, pnpm, pip, NuGet, dotnet, Android and `~/.cache` are moved to a private folder for that agent while it is in a party, so builds work as usual. Your own `~/.gradle`, `~/.m2` and `~/.npm` are left alone.

### Adding your own private folders

If another tool also needs to write somewhere, such as `~/.cargo` for Rust, add a line to `~/.agent-manager/config` and form the party again. Separate several folders with `:`.

```
COLLAB_PRIVATE_DIRS=~/.cargo:~/.rustup
```

The first time the party is formed, the agent gets its own copy of each folder. From then on it only writes to its copy, and your original stays untouched.

These can't be added: your home folder itself and anything outside it, your own or the partner's project (or a folder above them), `~/.agent-manager`, `~/.config/agent-manager`, `~/.claude`, `~/.claude.json`, `~/.local/bin`, `/tmp`, and symbolic links.

### Where the private folders live

They are in `~/.agent-manager/sandbox/<project>-<id>/`. That folder holds the caches, the private `/tmp`, Claude's private settings and any folders you added.

It stays after the party is disbanded and is used again next time. To clear it, disband the party first, then delete the whole folder, for example:

```bash
rm -rf ~/.agent-manager/sandbox/my-api-1a2b3c4d
```

### Other things to know

- An agent in a party can't run Windows programs, such as `dotnet.exe` or a Visual Studio build.
- An agent in a party can't see other files on Windows drives such as `/mnt/c`. Put any file you want it to see into the project folder. The project itself can live on the C drive.
- If `settings.json`, `CLAUDE.md`, `skills` and so on under `~/.claude` are symbolic links (for example, managed with dotfiles), the party mounts their targets read-only. A target is skipped if it doesn't exist, isn't yours, or sits somewhere that can't be mounted, such as a project, `/tmp` or `~/.agent-manager`. Skipped items are listed in the message shown after the party is formed.

## Things to keep in mind

- ⚠️ Forming and disbanding a party restarts both agents. Any work in progress stops, and so do background programs they started, such as test servers. Do it while neither agent is working.
- The isolation keeps an agent from reading or changing the partner's project on its own. If you copy the partner's code somewhere else yourself and clearly tell the agent to read it, it may do so, since it treats a clear request from you as your decision. If you want an agent to look at the partner's code directly, disband the party first or summon a separate agent that isn't in one.
- WSL / Linux needs a kernel that supports Landlock. Without it you can't form a party, and the manager suggests updating WSL (run `wsl --update` in Windows PowerShell).
- A session outside the sandbox can't start a conversation with an agent in a party, though the agent in the party can message it.

### Claude uses a private copy of its settings

Claude in a party uses its own copy of the settings, stored in `~/.agent-manager/sandbox/…/claude-config`. As a result:

- Prompts typed during a party are not written back to `~/.claude/history.jsonl`. The first time a party is formed, only the history of the agent's own project is copied in.
- MCP changes made during a party are kept only in the private `.claude.json`, and the next party overwrites them with `~/.claude.json`. Disband the party first if you want to change MCP settings.
- Settings changed with `/config` during a party are not saved back to `~/.claude/settings.json`.

## What is not isolated

- Only the partner's project and the places listed above are blocked from reading. An agent in a party can still read a third person's project, `~/.ssh`, `~/.aws`, `~/.config/gh` and so on. Don't keep passwords, keys or other secrets in shared places outside your projects.
- Logins such as ssh-agent and `gh` are shared by everything running as your user, so an agent in a party can use them too.
- Processes aren't isolated, because party messages need to reach the other agent. An agent can therefore stop programs outside the sandbox, such as its partner. That only interrupts work; it can't change any files.
- The session registry used for messaging (`~/.claude/sessions`) and the socket folder are shared and writable. An agent in a party could rewrite other sessions' entries, or intercept or fake messages sent to them, but it can't change files.
- The login credentials (`~/.claude/.credentials.json`) are writable inside the sandbox, because Claude needs to refresh its token. An agent in a party can read or overwrite them.
- If the partner's project is a git worktree, the main repository's `.git` is not protected.

## Limits on macOS

- An agent in a party can't run `open` or `osascript`, send Apple Events or start programs through LaunchServices, so Claude won't open a browser for you. ⚠️ Log in before forming a party (Claude's `/login`, `gh auth login` and so on), or copy the URL into your browser yourself.
- Claude in a party keeps your existing login from the Keychain, so it doesn't need to log in again. If it still asks for `/login`, the browser won't open by itself; copy the URL shown on screen.
- Claude in a party already runs inside `sandbox-exec`, so don't turn on Claude Code's own `/sandbox`. macOS doesn't allow a sandbox inside a sandbox, and the command will fail.
- These places can't be written during a party, because they would later run outside the sandbox: `~/Library/LaunchAgents`, `~/.gradle/init.d`, `~/.gradle/init.gradle`, `~/.gradle/gradle.properties`, `~/.m2/settings.xml`, `~/.npmrc`, `~/.yarnrc`, `~/.yarnrc.yml`, and VS Code's user settings and extensions. `crontab` and `launchctl` can't be run either.
- macOS has no private caches, so the rest of `~/.gradle` and `~/.m2` stays writable. Builds need that.
- Every folder above a protected location can't be renamed, deleted or replaced with a link. Files can still be created inside them.
- The standard library and package folders of the Python this tool uses, and `~/Library/Python`, can't be written. Other programs installed with Homebrew (`/opt/homebrew`) still can.
- When a party is formed, the tool first creates any missing folders that tools need, such as `~/.gradle` and `~/.m2`. Once every party is disbanded, they are removed again if they are still empty.
- Programs like `open` are blocked by their fixed path. In testing, a copy run from somewhere else was killed by the system.
- Overall, macOS allows everything by default: places not listed here can still be read and written, and the protection is narrower than on Linux. Don't rely on it where strict isolation is required.
