# Vein Launcher

**English** | [简体中文](README-zh.md)

<p align="center">
  <img src="assets/logo.png" width="96" alt="Vein Launcher" />
</p>

<p align="center">
  <b>Minecraft, but cleaner.</b><br />
  A portable Minecraft Java launcher for Windows — install, manage, launch, and drive vanilla
  Minecraft without installing a single mod.
</p>

<p align="center">
  <a href="https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.5.1"><img alt="version" src="https://img.shields.io/badge/version-0.5.1-orange" /></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-2f6fe0" />
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-MIT-green" /></a>
  <img alt="tests" src="https://img.shields.io/badge/tests-51%20passing-1f9d55" />
</p>

---

## Highlights

| Area | What you get |
|---|---|
| **MLC** | A ~5 KB Java agent attaches to vanilla instances (no Fabric/Forge). Read player state, run commands, subscribe to game events. Master switch is off by default and hard-gates every capability. |
| **Command palette** | `Ctrl+Alt+Q` opens an enchanted-book style palette. Arrow keys to pick, `Enter` sends straight into the game, failures fall back to copying. |
| **Global hotkeys** | `Ctrl+Alt+0..9` run bound commands through MLC first, clipboard second. |
| **Plugins** | Every plugin runs in its own Node process with a declared permission set, path sandbox and 30 s timeout. Lua UI renders in a Shadow DOM. |
| **Downloads** | BMCLAPI mirror first, official Mojang fallback, resumable transfers, SHA-1 verification, no duplicate concurrent writes. |
| **Skins** | LittleSkin through authlib-injector; local PNG skins with a Fabric + CustomSkinLoader instance. |
| **Instances** | Isolated game folders, separate processes, per-instance MLC agent ports. |
| **UI (0.5.1)** | Light theme by default with an orange accent, plus customization: corner radius, interface zoom, motion toggle, any accent color. |
| **i18n** | English and Simplified Chinese across the launcher, logs UI and docs. |
| **Logs** | File-only, split by category (`launcher` / `download` / `mlc` / `plugin`) and rotated daily. Never dumped to the console. |

## Download

Get the latest build from **[GitHub Releases](https://github.com/zhanjhn-studio/vein_launcher/releases/latest)**:

| File | Size | Notes |
|---|---|---|
| `VeinLauncher-0.5.1-win64.zip` | ~199 MB | Windows x64, portable. Unzip and run `VeinLauncher.exe`. |
| `latest.json` | ~0.4 KB | Update manifest used when the GitHub API is rate-limited. |

SHA-256 of `VeinLauncher-0.5.1-win64.zip`:

```
BD6ADBC34054DB327B12621580B9C5749FF92D5AB5657FC04255C9016E7BC5E0
```

### Requirements

- Windows 10 / 11 x64
- Java is **not** required manually — the launcher detects installed runtimes or downloads the right major version
- Node.js 18+ only if you want to run plugins

### Install

1. Unzip the archive anywhere (for example `D:\VeinLauncher`).
2. Run `VeinLauncher.exe`. A `VeinLauncher/` data folder is created next to the executable.
3. Open **Download**, install a version (vanilla or a loader), then press **Launch**.

There is no installer and nothing is written to the registry. Deleting the folder uninstalls everything.

## Run from source

```bash
git clone https://github.com/zhanjhn-studio/vein_launcher
cd vein_launcher
python -m pip install -r requirements.txt
python -m vein_launcher.presentation.main
```

Build the frontend after changing anything under `webui/src` (the built `dist/` is what the Qt shell loads):

```powershell
cd vein_launcher/presentation/webui
powershell -ExecutionPolicy Bypass -File build.ps1
```

Run tests:

```bash
python -m unittest discover -s tests
python tools/plugin_selftest.py
python tools/mlc_selftest.py
```

## Build a release package

```bash
python tools/build_exe.py --version 0.5.1
```

Outputs `dist_exe/VeinLauncher/`, `dist_exe/VeinLauncher-0.5.1-win64.zip` and `dist_exe/latest.json`.

## Data layout

Everything lives beside the executable, so the folder can be moved or deleted as a whole:

```
VeinLauncher/
  config/       config.json, accounts.json, tools.json
  log/          launcher / download / mlc / plugin logs, one file per day
  minecraft/    instances, libraries, assets
  plugin/       Node plugins
  downloads/    download cache
  agent/        MLC agent jars
```

## Project layout

```
vein_launcher/
  common/           event bus, config, logging, i18n, utils
  domain/           models, repository contracts, rules
  infrastructure/   network, download, process, mc2, plugin host, MLC agent build
  application/      services (versions, skins, instances, update, plugins, game registry)
  mlc/              control layer protocol and state
  presentation/     Qt window, JSON-RPC bridge, command palette, webui/
    webui/          React 19 + TypeScript source and built dist/
tests/              pytest/unittest suite
tools/              build and self-test scripts (agent, packaging, UI preview, docs)
plugins_examples/   sample plugins (template, game-log, lua-ui, mlc-panel, status-panel)
assets/             logo and icons used by the launcher
```

Architecture rules: cross-layer communication goes through `common/events/event_bus.py`; the UI only
talks to the backend over JSON-RPC (`presentation/bridge.py`), never through direct IO calls.

## Plugins

A plugin is a folder under `VeinLauncher/plugin/` with a `package.json` that carries a `vein` block:

```json
{
  "name": "vein-plugin-hello",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "Hello",
    "activateOnStartup": false,
    "permissions": ["ui.notify", "config.read", "mlc.state"]
  }
}
```

```js
export async function activate(vein) {
  await vein.ui.notify("Hello", "Plugin ready");
  vein.mlc.on("game.enter", () => vein.log("entered a world"));
}
```

Available capabilities include `file`, `config`, `ui.notify/render/openPage`, `http.getJson`,
`download.queueTask`, `game.launch/running/command`, `app.info`, `versions.list` and the `mlc.*`
family (all gated by its permissions and by the MLC master switch).

See `plugins_examples/` for runnable examples, including `status-panel`, which renders launcher
version, installed instances, running games and MLC state in one panel.

## Contributing

- Bug reports and feature requests: [Issues](https://github.com/zhanjhn-studio/vein_launcher/issues)
- Questions and plugin sharing: [Discussions](https://github.com/zhanjhn-studio/vein_launcher/discussions)
- Pull requests: see [CONTRIBUTING.md](CONTRIBUTING.md). Use Conventional Commits and keep the layer
  boundaries intact. Rebuild `webui/dist` whenever you touch the frontend and add tests with new RPCs.

Security issues: please do not open a public issue — use GitHub private vulnerability reporting.

## License

[MIT](LICENSE) © 2026 zhanjhn studio.

Vein Launcher is not affiliated with Mojang or Microsoft. Minecraft is a trademark of Mojang Synergies AB.
