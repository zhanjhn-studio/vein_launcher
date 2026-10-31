# Vein Launcher v0.5.0 更新日志

- **版本**：0.5.0（上一版 `0.1.0-alpha`）
- **日期**：2026-11-01
- **上游基线**：`zhanjhn-studio/vein_launcher` `main@a177ebc`（feat(ui): 默认浅色主题 + PCL2 风蓝绿配色 (v2.2)）
- **界面栈**：Python 3.12 + PySide6 6.12 (QtWebEngine) + React 18 + TypeScript（esbuild 打包）

---

## 一、新增功能

### 1. 简洁模式（Compact mode）

侧边栏默认收起，左边缘留一个**半透明玻璃质感的圆角把手**，点击滑出/收回侧栏。

| 项 | 说明 |
|---|---|
| 开关位置 | 设置 → Appearance → Compact mode |
| 收起形态 | `.side` 改为 `position: fixed` + `translateX(-100%)`，主区占满整宽 |
| 展开方式 | 左侧 22×58 px 把手（`border-radius: 0 15px 15px 0`，55% 不透明度，hover 变实），箭头 `>` / `<` 随状态翻转 |
| 自动收起 | 点任意导航项后自动关闭 |
| 持久化 | `config.json` → `ui.compact_mode` |

### 2. 启动页空闲透明（Fade out after idle）

启动页在设定时间内无任何输入后，整个 UI（侧栏 + 顶栏 + 主区）淡出为透明，只留壁纸；任何输入立即恢复。

| 项 | 说明 |
|---|---|
| 开关位置 | 设置 → Appearance → Fade out after idle |
| 默认值 | 60 秒，可填 5–3600；**填 0 关闭** |
| 计时输入 | `mousemove / mousedown / wheel / keydown / touchstart / pointerdown` |
| 生效范围 | 仅启动页（离开页面立即清除状态并停表） |
| 过渡 | `opacity .9s ease`，淡出后 `pointer-events: none` |
| 持久化 | `config.json` → `ui.idle_seconds` |

### 3. 自定义壁纸（Wallpaper）

设置里导入本地图片或视频作为启动页背景。

| 项 | 说明 |
|---|---|
| 支持格式 | 图片 `png / jpg / jpeg / webp / gif / bmp / avif`；视频 `mp4 / webm / mov / m4v` |
| 存储方式 | 导入时**复制**到 `<数据目录>\config\wallpapers\wallpaper.<ext>`，原文件可删除 |
| 渲染 | 图片 → `body` 的 `background-image`（cover 居中）；视频 → 静音循环 `<video>` 层 |
| 作用范围 | 仅启动页；其它页面恢复默认渐变背景 |
| 持久化 | `config.json` → `ui.wallpaper`（绝对路径） |
| 设置页预览 | 缩略图 168×94 + 文件名，可 Remove |

---

## 二、问题修复

### 2.1 命令方块图标显示错乱

