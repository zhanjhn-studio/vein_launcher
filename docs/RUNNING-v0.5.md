# Vein Launcher 启动说明（本机源码运行版）

## 一句话结论

不是单纯"缺一件环境"，而是**四个问题叠加**，逐个解决后才能起来：

| # | 问题 | 现象 | 处理 |
|---|------|------|------|
| 1 | 缺 Python 依赖 | `ModuleNotFoundError: PySide6 / aiohttp / pydantic` | 已装到 `.deps\`（PySide6 6.12 + aiohttp 3.14 + pydantic 2.14） |
| 2 | 前端产物 `dist\` 根本没下载到 | 窗口能开，但页面白屏 / `前端未构建`（日志 ERROR） | 已用 esbuild + React 19 重新构建到 `vein_launcher\presentation\webui\dist\` |
| 3 | QtWebEngine 渲染进程崩溃 | 日志 `渲染进程终止 exit_code=18` → `页面加载失败` | 启动时设 `QTWEBENGINE_DISABLE_SANDBOX=1` |
| 4 | 窗口比屏幕高 | 1280×820 的窗口在 1280×720 桌面上，底部按钮点不到 | 已改 `presentation\main.py`：按可用桌面收敛尺寸并居中 |

另外还有一个**上游的远程强制更新弹窗**（见下文第 5 点），点 **Not now** 即可继续使用。

---

## 怎么启动

双击工作区根目录的 **`启动VeinLauncher.cmd`**。

它等价于：

```bat
cd /d "D:\dsh's office"
set PYTHONPATH=D:\dsh's office\.deps;D:\dsh's office
set QTWEBENGINE_DISABLE_SANDBOX=1
"C:\Users\CMAI\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" -m vein_launcher.presentation.main
```

> 也可以手工跑上面三行。**必须在 `D:\dsh's office` 里执行**，因为代码是
> `from vein_launcher.xxx import ...` 的绝对导入；直接 `python vein_launcher\presentation\main.py`
> 会因为 `sys.path` 里没有父目录而 `ModuleNotFoundError`。

### 数据目录

首次启动会在 `D:\dsh's office\VeinLauncher\` 下建：`config\`（设置、公告缓存）、`log\`、
`minecraft\`（instances / libraries / assets）、`downloads\`、`plugin\`、`java\`、`democrat\`。

### 日志

`D:\dsh's office\VeinLauncher\log\`：`launcher-日期.log`、`plugin-*`、`mlc-*`、`download-*`、
`error.log`、`crash.log`。程序**只写文件不写控制台**；想看控制台就把 `.cmd` 里的
`rem set "VEIN_SHOW_CONSOLE=1"` 取消注释。

### 重新走一遍用户协议 / 首次引导

引导是否显示由 `VeinLauncher\config\onboarding.json` 决定（`presentation\bridge.py` 的
`_onboarding_done()` 读它，`app.info` 里 `firstRun = 没账号 且 没有 onboarding.json`）。
文件内容是：

```json
{ "completed": true, "consent": true, "at": 1793468697 }
```

- **重新进入引导**：双击根目录的 `重置引导.cmd`，它会先把 `onboarding.json` 备份成
  `onboarding.json.bak`、删掉原文件，然后启动启动器。也可以手动删掉这个文件再启动。
- **注意**：`firstRun` 还要求**没有已添加的账号**。只要 `accounts` 里有账号，
  即使删了 `onboarding.json` 也不会进引导（`bridge.py:266`）。这时要先在设置里删掉账号。
- **想立刻恢复"已同意"状态**：把 `onboarding.json.bak` 改回 `onboarding.json` 即可。

---

## 每个问题的细节

### 1. Python 依赖装在哪、为什么不是 venv

