# Vein Launcher 0.1.0

First public build. Windows, portable folder — unzip anywhere and run `VeinLauncher.exe`.
The launcher creates its data root (`VeinLauncher/`) next to the executable on first start.

## What's new

- **First-run setup** — welcome screen, five-step guide (features → account → privacy → ready)
  with offline, Microsoft and LittleSkin sign-in.
- **One-click updates** — Settings → About checks GitHub Releases, downloads the package and
  starts the installer. No manual downloading.
- **Language switch** — English by default; switch to 简体中文 in Settings → Appearance → Language.
- **Version manager (MLC)** — per-instance mods, resource packs, shaders, datapacks, modpacks and
  worlds; enable/disable with one click, delete files or the whole instance, read a world's seed.
- **Download page rework** — full-page install flow with real per-file progress, download monitor
  in the sidebar, level-1 categories and level-2 install pages.
- **Skins** — import a PNG, read the skin from your LittleSkin profile, or browse the public
  LittleSkin library and download a skin into the selected account.
- **Accounts** — offline accounts, Microsoft (device code) and LittleSkin (Yggdrasil) accounts,
  tokens stored per account and refreshed automatically.
- **LittleSkin support** — Yggdrasil login plus authlib-injector injection at launch.

## Known issues

- Microsoft login is implemented end-to-end but Minecraft Services currently rejects
  self-registered Azure applications (`Invalid app registration`). Offline and LittleSkin
  accounts are unaffected. See `aka.ms/AppRegInfo`.
- The world analysis panel currently shows the raw MC2 scan output; a nicer presentation
  (biomes / structures tables) is planned.
- Changing the launcher language translates the main chrome and settings; some page bodies are
  still English-only.

## Requirements

- Windows 10/11 x64
- Java is detected automatically; the launcher can fetch a matching runtime if none is found.

---

# Vein Launcher 0.1.0（中文）

第一个公开版本。Windows 便携版，解压到任意目录运行 `VeinLauncher.exe`。
首次启动会在 exe 同级创建数据目录 `VeinLauncher/`。

## 本次内容

- **首次启动引导**：欢迎页 + 五步向导（功能介绍 → 账号 → 隐私 → 完成），支持离线、微软、LittleSkin 登录
- **一键更新**：设置 → 关于 里检查 GitHub Release，下载并启动安装包
- **语言切换**：默认英文，设置 → 外观 → 语言 可切到简体中文
- **实例管理（MLC）**：按版本管理模组、资源包、光影、数据包、整合包和存档；一键启用/禁用，
  可删除文件或整个实例，可读取存档种子
- **下载页重做**：整页安装流程、逐文件真实进度、侧边栏下载监控、一级分类 + 二级安装页
- **皮肤**：导入 PNG、读取 LittleSkin 角色皮肤、浏览公开皮肤库并下载到选中账号
- **账号**：离线 / 微软（设备码）/ LittleSkin（Yggdrasil），令牌按账号隔离并自动续期
- **LittleSkin**：Yggdrasil 登录 + 启动时注入 authlib-injector

## 已知问题

- 微软登录链路已完成，但 Minecraft 服务端目前拒绝自建 Azure 应用（`Invalid app registration`），
  离线账号与 LittleSkin 账号不受影响
- 世界分析面板暂以原始 MC2 扫描结果展示，后续会做群系/结构表格
- 切换语言只覆盖主导航与设置，部分页面内容仍为英文

## 运行要求

- Windows 10/11 x64
- 自动探测 Java；找不到时会尝试下载匹配的运行时
