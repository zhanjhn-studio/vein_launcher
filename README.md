# Vein Launcher

**English** | [简体中文](README-zh.md)

A Minecraft Java Edition launcher for Windows, built to be practical rather than decorative:
strict layering in Python, a React + TypeScript interface, a Node.js plugin host, and a
self-designed control layer (MLC) that lets plugins drive the game.

---

## Highlights

| Area | What we do |
|---|---|
| Architecture | Python (Common / Domain / Infrastructure / Application / Presentation) + PySide6 WebView |
| Frontend | React 19 + TypeScript, JSON-RPC 2.0 bridge, 7 top-level pages, 3-pane layouts |
| Plugins | Node.js host in a separate process, bidirectional JSON-RPC, permission checks, path sandbox, hot reload |
| MLC | Launch game, read saves, subscribe to game events — exposed to plugins with permissions |
| Downloads | BMCLAPI mirror first, automatic fallback to Mojang, SHA-1 verification, resume, same-target serialization |
| Logs | File only (never the console): `launcher/plugin/mlc/download` split by category, daily files |
| Data | `VeinLauncher/` next to the executable: `plugin/`, `log/`, `config/`, `minecraft/`, `downloads/`, `democrat/` |

## Requirements

- Windows 10/11
- Python 3.11+
- Node.js 18+ (plugin host)

## Project layout

```
vein_launcher/            Python package (five layers)
├── common/               event bus, config, logging, i18n, utils
├── domain/               models, repository contracts, domain rules
├── infrastructure/       network, download, process, mc2, plugin host
├── application/          services (version/skin/instance/update/…)
├── mlc/                  Minecraft Launcher Control bridge
└── presentation/         Qt window + JSON-RPC bridge + webui/
    └── webui/            React 19 + TS frontend
        ├── src/          app source (pages, components, lib)
        ├── assets/       icons + Layui vendor (tracked)
        └── build.ps1     bundle + copy static assets to dist/
tests/                    pytest/unittest suite
tools/                    maintenance scripts
packaging/                PyInstaller entry + build output (ignored)
docs/                     extra notes archived from team branches
assets/                   logo, wordmark
plugins_examples/         sample Node plugins
```

## Run from source

```bash
python -m pip install -r requirements.txt
python -m vein_launcher.presentation.main
```

The launcher creates its data root on first start:

```
<exe or repo>/VeinLauncher/
├── democrat/     community data (reserved)
├── plugin/       Node plugins
├── log/          daily logs per category
├── config/       launcher configuration
├── minecraft/    versions, libraries, assets
└── downloads/    download cache
```

## Frontend build

```bash
cd vein_launcher/presentation/webui
esbuild src/main.tsx --bundle --outfile=dist/app.js --jsx=automatic --minify
```

The built `dist/` is part of the repository; rebuild only after changing `src/`.

## Communication

Frontend ↔ Python uses JSON-RPC 2.0 over QWebChannel:

```json
{"jsonrpc": "2.0", "id": 12, "method": "versions.install", "params": {"args": ["1.20.1", "fabric"]}}
```

Push channels: `__veinProgress`, `__veinLog`, `__veinNotify`, `__veinNavigate`.

## Plugin quick start

```js
export async function activate(vein) {
  vein.log(`hello from ${vein.plugin.displayName}`);
  await vein.file.writeText(`${vein.plugin.dataDir}/hello.txt`, 'hi');
  vein.mlc.on('game.log', (e) => vein.log(e.line));
}
```

`package.json` declares permissions under `vein.permissions`; anything not declared is rejected
by the host.

## Status

Implemented: version install (vanilla + Fabric/Quilt), Modrinth browse/install with thumbnails,
plugin host + management UI, MLC launch/saves/events, mirrors, categorized file logging.

Planned: announcement & forced update (zhanjhn.github.io), automatic Java download, MC2 seed/world
analysis, Lua UI sandbox, plugin marketplace.

## License

See [LICENSE](LICENSE).