`.deps\` 是 `pip install --target` 的目录（668 MB，PySide6 的 QtWebEngine 占大头）。
用 `--target` 而不是 venv，是因为本机沙箱环境下 `python -m venv` 的 `ensurepip` 会失败
（临时目录里的 `chmod` 被拒），而 `--target` 不依赖那一步。

装的内容（`requirements.txt` 里代码真正 import 的只有这三类）：

- `PySide6 6.12.0`（含 Essentials / Addons / WebEngine / Pdf）
- `aiohttp 3.14.5`（下载、HTTP、公告）
- `pydantic 2.14.2`（`common\config\settings.py`、`domain\models\*`）

`requests / tqdm / pyinstaller / pytest` 在 requirements 里列了但代码并未 import，没装。

### 2. 前端 dist 是缺的（上游 README 说反了）

README 写 "The built `dist/` is part of the repository"，但仓库里**没有** `presentation/webui/dist/`，
`.gitignore` 把它忽略了。没有 `dist/index.html` 时，`main.py` 只会在日志里写
`前端未构建：...\dist\index.html`，然后加载一个不存在的文件 —— 表现为白屏。

已按 `webui\build.ps1` 的步骤重建：

```
dist\app.js        298 KB（esbuild bundle，React 19 + TS，main.tsx -> app.js）
dist\index.html    dist\styles.css    dist\logo.png    dist\icons\*.png    dist\vendor\layui\*
```

同时在 `webui\` 里补了 `package.json` 和 `node_modules\`（react 19.3.1 / react-dom / esbuild 0.28.2），
以后改了 `src\` 只要在 `webui\` 里执行：

```bat
set npm_config_cache=D:\dsh's office\.npm-cache
"C:\Users\CMAI\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" "D:\New Folder\node_modules\npm\bin\npm-cli.js" run bundle
```

> 注意：npm 默认缓存在 `%LOCALAPPDATA%\npm-cache`，这个路径在本机沙箱下写不进去（`EPERM`），
> 所以必须把 `npm_config_cache` 指到工作区里；安装依赖时还要加 `--ignore-scripts`。

### 3. 渲染进程 exit_code=18

PySide6 自带 Chromium 的沙箱进程在这种受限令牌 / 精简会话里起不来：

```
[CRITICAL] 渲染进程终止：status=AbnormalTerminationStatus exit_code=18
[ERROR   ] 页面加载失败
```

`QTWEBENGINE_DISABLE_SANDBOX=1` 之后日志变成 `页面加载完成` → `前端就绪` → `配置加载成功`，
公告也能正常拉取。这个开关只影响本地 `file://` 界面的进程隔离，页面不加载外部网页。

### 4. 窗口尺寸（我改了一行代码）

`main.py` 原本固定 `resize(1280, 820)` + `setMinimumSize(1080, 680)`，本机桌面是 1280×720，
窗口比屏幕高 100 px，弹窗底部按钮（包括强制更新弹窗的 **Not now**）落在屏幕外，等于"卡住"。
改成按 `QGuiApplication.primaryScreen().availableGeometry()` 收敛尺寸并居中。

- 改动文件：`vein_launcher\presentation\main.py`（只动了 `MainWindow.__init__` 里 6~10 行）
- 原文件备份：`vein_launcher\presentation\main.py.orig`（要还原直接覆盖回去）

### 5. 远程"强制更新"弹窗（上游机制，不是故障）

启动后中间会弹 **Update required**：`min_version 0.0.3`，且有一条 `heavy` 级公告
（"0.0.2 及更早版本存在下载校验缺陷"）。判定逻辑在 `presentation\bridge.py:_announcements_get`：
只要公告里有 `level=heavy`，或当前版本低于 `min_version`，就 `force_update=true`。

弹窗不是死锁——点 **Not now** 就关掉继续用（`App.tsx` 里 `setDismissed(true)`）；
点 **Download update** 会打开 GitHub Releases。

---

## 已改动 / 新增的文件

| 路径 | 说明 |
|------|------|
| `.deps\` | 新增，Python 依赖（PySide6 / aiohttp / pydantic 及其传递依赖） |
| `vein_launcher\presentation\webui\dist\` | 新增，构建好的前端 |
| `vein_launcher\presentation\webui\package.json`、`node_modules\` | 新增，前端构建用 |
| `vein_launcher\presentation\main.py` | 改：窗口尺寸按屏幕收敛 + 标题栏样式 |
| `vein_launcher\presentation\main.py.orig` | 新增，原文件备份 |
| `vein_launcher\presentation\webui\src\styles.css` | 改：新配色 + 打磨层 + 侧栏图标居中 |
| `启动VeinLauncher.cmd` | 新增，启动脚本（纯 ASCII，cmd 用 OEM 代码页读脚本，写中文会解析错乱） |
| `VeinLauncher\` | 运行时生成的数据目录 |

## UI 改动（v3 打磨）

主色保持不变（`#6f97f0`），只补层次与细节。全部是样式层改动，**没有动任何 tsx 结构**。

