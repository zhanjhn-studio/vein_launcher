# Vein Launcher 0.5.0

面向 Minecraft Java 版的便携启动器。这个版本把「启动游戏」推进到「控制游戏」，并把插件能力补全。

## 亮点

### MLC：不装 mod 控制原版
- 5 KB javaagent + Mojang 官方映射，原版实例启动时自动附加
- 读玩家状态（坐标 / 血量 / 饥饿 / 等级 / 视角 / 维度）
- 执行聊天指令（页面、速查窗、全局热键）
- 事件：进入世界 / 离开世界 / 切换维度 / 死亡
- 多实例自动分配端口（25566 起）
- **总开关默认关闭**：关闭时所有 MLC 能力后端直接拒绝，界面明确提示

### 指令速查（Ctrl+Alt+Q）
- 附魔书风格面板：书本图标、紫色渐变选中、中文说明
- 鼠标点击 / Tab 追加，↑↓ 选择，Enter 发送，Ctrl+Enter 强制发送
- 发送失败弹窗并自动复制到剪贴板
- 打开时不暂停游戏（`pauseOnLostFocus=false`）

### 全局热键（Ctrl+Alt+0..9）
- 优先通过 MLC 直接发进游戏，失败回退复制
- 启动时自动绑定已保存的自定义热键

### 插件系统
- 新增能力：`game.running` / `game.command` / `app.info` / `versions.list`
- MLC 事件转发：`vein.mlc.on('game.enter' | 'game.leave' | 'player.dimension' | 'player.death')`
- 新示例 `status-panel`：一个面板展示版本、实例、运行中游戏、MLC 状态
- 沙箱：独立 Node 进程、权限声明、路径校验、30s 超时

### 界面
- MLC 总开关改为独立一行（状态胶囊 + 胶囊开关），修复错位
- 翻译层修复：状态切换后文案不再卡在旧值
- 禁用按钮统一弱化样式

## 安装 / 运行

- 系统：Windows 10/11 x64
- 解压后运行 `VeinLauncher.exe`，数据目录自动生成在 exe 同级 `VeinLauncher/`
- 游戏 Java 无需手动安装：启动器会检测或自动下载
- 插件功能需要 Node.js 18+
- 不带安装器：删除目录即卸载

## 校验

- 单元测试：51 项通过
- 插件自检：加载 / 能力 / 越权 / 超时 / 卸载 全通过
- 构建：`python tools/build_exe.py --version 0.5.0`

## 已知限制

- MLC agent 目前只对原版（无加载器）实例生效
- Fabric/Forge 实例使用键盘输入桥发送指令（需要游戏窗口在前台）
- 本地 PNG 皮肤需要 Fabric + CustomSkinLoader 实例
