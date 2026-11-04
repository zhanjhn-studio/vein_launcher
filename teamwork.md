# Teamwork Log

Shared change log for the Vein Launcher repository. **Read this file before making any
change, and append an entry after every change** so the other members stay in sync.

## How we work

1. `git pull` → read `teamwork.md` (this file) → check "In progress" before touching code.
2. Make the change in small steps, run the checks (`python -m unittest discover -s tests`,
   frontend build via `vein_launcher/presentation/webui/build.ps1`).
3. Append one entry at the bottom of "Change log" (newest last):
   `YYYY-MM-DD · area · what changed · files · verification · commit`.
4. Commit code and this file together, then `git push`.
5. If you stop mid-way, move the item to "In progress" with the exact next step.

### Entry template

```
- **2026-11-01 · ui/sidebar** — 280ms hover expand, labels slide in · `src/styles.css` · tests 44 OK, rAF sampled 68→208 · `38942ad`
```

## Current baseline

- Version: **0.1.0** (`vein_launcher/presentation/context.py`)
- Release: [v0.1.0](https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.1.0)
  (assets: `VeinLauncher-0.1.0-win64.zip`, `latest.json`)
- Defaults: dark theme · English UI (switch to 简体中文 in Settings → Appearance) ·
  **compact mode OFF** · idle fade 60 s · no wallpaper
- Build: PyInstaller onedir (`packaging/entry.py`), frontend `build.ps1`
- Tests: 44 (`tests/`)

## In progress

- [ ] Nothing blocking. Next candidates: wallpaper/compact polish after user feedback,
      world-analysis table (MC2), in-place self-update (updater script), Microsoft login
      waiting on Minecraft Services approval.

## Change log

- **2026-11-01 · domain/pydantic** — migrated 6 Pydantic models in `version.py` from the
  deprecated v1 class-style `Config` to `model_config = ConfigDict(populate_by_name=True)`;
  `PydanticDeprecatedSince20` warnings cleared to zero · `domain/models/version.py` ·
  tests 44 OK, 0 pydantic warnings
- **2026-11-01 · plugins** — plugin system hardening:
  (1) host auto-restart on unexpected exit, up to 3 retries with backoff, reloads
  previously loaded plugins; `_stopping` guards clean shutdown;
  (2) `CapabilityRegistry` gains per-capability timeout (default 30 s) →
  `CapabilityTimeoutError`, plus `describe()` for the plugin page;
  (3) new `ui.openPage` capability (permission `ui.open_page`) exposed as
  `vein.ui.openPage(page)` in the Node runtime;
  (4) `PluginService.state()` now returns host `restarts`, `examples`, `capabilities`,
  and per-plugin `dataDir`; new `examples()` / `capabilities()` helpers;
  (5) plugin template documents the sandbox rule and the `openPage` call ·
  `plugin_host/host.py`, `capabilities.py`, `runtime/node_host.js`,
  `plugins_examples/template/index.js`, `application/services/plugin_service.py` ·
  `tools/plugin_selftest.py` 9/9 PASS (load → capability call → path escape blocked →
  undeclared permission blocked → timeout → unload), `node --check` OK, tests 44 OK

- **2026-11-01 · repo** — removed the nested `vein_launcher v0.5/` copy (158 files), archived its
  docs to `docs/`, dropped duplicate `src/bridge.js` and `zh_strings.txt`, moved `scan_left.py`
  to `tools/` · repo tree · tests 44 OK · `f4391c3`
- **2026-11-01 · ui/prefs** — merged teammate's wallpaper + compact mode + idle fade
  (`UIConfig`, `ui.prefs` / `ui.setPrefs` / `ui.importWallpaper`, `prefs.ts`) · `styles.css`,
  `App.tsx`, `launchPage.tsx`, `settingsPage.tsx`, `bridge.py`, `settings.py` · build OK · `f4391c3`
- **2026-11-01 · ui/sidebar** — smoother expand (0.28s, `cubic-bezier(.16,1,.3,1)`), labels
  slide in with 60 ms delay, nav hover shift 2px, idle fade transition · `src/styles.css` ·
  rAF sampled 68→208, tests 44 OK · `38942ad`
