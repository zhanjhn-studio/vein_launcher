# Vein Launcher 全量规划（规划基线 v1）

> 本文档是**规划**，不是完成状态清单。标注「未做」的内容下一轮起才开始实现。
> 与代码冲突时，以代码为准，并回来修正本文档。
> 技术栈约束：Python 五层架构不变 → Domain 层不改 → PySide6 WebView 承载 React 界面 → QWebChannel 通信桥 → Node.js 插件宿主。

---

## 0. 一句话目标

一个对标 PCL2 的 Windows Minecraft 启动器：界面第一优先、启动稳定、插件系统是核心差异化能力（NPM 插件 + 双向 RPC + 沙箱权限），MLC 是插件操控游戏的自研控制层。

---

## 1. 不可动摇的约束

| 编号 | 约束 |
|---|---|
| C1 | Common / Domain 层代码保留，不重写领域模型 |
| C2 | 依赖方向：Presentation → Application → Domain ← Infrastructure；跨层只走 event_bus |
| C3 | 界面全部由 React 渲染，Python 不画原生控件（窗口壳除外） |
| C4 | Python ↔ React 只通过 MLC 通信桥，方法名与规格一致 |
| C5 | 插件运行在独立 Node 进程，权限未声明一律拒绝，路径限制在插件目录 |
| C6 | 不擅自新增需求外功能；广场模块只预留不实现 |
| C7 | UI 参考 PCL2 的信息结构，浅色主题，界面优先级最高 |
| C8 | 所有 Qt WebEngine 调用必须回到 UI 线程（用 Signal 队列），禁止跨线程直调 |

---

## 2. 现状矩阵（代码 / 界面 / 验证）

图例：✅ 完成　🟡 部分或未验证　❌ 未做

| 模块 | 代码 | 界面入口 | 验证情况 |
|---|---|---|---|
| HTTP 客户端（重试/超时/代理） | ✅ | — | 实测拉取 921 个版本 |
| Mojang API（清单/版本/assets） | ✅ | — | 实测 1.20.4 |
| 下载器（续传/SHA-1/原子落盘） | ✅ | 下载页进度 | 部分实测 |
| 下载队列（并发/事件） | ✅ | 下载页进度 | 部分实测 |
| Modrinth 客户端 | ✅ | 模组页 | 搜索/安装未端到端验证 |
| CurseForge 客户端 | 🟡 | ❌ | 需 API Key，未接界面 |
| Java 探测 | ✅ | 设置页 | 依赖本机环境 |
| 游戏进程 + 日志转发 | ✅ | ❌ 界面未显示 | 未实机启动 |
| 版本安装（原版） | ✅ | 下载页 | 实测 fabric 依赖原版 |
| Fabric / Quilt | ✅ | 下载页加载器 | Fabric 实测成功 |
| Forge / NeoForge | 🟡 | 下载页加载器 | 安装器路径未实机验证 |
| 整合包 .mrpack | ✅ | 模组页 | 仅解析验证 |
| 离线账号 | ✅ | 账号页 | 可用 |
| 微软账号 | ❌ | ❌ | 未做 |
| 插件宿主（RPC/沙箱） | ✅ | ❌ 无页面 | 曾端到端验证，示例插件已删 |
| MLC 控制层 | 🟡 | — | launch/world.info/subscribe 可用；player/mod 未实现 |
| 日志系统（按天/异常/Qt/JS/心跳） | ✅ | ❌ 无查看入口 | 已验证 |
| 通信桥 10 方法 | ✅ | 各页面 | 已验证主链路 |
| 广场 | ❌ | ❌ | 仅规划（第 9 节） |

---

## 3. 功能规划总表

### F1 版本与加载器
| 子项 | 规划 | 状态 |
|---|---|---|
| 原版自动版本匹配 | 列表按类型分组（正式/快照/远古），自动匹配 Java 主版本 | 列表 ✅ / 分组与 Java 匹配 ❌ |
| Fabric / Quilt | Meta API 安装 profile | ✅ |
| Forge / NeoForge | 官方 installer `--installClient`，产物导入实例目录 | 🟡 待实机 |
| 加载器版本选择 | 允许指定 loader 版本（不只最新） | 🟡 接口支持，界面未暴露 |
| 整合包 | .mrpack：清单 + overrides + 依赖写入 | ✅ 解析 / 🟡 完整安装 |
| 实例隔离 | 每实例独立 mods/config/saves | 🟡 目录已隔离，未做 UI 隔离开关 |