`icons/command_block.png` 实际是 **16×64 的四帧竖排贴图**，被 `object-fit: fill` 压进方形按钮后糊成一团。
→ 取第一帧裁成 16×16 重写（`assets\icons\` 与 `dist\icons\` 同步，SHA-256 一致），原图备份为 `work/vein-launcher-backup-20261101/command_block.png`。

### 2.2 启动页之外「几乎所有 UI 完全透明」

三处叠加导致：

1. `prefs.syncDocument()` 无条件给 `<html>` 挂 `data-wall="on"`，壁纸的半透明 token 覆盖了全部页面；
2. `html[data-wall] .card { backdrop-filter: blur(18px) }` 在**无 GPU 的 QtWebEngine** 下合成失败，面板背景直接不画；
3. 壁纸层 `z-index: 0` 盖在内容之上（应为 `-1`）。

→ 壁纸改为仅启动页生效；删除大面积 `backdrop-filter`；`z-index` 修正；面板底色不再跨页变化。

### 2.3 空闲淡出时界面反复闪烁

淡出给 `.main/.side` 加 `pointer-events: none`，浏览器会把一次合成 `mousemove` 派发给下层元素，被当成用户操作 → 立刻恢复 → 再次淡出，形成自激。
→ `mousemove` 只认**坐标真正变化**的；进入透明态 600 ms 内的输入一律忽略。

### 2.4 切回启动页时整窗抽动几下

合成层反复重建所致，逐层拆掉：

| 处理 | 原因 |
|---|---|
| 图片壁纸改用 `body` 背景图 | 原来每次进入启动页都新建 `fixed + z-index:-1` 的 `<img>` 图层，触发合成层新建/销毁 |
| 去掉壁纸的 `opacity` 过渡与 `visibility` 切换 | 两者都会让合成层反复回收 |
| 启动页关闭 `.page` 入场动画 | `fade-in`（0→1 + 上移 4px）每次挂载重播，叠上壁纸即整屏跳变 |
| 有壁纸时关闭顶栏 `backdrop-filter` | 1200px 宽模糊在软件渲染下每帧重栅格化 |
| `data-wall` 用 `useLayoutEffect` 同步写入 | 避免先画一帧「无壁纸」再补上 |

---

## 三、同步上游 v2.2

从上游 `main` 逐个文件比对（排除 `node_modules` / `dist` / 换行符差异后仅 4 个文件有实质变化）：

| 文件 | 变化 |
|---|---|
| `presentation/webui/src/theme.ts` | 默认主题 `dark` → **`light`** |
| `presentation/webui/src/styles.css` | PCL2 风蓝绿浅色系（129 增 / 203 删） |
| `presentation/main.py` | 原生标题栏样式收敛（`#1b1f27` 底、按钮 42×28），移除未用导入 |
| `presentation/webui/build.ps1` | 构建脚本微调 |

同步后已用本地 esbuild 重建前端产物。

---

## 四、配置项（`<数据目录>\config\config.json`）

```jsonc
{
  "ui": {
    "theme": "dark",              // dark / light
    "language": "zh_CN",
    "window_width": 1200,
    "window_height": 800,
    "compact_mode": false,        // v0.5 新增：简洁模式
    "idle_seconds": 60,           // v0.5 新增：启动页空闲透明秒数，0 = 关闭
    "wallpaper": ""               // v0.5 新增：壁纸绝对路径，空 = 无
  }
}
```

新增 RPC（`presentation/bridge.py`）：`ui.prefs` / `ui.setPrefs` / `ui.importWallpaper`。

---

## 五、已知限制

1. **视频壁纸**仍是独立 `<video>` 图层，切页时的合成开销高于图片；若仍见抽动，建议用图片。
2. 壁纸与空闲透明只作用于**启动页**，其它页面不参与（这是有意为之，避免面板对比度问题）。
3. 上游 `announcements`（`min_version 0.3`）在旧版本上会弹 `Update required` 遮罩；本版已把版本号升到 **0.5.0**，不再触发。
4. 前端产物随包提供（`dist/`），无需 Node 环境；只有改前端源码时才需要 `webui/node_modules` 与 esbuild。

---

## 六、包内文件清单

```
vein_launcher v0.5/
├─ 更新日志.md                    ← 本文件
├─ 启动VeinLauncher.cmd           ← 启动入口（需同目录的 .deps）
├─ 启动说明.md
├─ requirements.txt
└─ vein_launcher/                 ← 完整源码 + 已构建前端（不含 node_modules）
   ├─ __init__.py                 __version__ = 0.5.0
   ├─ application/ common/ domain/ infrastructure/ mlc/ presentation/
   └─ presentation/webui/
      ├─ dist/                    ← app.js / styles.css / icons / vendor（已构建）
      └─ src/                     ← React + TS 源码
```

## 七、运行

```bat
:: 需要 .deps（PySide6 6.12 + aiohttp + pydantic）在启动脚本同级目录
启动VeinLauncher.cmd
```

环境：Windows 10/11，`QTWEBENGINE_DISABLE_SANDBOX=1` 已在启动脚本中设置（受限会话下 QtWebEngine 渲染进程会退出码 18）。
