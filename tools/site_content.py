"""官网文档内容（每页独立 HTML 的源数据）。"""

DESC = "Vein Launcher 官方文档：安装、使用、二次开发、插件与 MLC 控制层。"

PAGES = [
    # ---------------- 开始使用
    dict(path="getting-started/install.html", group="开始使用", title="下载与安装",
         subtitle="Windows 10/11 x64，解压即用，不写注册表。",
         tags=["下载", "安装", "Windows"],
         body="""
<p>Vein Launcher 以 onedir 压缩包分发，解压后运行 <code>VeinLauncher.exe</code> 即可。整个数据目录在 exe 同级生成，删除目录即卸载。</p>
<h2>系统要求</h2>
<table><thead><tr><th>项目</th><th>要求</th></tr></thead><tbody>
<tr><td>系统</td><td>Windows 10 / 11 x64</td></tr>
<tr><td>磁盘</td><td>启动器约 500 MB，游戏实例另算</td></tr>
<tr><td>Java</td><td>无需手动安装，启动器会检测或自动下载</td></tr>
<tr><td>Node.js</td><td>只有使用插件功能才需要（18+）</td></tr>
</tbody></table>
<h2>下载</h2>
<p>从 <a href="../download.html">下载页</a> 或 GitHub Releases 获取最新版本：</p>
<pre><code>https://github.com/zhanjhn-studio/vein_launcher/releases/download/v0.5.0/VeinLauncher-0.5.0-win64.zip</code></pre>
<h2>安装步骤</h2>
<ol class="steps"><li><h3>解压</h3><p>把 zip 解压到任意目录，例如 <code>D:\\VeinLauncher</code>，路径不要带中文以外的特殊符号。</p></li>
<li><h3>运行</h3><p>双击 <code>VeinLauncher.exe</code>。首次启动会生成 <code>VeinLauncher/</code> 数据目录。</p></li>
<li><h3>安装游戏版本</h3><p>左侧「下载」→ 选择原版或加载器 → 选中版本安装。下载优先走镜像源，失败自动回退官方源。</p></li></ol>
<div class="callout"><b>没有安装器：</b>项目暂不提供安装程序，避免写注册表与系统目录。升级只需覆盖新版本目录，配置与实例都保留。</div>
"""),

    dict(path="getting-started/first-launch.html", group="开始使用", title="首次启动",
         subtitle="从打开启动器到进入游戏，最短路径。",
         tags=["快速开始", "账号", "启动"],
         body="""
<p>首次启动后，你只需要完成三件事：安装一个版本、选一个账号、点启动。</p>
<h2>1. 安装版本</h2>
<p>「下载」页列出可安装的版本。原版适合纯净玩法；Fabric / Forge / Quilt / NeoForge 适合模组。安装过程会下载客户端 jar、libraries 与资源索引。</p>
<h2>2. 选择账号</h2>
<table><thead><tr><th>类型</th><th>说明</th></tr></thead><tbody>
<tr><td>离线</td><td>填 3–16 位用户名即可，单机可用</td></tr>
<tr><td>微软</td><td>OAuth 设备码登录，正版服务器需要</td></tr>
<tr><td>LittleSkin</td><td>皮肤站账号，登录后自动配置皮肤注入</td></tr>
</tbody></table>
<h2>3. 启动</h2>
<p>回到「启动」页，选择实例，点「启动游戏」。首次运行会自动补全 natives 并检测 Java。</p>
<div class="callout ok"><b>提示：</b>启动失败时先看 <code>VeinLauncher/log/launcher-日期.log</code> 的最后 20 行，绝大多数问题能直接定位。</div>
"""),

    dict(path="getting-started/java.html", group="开始使用", title="Java 运行时",
         subtitle="自动检测、自动下载与手动指定。",
         tags=["Java", "运行时", "自动下载"],
         body="""
<p>启动器会优先使用系统已安装的 Java；没有合适的运行时，会从 Adoptium 下载对应大版本。</p>
<h2>版本匹配</h2>
<table><thead><tr><th>游戏版本</th><th>Java</th></tr></thead><tbody>
<tr><td>1.16.5 及更早</td><td>Java 8</td></tr>
<tr><td>1.17 – 1.20.4</td><td>Java 17</td></tr>
<tr><td>1.20.5+</td><td>Java 21</td></tr>
</tbody></table>
<h2>手动指定</h2>
<p>设置页可以把某个 Java 路径固定给全部实例；实例级配置优先于全局配置。</p>
<pre><code>VeinLauncher/config/config.json
{
  "java": { "path": "C:/Program Files/Java/jdk-17/bin/javaw.exe" }
}</code></pre>
<div class="callout warn"><b>注意：</b>32 位 Java 无法分配超过 1.5 GB 内存，启动器只接受 64 位运行时。</div>
"""),

    dict(path="getting-started/directories.html", group="开始使用", title="数据目录",
         subtitle="配置、日志、实例、插件与缓存都在同一个目录里。",
         tags=["目录", "数据", "备份"],
         body="""
<p>所有运行数据都在 exe 同级 <code>VeinLauncher/</code>，可以整体迁移或备份。</p>
<pre><code>VeinLauncher/
  config/      配置：config.json / accounts.json / tools.json
  log/         日志：launcher / download / mlc / plugin 按天分文件
  minecraft/   实例、资源、库
  plugin/      插件
  downloads/   下载缓存
  agent/       MLC agent jar</code></pre>
<h2>备份与迁移</h2>
<p>直接复制整个 <code>VeinLauncher/</code> 即可。存档在 <code>minecraft/instances/&lt;版本&gt;/saves</code>。</p>
<div class="callout tip"><b>建议：</b>升级前先备份 <code>config/</code>，回滚版本时配置不会丢。</div>
"""),

    # ---------------- 玩家
    dict(path="play/instances.html", group="玩家", title="实例管理",
         subtitle="每个实例是独立的游戏目录，可以有自己的 mods、存档和配置。",
         tags=["实例", "mods", "存档"],
         body="""
<p>实例对应 <code>minecraft/instances/&lt;名称&gt;/</code>，包含 <code>mods</code>、<code>saves</code>、<code>config</code>、<code>resourcepacks</code> 等目录。</p>
<h2>常用操作</h2>
<table><thead><tr><th>操作</th><th>位置</th></tr></thead><tbody>
<tr><td>导入 mod / 光影 / 资源包</td><td>实例页 → 对应分类 → 导入</td></tr>
<tr><td>查看存档</td><td>实例页 → 存档</td></tr>
<tr><td>复制实例</td><td>实例卡片 → 复制（适合纯净/模组两套环境）</td></tr>
<tr><td>删除实例</td><td>实例卡片 → 删除（连同 mods 与 saves，不可恢复）</td></tr>
</tbody></table>
<div class="callout warn"><b>同一实例不要双开：</b>存档只有一个 session，同时写会互相覆盖。需要并行请复制实例。</div>
"""),

    dict(path="play/skins.html", group="玩家", title="皮肤",
         subtitle="LittleSkin 账号开箱即用；本地 PNG 皮肤需要 Fabric + CustomSkinLoader。",
         tags=["皮肤", "LittleSkin", "authlib"],
         body="""
<h2>LittleSkin</h2>
<p>皮肤页登录后直接启动。启动器会自动下载 <code>authlib-injector.jar</code>（约 350 KB），通过 <code>-javaagent</code> 注入原版客户端。</p>
<h2>本地 PNG</h2>
<p>原版不支持本地皮肤文件。使用脚本给实例加皮肤支持：</p>
<pre><code>python tools/install_skin_support.py 1.20.1</code></pre>
<p>它会创建 <code>fabric-1.20.1</code> 实例并安装 CustomSkinLoader，之后启动该实例即可。</p>
<div class="callout"><b>排查：</b>皮肤不显示时先确认实例是原版（LittleSkin）或含 CustomSkinLoader（本地皮肤），再检查日志里的 authlib 注入行。</div>
"""),

    dict(path="play/commands.html", group="玩家", title="指令速查",
         subtitle="Ctrl+Alt+Q 打开附魔书面板，回车直接发进游戏。",
         tags=["指令", "速查", "Ctrl+Alt+Q"],
         body="""
<p>速查窗支持逐级构建指令，也支持中文关键词全局检索。</p>
<table><thead><tr><th>操作</th><th>行为</th></tr></thead><tbody>
<tr><td>鼠标单击候选</td><td>追加到指令（检索模式下填入）</td></tr>
<tr><td>双击候选</td><td>直接发送进游戏</td></tr>
<tr><td>↑ / ↓</td><td>上下选择</td></tr>
<tr><td>Tab / →</td><td>追加高亮候选</td></tr>
<tr><td>Enter</td><td>指令完整时发送；否则先追加</td></tr>
<tr><td>Ctrl+Enter</td><td>强制发送</td></tr>
<tr><td>Esc</td><td>关闭</td></tr>
</tbody></table>
<div class="callout warn"><b>发送失败：</b>会弹窗并自动把指令复制到剪贴板，常见原因是游戏没启动、MLC 总开关关闭或实例不是原版。</div>
"""),

    dict(path="play/hotkeys.html", group="玩家", title="全局热键",
         subtitle="Ctrl+Alt+0..9 直接执行常用指令。",
         tags=["热键", "快捷指令"],
         body="""
<p>在工具箱页把指令绑定到数字槽位后，启动器注册为全局热键。</p>
<h2>触发行为</h2>
<ol><li>优先通过 MLC 直接发进游戏；</li>
<li>MLC 不可用（未开启 / 游戏未启动 / 非原版）时回退为复制到剪贴板；</li>
<li>提示会显示「已发送」或「已复制」。</li></ol>
<h2>冲突处理</h2>
<p>热键被其它程序占用时注册会失败，工具箱页会列出失败的槽位，换一个数字即可。</p>
"""),

    dict(path="play/troubleshooting.html", group="玩家", title="常见故障",
         subtitle="启动失败、下载卡住、皮肤不显示的处理顺序。",
         tags=["排错", "日志"],
         body="""
<table><thead><tr><th>症状</th><th>原因</th><th>处理</th></tr></thead><tbody>
<tr><td>ClassNotFoundException: net.minecraft.client.main.Main</td><td>客户端 jar 不完整</td><td>重新点安装续传，或删除实例重装</td></tr>
<tr><td>窗口无标题栏、无法缩放</td><td>分辨率等于屏幕</td><td>配置里改为 1280×720</td></tr>
<tr><td>启动后立刻退出</td><td>Java 版本不匹配 / 内存不足</td><td>看日志退出码，换 Java 17/21，调内存</td></tr>
<tr><td>下载卡住</td><td>镜像超时</td><td>等待自动回退，或清理 downloads 后重试</td></tr>
</tbody></table>
<div class="callout tip"><b>日志位置：</b><code>VeinLauncher/log/</code>，按 <code>launcher / download / mlc / plugin</code> 分类，按天切分。</div>
"""),

    # ---------------- 开发
    dict(path="develop/architecture.html", group="二次开发", title="分层架构",
         subtitle="五层结构 + 全局事件总线。",
         tags=["架构", "模块"],
         body="""
<pre><code>presentation/   Qt 窗口、bridge、palette、webui（React + dist）
application/    服务编排：版本 / 皮肤 / 实例 / 更新 / 插件 / 游戏登记
domain/         模型、仓储契约、领域规则
infrastructure/ 网络、下载、进程、mc2、插件宿主、MLC agent 构建
common/         事件总线、配置、日志、i18n、工具</code></pre>
<p>跨层通信只通过 <code>common/events/event_bus.py</code>；UI 主动拉取走 RPC，服务端主动通知走 push 通道。</p>
<h2>新增功能的位置</h2>
<table><thead><tr><th>要加的东西</th><th>放哪</th></tr></thead><tbody>
<tr><td>新的外部 API / 下载源</td><td>infrastructure/</td></tr>
<tr><td>业务流程（安装、启动、导入）</td><td>application/services/</td></tr>
<tr><td>页面与交互</td><td>presentation/webui/src/</td></tr>
<tr><td>RPC 方法</td><td>presentation/bridge.py</td></tr>
</tbody></table>
"""),

    dict(path="develop/rpc.html", group="二次开发", title="JSON-RPC 协议",
         subtitle="QWebChannel 上的 JSON-RPC 2.0，方法注册在 bridge.py。",
         tags=["RPC", "bridge", "协议"],
         body="""
<p>前端通过 <code>rpc(method, params)</code> 调用 Python；服务端通过 <code>_run_js</code> 推送事件。</p>
<h2>常用方法</h2>
<table><thead><tr><th>方法</th><th>说明</th></tr></thead><tbody>
<tr><td><code>versions.info</code></td><td>已安装实例列表</td></tr>
<tr><td><code>launch</code></td><td>启动实例</td></tr>
<tr><td><code>game.running</code> / <code>game.kill</code></td><td>运行中游戏与结束进程</td></tr>
<tr><td><code>mlc.state</code> / <code>mlc.setEnabled</code></td><td>MLC 总开关</td></tr>
<tr><td><code>plugins.state</code> / <code>plugins.setEnabled</code></td><td>插件列表与启停</td></tr>
</tbody></table>
<h2>新增一个方法</h2>
<ol class="steps"><li><h3>写处理函数</h3><p><code>async def _your_method(self, arg: str = "") -&gt; dict:</code></p></li>
<li><h3>注册</h3><p><code>self._handlers["your.method"] = self._your_method</code></p></li>
<li><h3>前端调用</h3><p><code>await rpc('your.method', [arg])</code></p></li></ol>
"""),

    dict(path="develop/frontend.html", group="二次开发", title="前端与构建",
         subtitle="React 19 + TypeScript，esbuild 打包到 dist，Qt 直接加载。",
         tags=["前端", "React", "esbuild"],
         body="""
<pre><code>cd vein_launcher/presentation/webui
powershell -ExecutionPolicy Bypass -File build.ps1</code></pre>
<p>构建产物 <code>dist/app.js</code> 需要提交，因为启动器直接加载它，不依赖 Node 构建环境。</p>
<h2>目录</h2>
<table><thead><tr><th>文件</th><th>作用</th></tr></thead><tbody>
<tr><td><code>App.tsx</code></td><td>路由与全局布局</td></tr>
<tr><td><code>pages.tsx</code></td><td>启动 / 下载 / MLC 等页面</td></tr>
<tr><td><code>toolsPage.tsx</code></td><td>工具箱与指令</td></tr>
<tr><td><code>bridge.ts</code></td><td>RPC 封装与推送回调</td></tr>
<tr><td><code>i18n.ts</code> / <code>i18nDom.ts</code></td><td>文案与 DOM 翻译层</td></tr>
</tbody></table>
<div class="callout warn"><b>常见坑：</b>改了 <code>webui/src</code> 忘记重新构建，页面不会有变化。</div>
"""),

    dict(path="develop/testing.html", group="二次开发", title="测试",
         subtitle="单元测试、插件自检、MLC 自检与前端构建检查。",
         tags=["测试", "unittest"],
         body="""
<pre><code>python -m unittest discover -s tests      # 单元测试
python tools/plugin_selftest.py           # 插件宿主全链路
python tools/mlc_selftest.py              # MLC 冒烟
python tools/agent_smoke.py               # 真机 agent 验证</code></pre>
<h2>测试范围</h2>
<table><thead><tr><th>模块</th><th>覆盖</th></tr></thead><tbody>
<tr><td>下载源</td><td>镜像重写、候选排序、回退</td></tr>
<tr><td>版本解析</td><td>继承链合并、libraries 规则</td></tr>
<tr><td>插件</td><td>加载、权限、越权路径、超时、卸载</td></tr>
<tr><td>MLC</td><td>端口分配、状态解析、总开关拦截</td></tr>
</tbody></table>
<div class="callout ok"><b>当前：</b>51 项单元测试全部通过。</div>
"""),

    dict(path="develop/packaging.html", group="二次开发", title="打包发布",
         subtitle="PyInstaller onedir + zip + latest.json。",
         tags=["打包", "PyInstaller", "Release"],
         body="""
<pre><code>python tools/build_exe.py --version 0.5.0</code></pre>
<p>产物：<code>dist_exe/VeinLauncher/</code>（约 495 MB）、<code>VeinLauncher-0.5.0-win64.zip</code>（约 199 MB）与 <code>latest.json</code>。</p>
<h2>打包内容</h2>
<ul><li>webui/dist、assets、插件宿主 runtime、i18n locales</li>
<li>plugins_examples 与随包 agent jar</li>
<li>裁剪 translations / qml / opengl32sw 减小体积</li></ul>
<h2>发布</h2>
<pre><code>gh release upload v0.5.0 dist_exe/VeinLauncher-0.5.0-win64.zip
gh release edit v0.5.0 --draft=false</code></pre>
<div class="callout warn"><b>发布前：</b>核对版本号、资产校验值与 latest.json，再确认更新入口指向新版本。</div>
"""),

    # ---------------- 插件
    dict(path="plugins/overview.html", group="插件开发", title="插件系统",
         subtitle="每个插件跑在独立 Node 进程，权限之外一律拒绝。",
         tags=["插件", "沙箱", "Node"],
         body="""
<p>插件目录：<code>VeinLauncher/plugin/&lt;插件&gt;/</code>，由宿主进程加载。</p>
<h2>加载流程</h2>
<ol class="steps"><li><h3>扫描清单</h3><p>启动时扫描 <code>package.json</code>，只接受带 <code>vein</code> 字段的清单。</p></li>
<li><h3>启动进程</h3><p>宿主用 Node 启动插件，通过 stdin/stdout 的 JSON 行协议通信。</p></li>
<li><h3>能力校验</h3><p>插件调用 <code>vein.xxx()</code> 时先查权限，再走 IPC；Python 侧二次校验与路径沙箱。</p></li>
<li><h3>激活 / 停用</h3><p>调用 <code>activate(vein)</code> / <code>deactivate()</code>，超时默认 30 秒。</p></li></ol>
<div class="callout"><b>运行环境：</b>需要 Node.js 18+，没有 Node 时插件页会提示不可用。</div>
"""),

    dict(path="plugins/manifest.html", group="插件开发", title="清单文件",
         subtitle="package.json 里的 vein 字段决定名称、入口、权限与是否随启动激活。",
         tags=["package.json", "清单"],
         body="""
<pre><code>{
  "name": "vein-plugin-hello",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "Hello",
    "activateOnStartup": false,
    "permissions": ["ui.notify", "config.read", "mlc.state"]
  }
}</code></pre>
<table><thead><tr><th>字段</th><th>说明</th></tr></thead><tbody>
<tr><td><code>main</code></td><td>入口文件，ESM</td></tr>
<tr><td><code>displayName</code></td><td>插件页显示名</td></tr>
<tr><td><code>activateOnStartup</code></td><td>是否随启动器自动激活</td></tr>
<tr><td><code>permissions</code></td><td>能力白名单，缺一不可</td></tr>
</tbody></table>
"""),

    dict(path="plugins/permissions.html", group="插件开发", title="权限",
         subtitle="权限是硬性的，未声明会在 Node 侧直接拦截。",
         tags=["权限", "沙箱"],
         body="""
<table><thead><tr><th>能力</th><th>权限</th><th>说明</th></tr></thead><tbody>
<tr><td>file.readText / listDir</td><td>file.read</td><td>只能读插件沙箱目录</td></tr>
<tr><td>file.writeText</td><td>file.write</td><td>只能写插件沙箱目录</td></tr>
<tr><td>config.read / write</td><td>config.read / config.write</td><td>插件自己的配置</td></tr>
<tr><td>ui.notify / openPage</td><td>ui.notify / ui.open_page</td><td>通知、跳转页面</td></tr>
<tr><td>ui.render</td><td>ui.lua</td><td>渲染声明式 UI</td></tr>
<tr><td>network.http.getJson</td><td>network.http</td><td>受限 HTTP 请求</td></tr>
<tr><td>download.queueTask</td><td>download.queue</td><td>交给启动器下载器</td></tr>
<tr><td>game.launch</td><td>game.launch</td><td>启动实例</td></tr>
<tr><td>mlc.*</td><td>mlc.state / mlc.player / mlc.world / mlc.mod</td><td>受 MLC 总开关控制</td></tr>
</tbody></table>
<div class="callout warn"><b>报错：</b>未授权会抛 <code>permission denied: xxx</code>，把权限名补进清单即可。</div>
"""),

    dict(path="plugins/api.html", group="插件开发", title="能力 API",
         subtitle="vein 对象上的全部同步 / 异步方法。",
         tags=["API", "vein"],
         body="""
<pre><code>vein.log(msg)                       // 写 plugin-*.log
vein.file.readText(path)            // 沙箱内读
vein.file.writeText(path, text)     // 沙箱内写
vein.config.read() / write(obj)
vein.ui.notify(title, message)
vein.ui.render(tree)                // 声明式 UI
vein.ui.openPage(key)
vein.http.getJson(url)
vein.download.queueTask(url, savePath)
vein.game.launch(versionId)
vein.game.running()                 // 运行中的游戏
vein.game.command("/time set day")  // 受 MLC 总开关控制
vein.app.info()                     // 版本 + 数据目录
vein.versions.list()                // 已安装实例
vein.mlc.state() / playerInfo() / worldInfo() / modLoad()
vein.mlc.on(topic, cb)              // 事件订阅</code></pre>
<div class="callout"><b>返回值：</b>除 <code>vein.log</code> 外都是 Promise，失败会 reject 并在插件页记录。</div>
"""),

    dict(path="plugins/ui.html", group="插件开发", title="Lua UI",
         subtitle="Lua 声明式面板，渲染在 Shadow DOM 中，碰不到启动器自身 DOM。",
         tags=["Lua", "UI", "沙箱"],
         body="""
<pre><code>return ui.panel{
  title = "我的面板",
  children = {
    ui.text{ value = "Hello from Lua" },
    ui.row{ children = {
      ui.button{ label = "刷新", action = "refresh" },
      ui.badge{ value = "sandboxed" }
    }},
    ui.table{ columns = { "键", "值" }, rows = { { "状态", "ok" } } }
  }
}</code></pre>
<pre><code>export async function activate(vein) {
  vein.ui.onAction(async (action) =&gt; vein.log(`action: ${action}`));
  await vein.ui.lua("./ui.lua");
}</code></pre>
<p>可用组件：panel / row / text / button / input / table / list / badge / image / divider。</p>
"""),

    dict(path="plugins/examples.html", group="插件开发", title="示例",
         subtitle="从最小骨架到状态面板。",
         tags=["示例", "status-panel"],
         body="""
<table><thead><tr><th>目录</th><th>演示</th></tr></thead><tbody>
<tr><td><code>plugins_examples/template</code></td><td>最小骨架</td></tr>
<tr><td><code>plugins_examples/game-log</code></td><td>订阅日志写沙箱文件</td></tr>
<tr><td><code>plugins_examples/lua-ui</code></td><td>Lua UI + 按钮动作</td></tr>
<tr><td><code>plugins_examples/mlc-panel</code></td><td>读取 MLC 状态</td></tr>
<tr><td><code>plugins_examples/status-panel</code></td><td>版本 / 实例 / 运行中游戏 / MLC 状态面板</td></tr>
</tbody></table>
<p>复制到 <code>VeinLauncher/plugin/</code> 后，在插件页启用即可。</p>
"""),

    dict(path="plugins/debugging.html", group="插件开发", title="调试",
         subtitle="日志、热重载与越权排查。",
         tags=["调试", "日志"],
         body="""
<ul><li>日志：<code>VeinLauncher/log/plugin-YYYY-MM-DD.log</code>，<code>vein.log()</code> 直接写入。</li>
<li>插件页可单独启用 / 禁用 / 重载；禁用会结束进程。</li>
<li>自检：<code>python tools/plugin_selftest.py</code>（加载、能力、越权、超时、卸载）。</li></ul>
<div class="callout warn"><b>超时：</b>单次能力调用默认 30 秒，超时抛错而不是挂住宿主。</div>
"""),

    # ---------------- MLC
    dict(path="mlc/overview.html", group="MLC", title="MLC 概览",
         subtitle="不装 mod，也能让启动器直接控制原版 Minecraft。",
         tags=["MLC", "原版", "javaagent"],
         body="""
<p>MLC 是 Vein 自研的控制层。启动原版实例时附加约 5 KB 的 javaagent，通过 Mojang 官方映射在本地开一个 JSON 端口。</p>
<h2>总开关</h2>
<p>MLC 页顶部有总开关，默认关闭。关闭时所有 MLC 能力后端直接拒绝，界面明确提示不可用。</p>
<table><thead><tr><th>能力</th><th>关闭时</th></tr></thead><tbody>
<tr><td>读存档 / 玩家数据</td><td>拒绝</td></tr>
<tr><td>发送指令</td><td>拒绝；热键回退为复制</td></tr>
<tr><td>事件订阅</td><td>不启动监听</td></tr>
</tbody></table>
"""),

    dict(path="mlc/how-it-works.html", group="MLC", title="工作原理",
         subtitle="agent 生成、注入、连接与状态轮询。",
         tags=["agent", "映射", "TCP"],
         body="""
<pre><code>启动器                                 游戏进程
MlcService  ←── JSON 行协议 ──→  vein-agent.jar (premain)
状态 / 指令                       反射：Minecraft / Player</code></pre>
<p>agent 由 <code>tools/build_vanilla_agent.py</code> 生成：拉官方 client mappings → 解析混淆名 → 渲染 Java 源码 → javac 编译。换版本时重跑脚本。</p>
<h2>启动参数</h2>
<pre><code>-javaagent:&lt;数据目录&gt;/agent/vein-agent-1.20.1.jar
-Dvein.agent.port=25566</code></pre>
"""),

    dict(path="mlc/protocol.html", group="MLC", title="协议",
         subtitle="一行 JSON 一个请求，一行 JSON 一个响应。",
         tags=["协议", "JSON", "state"],
         body="""
<table><thead><tr><th>命令</th><th>请求</th><th>返回</th></tr></thead><tbody>
<tr><td>ping</td><td><code>{"cmd":"ping"}</code></td><td><code>{"ok":true}</code></td></tr>
<tr><td>state</td><td><code>{"cmd":"state"}</code></td><td><code>{"inGame":true,"player":{…}}</code></td></tr>
<tr><td>chat</td><td><code>{"cmd":"chat","text":"/time set day"}</code></td><td><code>{"ok":true}</code></td></tr>
</tbody></table>
<h2>state 字段</h2>
<table><thead><tr><th>字段</th><th>示例</th></tr></thead><tbody>
<tr><td>name / x / y / z</td><td>Player / -1044.9 / 64.0 / -1068.1</td></tr>
<tr><td>health / food / xpLevel</td><td>20.0 / 20.0 / 0</td></tr>
<tr><td>yaw / pitch</td><td>-40.68 / 19.5</td></tr>
<tr><td>dimension</td><td>minecraft:overworld</td></tr>
</tbody></table>
"""),

    dict(path="mlc/events.html", group="MLC", title="事件",
         subtitle="每秒对比状态，变化时发布事件。",
         tags=["事件", "订阅"],
         body="""
<table><thead><tr><th>事件</th><th>触发</th></tr></thead><tbody>
<tr><td><code>mlc.agent.game.enter</code></td><td>进入世界</td></tr>
<tr><td><code>mlc.agent.game.leave</code></td><td>退回菜单 / 退出</td></tr>
<tr><td><code>mlc.agent.player.dimension</code></td><td>切换维度</td></tr>
<tr><td><code>mlc.agent.player.death</code></td><td>血量从 &gt;0 变为 ≤0</td></tr>
</tbody></table>
<p>插件侧订阅：</p>
<pre><code>vein.mlc.on("game.enter", () =&gt; vein.log("entered"));</code></pre>
"""),

    dict(path="mlc/troubleshooting.html", group="MLC", title="MLC 排错",
         subtitle="未连接、发不出指令、端口冲突。",
         tags=["排错", "端口"],
         body="""
<ol><li>确认总开关开启；</li>
<li>确认实例是原版（Fabric/Forge 不附加 agent）；</li>
<li>确认已进入世界（菜单态 <code>inGame:false</code>）；</li>
<li>查看 <code>log/mlc-*.log</code> 与 <code>launcher-*.log</code>。</li></ol>
<h2>端口</h2>
<p>每个实例从 25566 起分配并预留，多实例互不冲突。端口被占用时自动顺延。</p>
"""),

    # ---------------- 参考
    dict(path="reference/config.html", group="参考", title="配置项",
         subtitle="config.json 的主要字段。",
         tags=["配置", "config"],
         body="""
<pre><code>{
  "launch": { "memory_min": 512, "memory_max": 4096 },
  "download": { "source": "auto", "max_concurrent": 8 },
  "ui": { "language": "zh_CN", "theme": "light" }
}</code></pre>
<table><thead><tr><th>字段</th><th>说明</th></tr></thead><tbody>
<tr><td><code>download.source</code></td><td>auto / bmclapi / official</td></tr>
<tr><td><code>launch.memory_max</code></td><td>最大堆内存（MB）</td></tr>
<tr><td><code>ui.language</code></td><td>zh_CN / en_US</td></tr>
</tbody></table>
"""),

    dict(path="reference/faq.html", group="参考", title="FAQ",
         subtitle="按症状找答案。",
         tags=["FAQ", "排错"],
         body="""
<h2>启动与运行</h2>
<h3>报 ClassNotFoundException</h3><p>客户端 jar 不完整，重新点安装续传。</p>
<h3>游戏窗口没有标题栏</h3><p>分辨率等于屏幕分辨率，改配置为 1280×720。</p>
<h2>账号与皮肤</h2>
<h3>皮肤不显示</h3><p>LittleSkin 账号直接启动；本地 PNG 需要 Fabric + CustomSkinLoader。</p>
<h2>指令与热键</h2>
<h3>Ctrl+Alt+Q 打不开</h3><p>热键被占用，到工具箱页改键。</p>
<h3>热键只复制不发送</h3><p>MLC 不可用：确认总开关、原版实例、已进入世界。</p>
<h2>插件</h2>
<h3>插件不加载</h3><p>确认目录含 <code>package.json</code> 与 <code>vein</code> 字段，且安装了 Node 18+。</p>
"""),

    dict(path="reference/glossary.html", group="参考", title="术语表",
         subtitle="项目中反复出现的名词。",
         tags=["术语"],
         body="""
<table><thead><tr><th>术语</th><th>含义</th></tr></thead><tbody>
<tr><td>实例</td><td>独立的游戏目录，含 mods / saves / 配置</td></tr>
<tr><td>MLC</td><td>Minecraft Launcher Control，原版控制层</td></tr>
<tr><td>agent</td><td>随游戏启动的 5 KB javaagent</td></tr>
<tr><td>bridge</td><td>前端与 Python 之间的 RPC 桥</td></tr>
<tr><td>插件宿主</td><td>运行插件的 Node 进程</td></tr>
</tbody></table>
"""),

    dict(path="reference/security.html", group="参考", title="安全与隐私",
         subtitle="数据存在哪里、联网做什么。",
         tags=["安全", "隐私"],
         body="""
<h2>本地数据</h2>
<p>账号令牌、配置、日志都保存在 <code>VeinLauncher/</code>，不会上传。</p>
<h2>网络请求</h2>
<ul><li>版本清单 / 客户端 / 资源：BMCLAPI 镜像或 Mojang 官方源</li>
<li>皮肤：LittleSkin 与 authlib-injector</li>
<li>公告与更新检查：GitHub 与公告站</li>
<li>Java 下载：Adoptium</li></ul>
<div class="callout warn"><b>MLC 端口：</b>agent 只监听 <code>127.0.0.1</code>，没有远程访问，也没有鉴权；只在本机使用。</div>
"""),
]