### F2 资源下载
| 子项 | 规划 | 状态 |
|---|---|---|
| Modrinth 搜索/安装 | 模组、整合包、资源包、光影、数据包、服务器插件 | ✅ 接口 / 🟡 依赖解析 ❌ |
| CurseForge | API Key 配置后启用，同一套安装管线 | 🟡 客户端 / ❌ 界面 |
| 服务器插件（Paper 等） | Modrinth `project_type=plugin` + 后续 Hangar 源 | 🟡 类型已通 / ❌ 专用页面 |
| 依赖解析 | 读取 `dependencies` 递归安装前置 | ❌ |
| 光影 / 数据包专用目录 | shaderpacks / datapacks | ✅ 目录 / 🟡 无专用筛选 |

### F3 账号
| 子项 | 规划 | 状态 |
|---|---|---|
| 离线账号 | 增删选 + 持久化 | ✅ |
| 微软登录 | 设备码流程 → MS OAuth → Xbox → Minecraft 令牌链，令牌加密存储、自动刷新 | ❌ |
| 账号头像/皮肤 | 仅显示用户名与类型 | ❌（可选） |

### F4 运行时
| 子项 | 规划 | 状态 |
|---|---|---|
| Java 探测 | 注册表 / JAVA_HOME / PATH / 常见目录 | ✅ |
| 手动指定 Java | 设置页选择路径，按实例记忆 | ❌ |
| 启动命令构建 | classpath、natives、参数替换、内存 | ✅ |
| 进程日志推送 | stdout → event_bus → 前端日志面板 | 🟡 桥已通，面板未接 |
| 下载队列管理 | 并发上限、暂停/继续/重试 | 🟡 并发与进度有，暂停/取消 ❌ |

### F5 插件系统（核心）
| 子项 | 规划 | 状态 |
|---|---|---|
| Node 宿主 + JSON-RPC | stdio 逐行 JSON，双向调用 | ✅ |
| 权限沙箱 | 权限声明 + 路径限制 + 超时 | ✅ |
| 示例插件 | `plugin-template` + 一个可运行示例（非 demo 功能） | ❌（被误删，需重建） |
| 插件管理页 | 列表、状态、启用/禁用、重载、查看日志、打开目录、安装本地插件 | ❌ |
| 插件市场 | NPM 拉取 + 安装 | ❌（P2） |
| 崩溃隔离与重启 | 宿主/插件异常不拖垮主程序 | 🟡 异常隔离有，重启 ❌ |

### F6 广场（仅预留，禁止实现）
- 只保留数据模型与接口签名占位，**本轮及下一轮都不开发**
- 帖子 / 标签 / 点赞 / 热度排序全部不实现

---

## 4. UI 规划（第一优先级）

### 4.1 参考基线
PCL2 页面结构（源码 `Plain Craft Launcher 2/Pages`）：`PageLaunch`（启动）、`PageDownload`（下载）、`PageInstance`（实例）、`PageSetup`（设置）、`PageOther`。

Vein 映射：
| Vein 页面 | 对应 PCL | 说明 |
|---|---|---|
| 启动 | PageLaunchLeft/Right | 版本卡 + 启动按钮 + 右侧最新版本 |
| 下载 | PageDownloadLeft + Install | 版本列表 → 加载器 → 安装 |
| 版本 | PageInstance | 已安装实例卡片 |
| 模组 | —（PCL 为实例内页） | 独立页，Modrinth 搜索 |
| 账号 | PageLogin* | 离线 / 微软 |
| 设置 | PageSetup | 关于、Java、日志入口 |
| 插件（新增） | — | 插件管理（核心能力必须可见） |

### 4.2 设计 token（浅色）
| 项 | 值 |
|---|---|
| 背景 | `#f2f4f8`；卡片 `#ffffff` |
| 边框 | `#e6e9f0`；强调边框 `#d5dbe6` |
| 主色 | `#2d6cdf`；深色 `#1657c8`；浅底 `#eaf1ff` |
| 文字 | 主 `#1d2430`，次 `#58627a`，弱 `#8b94a7` |
| 圆角 | 卡片 16px，按钮 10–14px，标签 6px |
| 阴影 | 卡片 `0 1px 2px rgba(20,30,50,.04)`，主按钮 `0 10px 22px rgba(45,108,223,.28)` |
| 字体 | 微软雅黑 UI；数字/路径用 Consolas |
| 字号 | 标题 22 / 页标题 15 / 正文 14 / 辅助 12 / 标签 10.5 |

