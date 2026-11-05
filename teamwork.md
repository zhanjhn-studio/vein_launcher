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
- **2026-11-05 · docs/dev** — developer Word doc for v0.1.0 stays at **8 pages** but is denser:
  added chapter 9「开发约定与常见任务」(how to add an RPC method / page / plugin capability,
  pre-commit checklist, troubleshooting table) and appendix A.1「帖子系统落地建议」
  (6-step rollout + 3 design notes); appendix B trimmed from 3 → **2 blank pages**;
  appendix A gets its own page so its table no longer splits · `tools/gen_dev_doc.py` ·
  Word export 8 pages, pages 2/3/5/6 reviewed · `git log -- tools/gen_dev_doc.py`
- **2026-11-05 · tests/contracts** — 新增两条 AST 静态契约回归：`bridge` 调用
  `LauncherService.launch` 的关键字/位置参数必须匹配签名（抓本次 `uuid=` 漂移）；
  `download/` 下 `DownloadError` 家族构造必须匹配各自 `__init__`（抓 `status=` 漂移，
  含子类 `super().__init__` 校验与 `status` 不进 `DownloadError` 的回归锚点） ·
  `tests/test_rpc_launch_contract.py`、`tests/test_download_error_contract.py` ·
  `python -m unittest discover -s tests` → 51 OK；把旧 bug 注入临时桩文件反向验证两条
  都会 fail（不空转） · 未提交
- **2026-11-05 · tools/doc** — 新增文档事实提取器 `tools/doc_facts.py`（stdlib only：
  AST 取 RPC/版本，正则取 NAV/插件能力，subprocess 跑 unittest 取测试数）：
  RPC 66（20 组）· NAV 8 · 测试 51 · 版本 0.1.0 · 插件能力 17 · 前端 LOC 5015；
  单锚点失败只进 `errors` 不中断，`check()` 暂留空实现等 docs 侧规则 ·
  `tools/doc_facts.py`（未改 `gen_internal_doc.py` / `gen_dev_doc.py`） ·
  `python tools/doc_facts.py` exit 0 · 未提交
- **2026-11-05 · fix/launch-chain** — Lead 接替并验收被中断的改动：
  bridge 启动调用 `uuid=` → `auth_uuid=`；Downloader 新增
  `HTTPStatusDownloadError` 区分可重试状态（408/425/429/5xx），不再向
  `DownloadError` 传非法 `status`；version_service 补 `VeinError` /
  `get_assets_dir` import；FileStorage 拆 `version_path`（查询不建目录）；
  launcher_service 支持 legacy `minecraftArguments` 并用
  `vein_launcher.__version__` 作 launcher_version；game_process 后台
  `_watch_exit` 只发布一次 `GAME_EXITED`；java_detector 把 `1.8.0_x`
  解析成 major=8；domain 版本模型补齐 camelCase alias，实测可解析真实
  1.20.4 JSON 与 Fabric 子版本；bridge 新增 `__veinGameExited` 推送、
  bridge.ts 转发 `vein:gameExited`，启动页据此复位 busy ·
  `python -m unittest discover -s tests` → 51 OK · frontend build OK
- **2026-11-05 · team/dismiss** — 按要求停用全部 8 个伙伴，后续由 Lead
  单独推进；遗留工作区改动逐项复核后保留并提交，临时截图与 `$null` 已清理