### `styles.css`

| 位置 | 改了什么 |
|------|----------|
| `:root` / `[data-theme='light']` | 重排配色：更深的中性底（`#101318`），surface 分三级层次；`--text-2/3` 提对比度；`--accent-2` 由紫色改成浅蓝（原来 `#8a7ff0`，悬停时会突然变紫）；新增 `--accent-ink`、`--ring`、`--shadow-lg`、`--sheen` |
| `.side-ico` | 收起态图标按 18px 宽度居中：`margin-left: 5px`（150% 缩放 = 7.5 物理像素），悬停展开时平滑归零 |
| `v3 打磨层`（文件尾部） | 焦点环 `:focus-visible`、面板顶部 1px 高光、主按钮渐变+投影、输入框 ring、页头底部高光、侧栏选中项左侧 3px 指示条、滚动条细化、弹窗 `backdrop-filter: blur(6px)`、Toast/下载条投影、chip/代码块统一底色、`::selection` |
| `@media (max-height: 680px)` | 矮窗口（如 150% 缩放下的 720p 桌面）压紧页头、正文内边距、侧栏条目；`.side-nav` 改为可滚动，避免底部条目被切掉 |
| `.page` | `max-width: min(1180px, 100%)`，窄窗口下不再顶出右侧 |
| `.vl-checkbox` | **修复勾选框压字**：`layui.css` 把 `.layui-form-checkbox>i` 设成 `position:absolute; right:0`，导致勾选标记跑到文字尾部并重叠；这里把 `i` 改回 `position:static`，`.vl-checkbox` 的 flex + `order`（图标在前、文字在后）才真正生效。顺带 `.consent` 里改为顶对齐、文字 `line-height:1.6` 可换行 |

### `main.py`（Qt 标题栏）

- 背景跟随新配色 `#101318`，底边 `#242b36`，顶部一条 30% 透明度的蓝色发丝线
- 标题用 `#vlTitleText`（`#e8ecf4`，字重 600，字距 0.3px），替换原来的内联样式
- 三个窗口按钮：40×26 圆角 7px，悬停 `#202531`，关闭按钮悬停改 `#b8565c`（原来是`#c0504d`），按下态加深

### 重新构建前端

```bat
cd /d "D:\dsh's office\vein_launcher\presentation\webui"
node_modules\.bin\esbuild.cmd src/main.tsx --bundle --outfile=dist/app.js --jsx=automatic --minify
copy /y src\styles.css dist\styles.css
copy /y index.html dist\index.html
```

> 只改 CSS 时不需要重新 bundle JS，拷 `styles.css` 到 `dist\` 就够。

## 已知的上游小瑕疵（不影响使用）

- 关闭窗口时 Python 会打印 `RuntimeWarning: coroutine 'GameProcess.kill' was never awaited`
  （`main.py:295` 把协程当函数调了），只是告警。
- 标题栏左上角没有 logo：`_resources_dir()` 指向仓库根目录，需要把仓库根目录的 `assets\logo.ico`
  放过来才会有图标；目前只用 `webui\src\logo.png`。
- **150% 缩放下的渲染放大**：这台机器的 Qt 把窗口的物理像素当 CSS 像素交给 WebEngine，
  Chromium 又按 `devicePixelRatio=1.5` 再放大一次，结果是界面按 1.5 倍渲染、右侧约 1/3 被裁
  （截图里能看到 "Login"/"Announcements" 列被切掉）。试过 `setZoomFactor(dpr)`、
  `1/dpr`、`--force-device-scale-factor=1`、`QT_SCALE_FACTOR`、`QT_ENABLE_HIGHDPI_SCALING`，
  都没能让 CSS 视口和物理尺寸对齐，属于 Qt+WebEngine 的缩放叠加问题，不是这次样式改动引起的。
  如果要把界面按 1:1 显示，需要单独处理（改窗口尺寸策略或换渲染方式），可以另开一轮。