### 4.3 页面细节规划

**启动页**
- 版本卡：当前实例名（大号可点切换）、类型标签、实例数
- 主按钮：62px 高渐变「启动游戏」，启动中禁用并显示状态
- 快捷：下载新版本 / 账号管理
- 右栏：最新正式版本（真实拉取）→ 点击跳下载
- 无实例空态：显示「去下载」

**下载页**
- 左：版本列表（搜索、类型标签、已装标记、滚动）
- 右：安装配置（版本、实例 ID、加载器卡片 5 选 1、安装按钮、进度条、安装活动日志）
- 状态：加载中骨架 / 空 / 出错重试 / 安装中 / 完成

**版本页**
- 实例卡片网格：名称、类型、操作（删除、打开目录、设为当前）
- 缺：实例详情（内存、JVM 参数、模组数）—— 规划 P1

**模组页**
- 类型切换（模组/服务器插件/整合包/资源包/光影/数据包）
- 搜索、结果列表、安装到当前实例、已安装列表（规划 P1）

**账号页**
- 离线：列表 + 添加 + 设为当前
- 微软：登录按钮 → 设备码弹窗（显示代码 + 复制 + 打开浏览器）→ 轮询 → 成功

**设置页**
- 关于（版本、数据目录、架构）
- Java：自动探测、手动指定、按实例记忆
- 日志：打开日志目录、查看今日日志（脱敏）
- 主题：浅色（默认）/ 深色（P2）

**插件页（新增）**
- 宿主状态（运行中/停止、Node 版本、PID）
- 插件卡片：名称、版本、权限标签、启用状态
- 操作：启用/禁用、重载、打开数据目录、查看日志、安装本地插件（目录选择）
- 底部：RPC 调用日志（最近 100 条，含权限拒绝记录）

### 4.4 交互与状态规范
- 所有异步按钮：加载态 → 禁用 → 成功 toast / 失败 toast（红）
- 空态必须给下一步动作
- 不出现假数据；无数据就展示空态
- 错误文案：发生了什么 + 建议动作（如「网络不可达，检查代理后重试」）
- 骨架屏：版本列表首次加载
- 键盘：搜索框 Enter 触发；Esc 关闭弹层

### 4.5 延后项（P2，不在近期）
- 桌面悬浮球 / 灵动岛（等主界面定稿后再做）
- 主题切换、多语言
- 窗口圆角/毛玻璃

---

## 5. 通信桥（MLC Protocol）规划

### 5.1 调用约定
```
JS → Python : bridge.call(requestId, JSON.stringify({method, args}))
Python → JS : window.__veinResult(requestId, ok, payload)   // payload 为结果或错误文本
进度推送    : window.__veinProgress(taskId, downloaded, total)
日志推送    : window.__veinLog(line)
通知推送    : window.__veinNotify(title, message)
```
- requestId 自增，前端 Promise 表管理
- 失败返回 `ok=false`，payload 为可读错误信息
- Python 必须回执（成功/失败都要），超时由前端 30s 兜底

### 5.2 固定方法（不得擅自增减）
| 方法 | 参数 | 返回 |
|---|---|---|
| versions.info | — | `[{id, type}]` 已安装 |
| versions.remote | limit | `[{id, type, release_time}]` |
| versions.install | versionId, loader? | 原版：`{files, ok, failed}`；加载器：`{version_id, loader_version}` |
| versions.delete | versionId | `{deleted}` |
| launch | versionId, username | `{pid}` |
| accounts.list | — | `[{id, username, selected, type}]` |
| accounts.add | username, type? | 账号对象；微软：设备码信息（规划） |
| accounts.select | accountId | `{ok}` |
| mods.search | query, type, mcVersion, loader | `[{slug,title,author,downloads,description}]` |
| mods.install | slug, instance, type, loader | `{installed, path}` 或整合包 `{files, ok, failed}` |
| java.detect | — | `[{path, major, version, vendor}]` |