- **2026-11-01 · ui/defaults** — compact mode defaults to **off**; documented in this file so a
  fresh checkout/run never starts as a drawer · `settings.py`, `prefs.ts` ·
  `config.json` has no `compact_mode` key → `False` · `68f4961`
- **2026-10-31 · release** — v0.1.0 published (zip + latest.json), PyInstaller packaging,
  one-click update with GitHub → latest.json → announcements fallback · `update_service.py`,
  `packaging/` · update detection tested (`0.0.3 → 0.1.0`), packaged exe launched · `cfda55c`
- **2026-10-31 · download** — per-file progress, failures surfaced, concurrency 8,
  LittleSkin public skin library (`/skinlib/list`) · `queue.py`, `version_service.py`,
  `littleskin.py` · install 1.20.1 3640/3640, tests 44 OK · `9a759ab`
- **2026-10-31 · instances** — instance detail page (mods/RP/shader/datapack/modpack, worlds,
  seed scan, delete) · `instance_service.py`, `instancePage.tsx` · tests 40 OK · `f3219dd`
- **2026-10-31 · skins** — import PNG, LittleSkin profile skin, library download · `skin_service.py`,
  `skinsPage.tsx` · tests 32 OK · `b2786cb`
- **2026-10-31 · onboarding** — full-page wizard (5 steps, privacy consent) · `onboarding.tsx`,
  `styles.css` · screenshot verified · `51b4733`
- **2026-10-31 · images** — allow remote images from `file://` pages
  (`LocalContentCanAccessRemoteUrls`), `RemoteIcon` fallback · `main.py`, `ui.tsx` ·
  Modrinth icon loads (96×96), `ebf7f6a`

- **2026-11-03 · docs** — added v0.1.0 internal doc (architecture, modules, release flow, risks)
  and a dedicated discussion page · `docs/v0.1.0/*` · 44 tests OK · `5794fd1`
- **2026-11-04 · docs/word** — Word generator for the v0.1.0 internal doc (cover, TOC, styled
  tables, page footer, discussion page) · `tools/gen_internal_doc.py`, `docs/v0.1.0/README.md` ·
  docx reopened: 107 paragraphs / 10 tables / 19 headings · `c4a4566`
- **2026-11-04 · docs/branding** — internal Word doc now branded: full-page cover with big logo,
  "内部版本 · 请勿上传至 GitHub" warning, ZHANJHN Studio; logo in header of every page;
  "关于我们" page; discussion section condensed to exactly 2 pages (repeating table header,
  rows never split) · `tools/gen_internal_doc.py` · PDF preview 11 pages, cover + p10/p11
  reviewed · `b8a92f1`
- docx stays local: `*.docx` is gitignored, preview PDF/PNGs added to `.gitignore` — internal
  doc is **not** uploaded to GitHub
- **2026-11-04 · ui/polish** — sidebar gets a sliding active pill, icon spring/glow, hover light
  sweep, brand-logo tilt; dark theme is now the real default (`currentTheme()` fallback was
  `light`); primary buttons get the accent gradient in dark too; page mount uses staggered
  fade-up; cards lift on hover; version cards decluttered (mark shows 1.20, manage icon appears
  on hover); launch page gains three quick-action cards; removed large `backdrop-filter` layers
  that caused flicker · `styles.css`, `App.tsx`, `launchPage.tsx`, `theme.ts` ·
  offline preview (`tools/ui_preview.py`) rendered launch/download/skins · `90924f6`
- **2026-11-05 · docs/dev** — new developer-facing Word doc for v0.1.0
  (`VeinLauncher_开发者文档_v0.1.0.docx`, 15 pages): cover with logo, logo in every page header,
  architecture/protocol/plugin/instance/auth/update chapters, competitor comparison, status
  matrix, known limits, posts-API appendix, 3 blank team-record pages; generator reuses the
  internal-doc styling helpers · `tools/gen_dev_doc.py`, `tools/gen_internal_doc.py` ·
  Word export 15 pages, pages 1/2/15 reviewed · `git log -- tools/gen_dev_doc.py`
