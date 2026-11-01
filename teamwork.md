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