### 5.3 扩展命名空间（规划，暂不实现）
- `plugins.*`：list / enable / disable / reload / logs / install
- `settings.*`：get / set（内存、JVM 参数、日志级别）
- 扩展需同步更新本文档与前端约定版本号

### 5.4 线程与生命周期规范
- 所有 JS 执行通过 `Signal(str)` 回到 UI 线程（当前实现已符合）
- 页面未加载完成前脚本入队，`loadFinished` 后冲刷
- 每次调用记录耗时与异常（DEBUG 级）

---

## 6. 日志规划

| 需求 | 方案 |
|---|---|
| 程序外日志 | `%APPDATA%\VeinLauncher\logs\YYYY-MM-DD.log`（按天一个文件，追加） |
| 错误专档 | `error.log`（ERROR 及以上） |
| 程序内日志 | 下载页「安装活动」显示安装/下载进度；插件页显示 RPC 日志 |
| 级别 | 环境变量 `VEIN_LOG_LEVEL`，默认 INFO，文件始终 DEBUG |
| 采集 | Python 日志、Qt 消息、前端 console、未捕获异常、faulthandler |
| 心跳 | 每秒一次，主线程卡顿 > 3s 记 WARNING |
| 保留 | 30 天，启动时清理 |
| 脱敏 | 路径保留、令牌/密码不落盘（规划微软账号时落实） |

---

## 7. 数据目录规划

```
%APPDATA%\VeinLauncher\
├── config.json
├── instances\<实例ID>\
│   ├── <实例ID>.json        # 版本 JSON
│   ├── <实例ID>.jar         # client jar
│   ├── mods\ resourcepacks\ shaderpacks\ datapacks\ saves\
│   └── natives\
├── libraries\               # 多实例共享
├── assets\                  # indexes + objects
├── plugins\<包名>\          # package.json / index.js / data\
├── logs\
└── cache\
```

---

## 8. 插件系统规划

### 8.1 插件包结构
```
plugins/my-plugin/
├── package.json
├── index.js
└── data/            # 宿主创建，插件专属沙箱
```
`package.json` 约定：
```json
{
  "name": "vein-plugin-xxx",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "显示名",
    "permissions": ["file.read", "ui.notify"],
    "activateOnStartup": true,
    "engines": { "vein": ">=0.1" }
  }
}
```

### 8.2 权限清单
| 权限 | 能力 |
|---|---|
| file.read / file.write | 仅限插件自身目录 |
| download.queue | 加入下载队列 |
| game.launch | 启动游戏 |
| ui.notify | 系统/应用通知 |
| config.read / config.write | 读/写启动器配置 |
| network.http | 宿主代理 HTTP |
| mlc.world | 世界信息与创建 |
| mlc.player | 玩家数据（当前不支持） |
| mlc.mod | 运行时加载模组（当前不支持） |
| mlc.plugin | 搜索已装插件 |

### 8.3 RPC 协议
| 方向 | 方法 |
|---|---|
| Python → Node | host.ping、plugin.load、plugin.unload、event.emit、host.shutdown |
| Node → Python | host.call{pluginId, api, args} |
| 通知 | plugin.log、plugin.error |

### 8.4 安全与稳定性
- 未声明权限 → 拒绝并记审计日志（`logs/plugins.log`）
- 路径越界 → 拒绝（`Path.resolve()` + `relative_to`）
- 单次调用超时 30s，插件激活超时 10s
- 插件异常不影响其它插件与主程序
- 宿主崩溃：主程序降级运行，插件页显示「宿主已停止」+ 重启按钮

### 8.5 示例与模板（下一轮补）
- `plugins_examples/template/`：最小可加载插件
- `plugins_examples/game-log/`：订阅 MLC 日志、写沙箱文件、发通知（证明双向 RPC 与沙箱）
- 命名上不再叫 demo，作为正式示例发布

### 8.6 插件页功能（下一轮）
列表 / 状态 / 权限标签 / 启用禁用 / 重载 / 安装本地插件 / 日志 / 打开目录

---

## 9. MLC（Minecraft Launcher Control）规划

### 9.1 定位
插件操控游戏的自研控制层，替代传统 MCP 角色。链路：
```
Python 宿主 ←→ Node 插件进程 ←→ Minecraft
```

### 9.2 接口与阶段
| 接口 | 能力 | 阶段 |
|---|---|---|
| mlc.launch | 启动游戏，返回 PID | M1 ✅ |
| mlc.world.info | 存档列表 | M1 ✅ |
| mlc.world.create | 创建存档目录 | M1 ✅（世界生成仍需游戏内） |
| mlc.event.subscribe | 订阅 game.log / game.exit / download.progress | M1 ✅ |
| mlc.player.info | 玩家坐标/状态 | M3（需游戏侧 mod） |
| mlc.mod.load | 运行时加载模组 | M3 |
| mlc.plugin.search | 搜索已装插件 | M1 ✅ |

### 9.3 游戏内事件（规划 M3）
- 开发 Fabric 侧小 mod，通过本地管道（named pipe / localhost socket）把按键（如 `local_w`）、坐标、世界变更上报 Python
- 协议：逐行 JSON `{type, payload, ts}`
- 安全：仅本机回环，鉴权 token 由启动参数注入
- 未接通前，`mlc.player.info` / `mlc.mod.load` 明确返回 `{supported:false}`，不伪造数据

---

## 10. 里程碑

### M0 规划（本轮）
- 产出本文档；不改代码

### M1 界面与插件可见化（下一轮）
1. 插件页：宿主状态、插件列表、启用/禁用、日志、安装本地插件
2. 重建示例插件（template + game-log）
3. 游戏日志面板接入启动页或独立抽屉
4. 设置页：手动指定 Java、打开日志目录
5. 前端错误态与骨架屏补全
- 验收：插件页能看到示例插件运行日志；关掉示例插件不崩溃

### M2 账号与资源源
1. 微软设备码登录（含令牌存储/刷新）
2. CurseForge 界面入口（API Key 配置）
3. 服务器插件专用筛选与目录
4. 模组依赖解析（dependencies 递归）
- 验收：微软登录成功后可启动；CurseForge 搜索可用

### M3 加载器与整合包收口
1. Forge/NeoForge 实机验证与失败回滚
2. 加载器版本选择
3. 整合包完整安装（依赖 + overrides + 启动）
- 验收：三个加载器各装一个实例并成功启动

### M4 MLC 游戏侧桥
1. Fabric 侧 mod（本地管道）
2. player.info / mod.load 真实实现
3. 事件总线扩展（输入事件）
- 验收：插件能收到 `local_w` 并读坐标

### M5 打磨与分发
1. 悬浮球/灵动岛（回到桌面形态需求）
2. 深色主题、多语言
3. PyInstaller 打包 + 首次启动引导
4. 日志清理与崩溃收集

---

## 11. 验收标准（通用）

- 启动：冷启动 < 3s（含 WebView）
- 稳定性：连续启动/退出 10 次无未响应、无崩溃
- 日志：每次启动有完整时间线；卡顿有 WARNING
- 界面：所有列表有加载/空/错误三态；所有写操作有成功与失败反馈
- 插件：未声明权限的调用 100% 被拒并留痕；越界路径 100% 被拒
- 数据：安装失败不产生半成品实例（临时目录 + 原子替换）

---

## 12. 风险与既定决策

| 风险 | 应对 |
|---|---|
| 本机无法访问 npm / PyPI CDN | 复用本地 React 包 + esbuild 离线打包（既定） |
| GitHub 间歇不可达 | 推送重试；不阻塞开发 |
| Forge installer 依赖网络与 Java | 失败回滚 + 明确错误文案；允许手动导入 |
| 微软 OAuth 需 Azure client id | 配置项 `msa.client_id`，缺失时提示 |
| Qt WebEngine 跨线程调用 | 强制 Signal 队列（已修复，写入 C8） |
| 悬浮球延后导致需求未闭环 | 已在 M5 排期，不作为当前阻塞 |

---

## 13. 明确不做（本轮及近期）

- 广场：帖子/标签/点赞/热度排序（仅预留）
- 假数据填充界面
- 需求外的统计、社区、皮肤商城等功能
- 桌面悬浮球（延后到 M5）

---

## 14. 下一轮开工顺序

1. 插件页 + 示例插件（用户点名缺失）
2. 日志面板（程序内）
3. 设置页手动 Java / 打开日志目录
4. 错误态与骨架屏
5. 微软登录
