"""文档内容扩充（中文）：在每篇文档后追加更完整的章节。"""

EXTRA = {
"getting-started/install.html": """
<h2>校验下载是否完整</h2>
<p>压缩包与 zip 内的可执行文件都可以独立校验。先比对 GitHub Release 页面公布的 SHA-256，再解压：</p>
<pre><code>certutil -hashfile VeinLauncher-0.5.1-win64.zip SHA256
# 与 Release 页面一致再解压</code></pre>
<p>解压后目录结构应包含 <code>VeinLauncher.exe</code>、<code>_internal/</code>；<code>_internal/agent/</code> 里是 MLC 的 Java agent。</p>
<h2>安装位置怎么选</h2>
<table><thead><tr><th>位置</th><th>适合</th><th>注意</th></tr></thead><tbody>
<tr><td>非系统盘（如 <code>D:\\Games\\VeinLauncher</code>）</td><td>日常使用</td><td>路径尽量短，避免深层目录与特殊符号</td></tr>
<tr><td>桌面 / 下载目录</td><td>临时试用</td><td>移动目录后快捷方式会失效</td></tr>
<tr><td>OneDrive 等同步目录</td><td>不建议</td><td>实例与缓存体积大，同步会拖慢启动</td></tr>
</tbody></table>
<h2>升级与降级</h2>
<ol><li>关闭启动器与所有游戏实例。</li>
<li>把新版本解压到新目录，确认能启动后，再把 <code>VeinLauncher/</code> 数据目录指向旧目录（或直接把旧数据目录复制到新目录旁）。</li>
<li>确认无误后再删除旧程序目录。</li></ol>
<div class="callout warn"><b>不要覆盖正在运行的程序目录：</b>Windows 会锁定 <code>VeinLauncher.exe</code> 与部分 dll，覆盖会失败或留下半新半旧的文件。</div>
<h2>卸载</h2>
<p>退出启动器后删除整个程序目录即可；如果还想清掉实例与缓存，把同级的 <code>VeinLauncher/</code> 一起删除。系统里没有注册表项、没有服务、没有计划任务。</p>
<h2>下载失败怎么办</h2>
<ul><li>网络受限时先在设置里把下载源切成 <code>auto</code> 或 <code>bmclapi</code>，再重试。</li>
<li>包体损坏（哈希不一致）通常是下载中断，重新下载即可，不要解压半个 zip。</li>
<li>杀毒软件误报可执行文件时，把程序目录加入白名单；本项目不包含混淆或自解压壳。</li></ul>
""",

"getting-started/first-launch.html": """
<h2>启动后先看这三处</h2>
<table><thead><tr><th>位置</th><th>应该看到什么</th></tr></thead><tbody>
<tr><td>「启动」页版本卡片</td><td>刚安装的版本，类型标注（release / snapshot / 加载器）</td></tr>
<tr><td>「启动」页账号行</td><td>离线账号名，或 LittleSkin / 微软账号</td></tr>
<tr><td>右侧「公告 / 游戏日志」</td><td>网络正常时会出现最新公告；启动后日志会滚动</td></tr>
</tbody></table>
<h2>第一次启动的数据目录</h2>
<p>首次启动会在 exe 同级生成 <code>VeinLauncher/</code>。此时里面只有配置与日志；安装版本后才会有 <code>minecraft/instances/</code>。日志在 <code>VeinLauncher/log/launcher-YYYY-MM-DD.log</code>，每次启动都会追加。</p>
<h2>账号选择建议</h2>
<ul><li>只玩单机：离线账号足够，名字用 3–16 位字母数字。</li>
<li>要进正版服务器：用微软账号，需要能访问微软登录服务。</li>
<li>想要皮肤：用 LittleSkin 账号；离线账号 + 本地皮肤需要额外安装 CustomSkinLoader 实例。</li></ul>
<div class="callout tip"><b>切换账号不会丢实例：</b>账号只影响用户名与皮肤，实例目录与存档不变。</div>
<h2>启动前的自检</h2>
<ol><li>实例卡片是否高亮选中；</li>
<li>内存设置是否足够（大型整合包建议 4–8 GB）；</li>
<li>Java 是否已匹配（启动时会自动检测/下载）；</li>
<li>如果开了 MLC 总开关，确认游戏不是 Fabric/Forge 实例。</li></ol>
""",

"getting-started/java.html": """
<h2>启动器如何选择 Java</h2>
<ol class="steps"><li><h3>读版本 JSON</h3><p>从 <code>javaVersion.majorVersion</code> 得到需要的大版本（8 / 17 / 21）。</p></li>
<li><h3>查本机</h3><p>扫描已记录的 Java 路径、注册表与常见安装目录，优先选择 64 位运行时。</p></li>
<li><h3>缺则下载</h3><p>从 Adoptium 下载对应大版本的 Temurin JRE，解压到数据目录并记录路径。</p></li>
<li><h3>启动</h3><p>用选中的 <code>javaw.exe</code> 拼启动命令；失败时日志会写出实际使用的路径。</p></li></ol>
<h2>内存怎么设</h2>
<table><thead><tr><th>场景</th><th>建议 Xmx</th></tr></thead><tbody>
<tr><td>原版 / 轻量模组</td><td>2048–4096 MB</td></tr>
<tr><td>中型整合包</td><td>4096–6144 MB</td></tr>
<tr><td>大型整合包</td><td>6144–8192 MB，并留出系统内存</td></tr>
</tbody></table>
<div class="callout warn"><b>不要超过物理内存的 60%：</b>给系统与显存共享留余量，否则会频繁换页反而更卡。</div>
<h2>常见 Java 报错</h2>
<table><thead><tr><th>报错</th><th>原因</th><th>处理</th></tr></thead><tbody>
<tr><td><code>UnsupportedClassVersionError</code></td><td>Java 版本过低</td><td>换 17 / 21</td></tr>
<tr><td><code>Could not reserve enough space</code></td><td>32 位 Java 或 Xmx 过大</td><td>换 64 位，降低 Xmx</td></tr>
<tr><td><code>Invalid maximum heap size</code></td><td>参数写法错误</td><td>只填数字，单位 MB</td></tr>
</tbody></table>
""",

"getting-started/directories.html": """
<h2>每个目录负责什么</h2>
<table><thead><tr><th>目录</th><th>能删吗</th><th>说明</th></tr></thead><tbody>
<tr><td><code>config/</code></td><td>不建议</td><td>账号、启动参数、插件与界面偏好</td></tr>
<tr><td><code>log/</code></td><td>可以</td><td>只用于排错，删掉不影响运行</td></tr>
<tr><td><code>minecraft/instances/</code></td><td>谨慎</td><td>实例、mods、存档都在这里</td></tr>
<tr><td><code>minecraft/libraries|assets</code></td><td>可以</td><td>删后下次启动会重新校验下载</td></tr>
<tr><td><code>downloads/</code></td><td>可以</td><td>缓存；删后重新下载</td></tr>
<tr><td><code>agent/</code></td><td>可以</td><td>MLC agent，缺失时从程序目录复制</td></tr>
</tbody></table>
<h2>备份策略</h2>
<p>存档在 <code>minecraft/instances/&lt;实例&gt;/saves</code>。只想备份存档时复制这个目录即可；想整机迁移就复制整个 <code>VeinLauncher/</code>。配置里有账号令牌，备份文件不要上传到公共网盘。</p>
<h2>多用户 / 多套环境</h2>
<p>复制整个数据目录并改程序目录名，就能得到两套互不影响的环境（例如「纯净」与「整合包」）。启动器按 exe 同级目录查找数据目录，不会写到系统其他位置。</p>
""",

"play/instances.html": """
<h2>实例里有什么</h2>
<pre><code>instances/1.20.1/
  mods/            模组
  config/          模组配置
  saves/           世界存档
  resourcepacks/   资源包
  shaderpacks/     光影
  options.txt      游戏设置
  &lt;版本&gt;.jar       客户端（或共享父版本）</code></pre>
<h2>复制实例的正确姿势</h2>
<ol><li>关闭正在运行的该实例。</li>
<li>在实例卡片选择复制，或手动复制目录并在实例列表里刷新。</li>
<li>复制后改名，避免同名冲突。</li></ol>
<div class="callout warn"><b>不要在线复制：</b>运行中复制会得到写了一半的存档与锁文件。</div>
<h2>导入整合包 / 模组</h2>
<ul><li>单个 mod：把 jar 拖进实例的 <code>mods</code> 目录。</li>
<li>资源包 / 光影：导入到对应分类，启动器会放到正确目录。</li>
<li>整合包（.mrpack 等）：目前只下载文件，安装步骤以包内说明为准。</li></ul>
<h2>删除实例</h2>
<p>删除会连同 <code>mods</code> 与 <code>saves</code> 一起移除且不可恢复。删除前把要保留的存档复制到别处。</p>
""",

"play/skins.html": """
<h2>LittleSkin 完整流程</h2>
<ol class="steps"><li><h3>登录</h3><p>皮肤页输入 LittleSkin 邮箱与密码，或使用已保存账号。</p></li>
<li><h3>选择角色</h3><p>登录后列出皮肤站角色，选择要使用的角色。</p></li>
<li><h3>启动</h3><p>启动器自动准备 authlib-injector，并在 JVM 参数里注入。</p></li>
<li><h3>验证</h3><p>进入游戏后按 F5 查看皮肤；服务器需允许皮肤站认证。</p></li></ol>
<h2>本地皮肤（Fabric + CustomSkinLoader）</h2>
<p>原版不能读取本地皮肤文件。运行脚本创建带皮肤支持的实例：</p>
<pre><code>python tools/install_skin_support.py 1.20.1</code></pre>
<p>脚本会创建 <code>fabric-1.20.1</code> 实例并安装 CustomSkinLoader 15.1，之后启动该实例。</p>
<h2>排错</h2>
<table><thead><tr><th>现象</th><th>检查</th></tr></thead><tbody>
<tr><td>皮肤仍是默认</td><td>账号是否为 LittleSkin；日志里是否有 authlib 注入行</td></tr>
<tr><td>只有离线皮肤</td><td>实例是否是原版；Fabric 实例需装 CustomSkinLoader</td></tr>
<tr><td>登录失败</td><td>皮肤站是否可达、密码是否正确、是否被风控</td></tr>
</tbody></table>
""",

"play/commands.html": """
<h2>常用指令速查</h2>
<table><thead><tr><th>指令</th><th>作用</th></tr></thead><tbody>
<tr><td><code>/time set day</code></td><td>设为白天</td></tr>
<tr><td><code>/weather clear</code></td><td>清除天气</td></tr>
<tr><td><code>/gamemode creative</code></td><td>切换创造模式</td></tr>
<tr><td><code>/give @s minecraft:diamond 64</code></td><td>给自己 64 个钻石</td></tr>
<tr><td><code>/tp @s ~ ~10 ~</code></td><td>向上传送 10 格</td></tr>
<tr><td><code>/gamerule keepInventory true</code></td><td>死亡不掉落</td></tr>
</tbody></table>
<h2>速查窗的两种模式</h2>
<ul><li><strong>构建模式</strong>：前缀能匹配指令树时，逐级追加候选。适合不熟悉语法的指令。</li>
<li><strong>检索模式</strong>：输入中文或物品 ID 关键字，跨整个指令库搜索。</li></ul>
<div class="callout tip"><b>完整指令才能直接发送：</b>还缺参数时按 Enter 会先追加候选；确认完整后按 Enter 或 Ctrl+Enter。</div>
<h2>指令在哪种模式下能生效</h2>
<p>需要作弊权限：单机世界开启「允许作弊」，或服务器 OP。MLC 只是把指令送进聊天框并回车，不绕过权限。</p>
""",

"play/hotkeys.html": """
<h2>绑定流程</h2>
<ol><li>打开「工具箱 → 指令」。</li>
<li>把常用指令填入草稿行，选择要绑定的数字槽位（0–9）。</li>
<li>保存后启动器注册全局热键；重启后会自动绑定已保存的槽位。</li></ol>
<h2>冲突与优先级</h2>
<table><thead><tr><th>情况</th><th>结果</th></tr></thead><tbody>
<tr><td>热键被其他软件注册</td><td>注册失败，工具箱会列出失败槽位</td></tr>
<tr><td>MLC 可用且进入世界</td><td>直接发送进游戏</td></tr>
<tr><td>MLC 不可用</td><td>回退为复制指令到剪贴板</td></tr>
</tbody></table>
<h2>多实例</h2>
<p>热键会发送到最近启动且仍在运行的原版实例。想指定实例，在 MLC 页切换实例后再使用热键。</p>
""",

"play/troubleshooting.html": """
<h2>先收集这三样</h2>
<ol><li>启动器版本号（设置 → 关于）；</li>
<li><code>log/launcher-*.log</code> 最后 30 行；</li>
<li>问题发生的操作步骤（点了哪个按钮、用了哪个实例）。</li></ol>
<h2>日志怎么读</h2>
<table><thead><tr><th>关键字</th><th>含义</th></tr></thead><tbody>
<tr><td><code>退出码</code></td><td>游戏进程退出码，非 0 通常是崩溃</td></tr>
<tr><td><code>缺少 java</code></td><td>没有可用运行时，需要下载或指定</td></tr>
<tr><td><code>jar 不完整</code></td><td>客户端文件缺失或被占用</td></tr>
<tr><td><code>镜像</code> / <code>fallback</code></td><td>下载源回退记录</td></tr>
</tbody></table>
<h2>常见组合问题</h2>
<ul><li>装了模组却启动原版实例：检查实例卡片是否选中了带 Fabric/Forge 的版本。</li>
<li>双开同一实例导致存档损坏：改用复制实例。</li>
<li>系统时间错误导致 HTTPS 校验失败：校准时间。</li>
<li>代理软件拦截下载：在设置里配置代理或关闭系统代理。</li></ul>
<h2>还解决不了</h2>
<p>到 GitHub Issues 反馈，附版本、日志与复现步骤；不要贴账号令牌。</p>
""",

"develop/architecture.html": """
<h2>启动一次游戏的数据流</h2>
<pre><code>React「启动」按钮
  → bridge.launch(version_id, account)
  → LauncherService.launch()
      → VersionService.merged(version_id)   合并继承链
      → JavaManager.ensure(major)           确保运行时
      → 解析 libraries / natives / agent 参数
      → subprocess.Popen(javaw ...)
  → event_bus.publish("game.started")
  → bridge 推送 __veinGameStarted
  → React 更新运行状态</code></pre>
<h2>事件清单（节选）</h2>
<table><thead><tr><th>事件</th><th>发布者</th><th>用途</th></tr></thead><tbody>
<tr><td><code>download.progress</code></td><td>下载服务</td><td>进度条与速度</td></tr>
<tr><td><code>game.log</code></td><td>进程监听</td><td>日志面板</td></tr>
<tr><td><code>game.exited</code></td><td>进程监听</td><td>运行状态回收</td></tr>
<tr><td><code>mlc.agent.*</code></td><td>MLC 轮询</td><td>进世界 / 离开 / 维度 / 死亡</td></tr>
<tr><td><code>plugin.*</code></td><td>插件服务</td><td>插件状态与 UI 树</td></tr>
</tbody></table>
<h2>新增一个服务的检查表</h2>
<ul><li>放在 <code>application/services/</code>，依赖通过构造函数注入；</li>
<li>在 <code>presentation/context.py</code> 中装配，暴露给 bridge；</li>
<li>不直接操作 Qt；通知界面一律发事件；</li>
<li>补单元测试与文档页。</li></ul>
""",

"develop/rpc.html": """
<h2>请求与响应</h2>
<pre><code>// 前端
const info = await rpc&lt;VersionInfo[]&gt;('versions.info', []);

// bridge.py
async def _versions_info(self) -&gt; list[dict]:
    return self._ctx.versions.list_installed()</code></pre>
<h2>错误处理</h2>
<p>后端抛出的异常会被包装成 <code>{ code, message }</code>，前端 <code>rpc()</code> 以 <code>Error</code> 抛出。给用户看的文案不要带堆栈；堆栈写日志。</p>
<table><thead><tr><th>错误来源</th><th>处理</th></tr></thead><tbody>
<tr><td>参数非法</td><td>抛 <code>ValueError</code>，前端 toast</td></tr>
<tr><td>文件/网络失败</td><td>包装成可读消息，写日志</td></tr>
<tr><td>MLC 总开关关闭</td><td>抛 <code>MlcError</code>，界面提示去开启</td></tr>
</tbody></table>
<h2>推送通道</h2>
<table><thead><tr><th>函数</th><th>方向</th><th>用途</th></tr></thead><tbody>
<tr><td><code>__veinResult</code></td><td>后端 → 前端</td><td>RPC 结果</td></tr>
<tr><td><code>__veinProgress</code></td><td>后端 → 前端</td><td>下载与安装进度</td></tr>
<tr><td><code>__veinLog</code></td><td>后端 → 前端</td><td>日志行</td></tr>
<tr><td><code>__veinNotify</code></td><td>后端 → 前端</td><td>通知</td></tr>
<tr><td><code>__veinMlcEvent</code></td><td>后端 → 前端</td><td>MLC 事件</td></tr>
</tbody></table>
""",

"develop/frontend.html": """
<h2>页面与组件</h2>
<table><thead><tr><th>页面</th><th>文件</th></tr></thead><tbody>
<tr><td>启动</td><td><code>launchPage.tsx</code></td></tr>
<tr><td>下载</td><td><code>downloadPage.tsx</code></td></tr>
<tr><td>实例</td><td><code>instancePage.tsx</code></td></tr>
<tr><td>皮肤</td><td><code>skinsPage.tsx</code></td></tr>
<tr><td>插件</td><td><code>pages.tsx</code> / <code>pluginUi.tsx</code></td></tr>
<tr><td>设置</td><td><code>settingsPage.tsx</code></td></tr>
<tr><td>工具箱</td><td><code>toolsPage.tsx</code></td></tr>
</tbody></table>
<h2>主题与自定义</h2>
<p>颜色全部走 <code>styles.css</code> 的 CSS 变量；主色由 <code>accent.ts</code> 覆盖，界面自定义（圆角 / 缩放 / 动效）由 <code>uiCustom.ts</code> 写 <code>data-*</code> 属性。不要在组件里写死颜色。</p>
<h2>翻译层</h2>
<p>源码文案是英文，中文由 <code>i18nDom.ts</code> 在渲染后替换，并带 MutationObserver 处理动态节点。新增界面文案时优先加词典条目，而不是在 JSX 里写中文。</p>
<div class="callout warn"><b>改完必须构建：</b><code>dist/app.js</code> 是 Qt 实际加载的文件，源码改动不构建等于没改。</div>
""",

"develop/testing.html": """
<h2>测试分层</h2>
<table><thead><tr><th>层</th><th>方式</th><th>覆盖</th></tr></thead><tbody>
<tr><td>单元</td><td><code>unittest</code></td><td>下载源、版本解析、路径、插件权限、MLC 协议</td></tr>
<tr><td>集成</td><td><code>tools/plugin_selftest.py</code></td><td>宿主进程、能力调用、越权、超时</td></tr>
<tr><td>冒烟</td><td><code>tools/mlc_selftest.py</code></td><td>agent 端口与状态解析</td></tr>
<tr><td>真机</td><td><code>tools/agent_smoke.py</code></td><td>启动游戏读取真实状态</td></tr>
</tbody></table>
<h2>新增测试的写法</h2>
<pre><code>class MyTest(unittest.TestCase):
    def test_something(self):
        self.assertEqual(foo(), expected)</code></pre>
<p>测试不要依赖网络与真实游戏进程；需要外部资源时用 mock 或临时目录。</p>
<h2>前端检查</h2>
<p>构建通过是最低门槛；改动界面后跑一次 <code>tools/ui_preview.py</code> 生成截图，确认没有布局回归。</p>
""",

"develop/packaging.html": """
<h2>打包内容</h2>
<ul><li><code>webui/dist</code>：前端构建产物</li>
<li><code>assets</code>：logo、图标</li>
<li>插件宿主运行时 <code>node_host.js</code> / <code>lua.js</code></li>
<li><code>i18n/locales</code>、<code>plugins_examples</code></li>
<li><code>agent/*.jar</code>：首次启动复制到数据目录</li></ul>
<h2>体积控制</h2>
<p>PyInstaller 默认会带上大量 Qt 组件；脚本会裁剪 <code>translations / qml / opengl32sw</code>，并排除未用到的模块。当前产物约 495 MB，zip 约 199 MB。</p>
<h2>发布前检查</h2>
<ol><li><code>python -m unittest discover -s tests</code></li>
<li><code>python tools/build_exe.py --version X.Y.Z</code></li>
<li>启动一次 exe，确认窗口标题版本正确、能创建数据目录</li>
<li>上传 zip 与 <code>latest.json</code>，确认 SHA-256 与页面一致</li>
<li>更新下载页、更新日志与首页截图</li></ol>
<div class="callout"><b>latest.json：</b>GitHub API 限流时启动器会读这个文件判断更新，别忘了随包上传。</div>
""",

"plugins/overview.html": """
<h2>进程与通信</h2>
<pre><code>启动器 (Python)
  └─ node_host.js (每个插件一个子进程)
       ├─ stdin/stdout JSON lines
       ├─ 能力调用 host.call → Python 能力注册表
       └─ 事件 event.emit ← Python 事件总线</code></pre>
<h2>生命周期</h2>
<table><thead><tr><th>阶段</th><th>行为</th></tr></thead><tbody>
<tr><td>扫描</td><td>读取 <code>package.json</code>，校验 <code>vein</code> 字段</td></tr>
<tr><td>激活</td><td>调用 <code>activate(vein)</code>，超时 30 秒</td></tr>
<tr><td>运行</td><td>响应能力调用与事件</td></tr>
<tr><td>停用</td><td>调用 <code>deactivate()</code> 后结束进程</td></tr>
</tbody></table>
<h2>隔离与限制</h2>
<ul><li>插件崩溃不会带走启动器；宿主会记录并标记失败。</li>
<li>文件能力只能访问插件自己的沙箱目录。</li>
<li>网络与下载走启动器的能力层，便于统一超时与代理。</li></ul>
""",

"plugins/manifest.html": """
<h2>完整字段</h2>
<table><thead><tr><th>字段</th><th>必填</th><th>说明</th></tr></thead><tbody>
<tr><td><code>name</code></td><td>是</td><td>唯一标识，建议 <code>vein-plugin-*</code></td></tr>
<tr><td><code>version</code></td><td>是</td><td>语义化版本</td></tr>
<tr><td><code>type</code></td><td>是</td><td>固定 <code>module</code></td></tr>
<tr><td><code>main</code></td><td>是</td><td>入口文件</td></tr>
<tr><td><code>vein.displayName</code></td><td>否</td><td>界面显示名</td></tr>
<tr><td><code>vein.activateOnStartup</code></td><td>否</td><td>是否随启动器激活</td></tr>
<tr><td><code>vein.permissions</code></td><td>是</td><td>能力白名单</td></tr>
</tbody></table>
<h2>常见校验失败</h2>
<ul><li>缺少 <code>vein</code> 字段：不会被识别为插件。</li>
<li><code>main</code> 指向不存在的文件：激活时报错。</li>
<li>使用 CommonJS <code>require</code>：需要 ESM（<code>import</code> / <code>export</code>）。</li></ul>
""",

"plugins/permissions.html": """
<h2>能力 → 权限对照（完整）</h2>
<table><thead><tr><th>能力</th><th>权限</th><th>范围</th></tr></thead><tbody>
<tr><td><code>file.readText</code> / <code>listDir</code></td><td>file.read</td><td>沙箱目录</td></tr>
<tr><td><code>file.writeText</code></td><td>file.write</td><td>沙箱目录</td></tr>
<tr><td><code>config.read</code> / <code>write</code></td><td>config.read / config.write</td><td>插件配置</td></tr>
<tr><td><code>ui.notify</code> / <code>openPage</code></td><td>ui.notify / ui.open_page</td><td>通知与跳转</td></tr>
<tr><td><code>ui.render</code> / <code>ui.lua</code></td><td>ui.lua</td><td>Shadow DOM 面板</td></tr>
<tr><td><code>http.getJson</code></td><td>network.http</td><td>受限 GET</td></tr>
<tr><td><code>download.queueTask</code></td><td>download.queue</td><td>下载器队列</td></tr>
<tr><td><code>game.launch</code></td><td>game.launch</td><td>启动实例</td></tr>
<tr><td><code>game.running</code> / <code>command</code></td><td>game.state / game.command</td><td>运行状态 / 发送指令</td></tr>
<tr><td><code>app.info</code> / <code>versions.list</code></td><td>app.info / versions.read</td><td>版本与目录</td></tr>
<tr><td><code>mlc.*</code></td><td>mlc.state / mlc.player / mlc.world / mlc.mod</td><td>受 MLC 总开关二次限制</td></tr>
</tbody></table>
<h2>越权时会发生什么</h2>
<p>Node 宿主在发 IPC 之前就拒绝，错误信息为 <code>permission denied: 权限名</code>；Python 侧还会再校验一次。插件页会记录失败原因。</p>
<div class="callout warn"><b>不要试图绕过：</b>扩展能力需要提 PR，而不是在插件里直接调系统 API。</div>
""",

"plugins/api.html": """
<h2>调用示例</h2>
<pre><code>export async function activate(vein) {
  const info = await vein.app.info();
  const versions = await vein.versions.list();
  const running = await vein.game.running();
  const mlc = await vein.mlc.state();

  await vein.ui.render({
    type: "panel",
    title: `Vein ${info.version}`,
    children: [
      { type: "text", value: `${versions.length} instances, ${running.games.length} running` },
      { type: "badge", value: mlc.enabled ? "MLC on" : "MLC off" },
    ],
  });
}</code></pre>
<h2>返回结构</h2>
<table><thead><tr><th>方法</th><th>返回</th></tr></thead><tbody>
<tr><td><code>app.info()</code></td><td><code>{ version, dataDir }</code></td></tr>
<tr><td><code>versions.list()</code></td><td><code>[{ id, type, ... }]</code></td></tr>
<tr><td><code>game.running()</code></td><td><code>{ games: [{ pid, version_id, source }] }</code></td></tr>
<tr><td><code>mlc.state()</code></td><td><code>{ enabled, ... }</code></td></tr>
</tbody></table>
<div class="callout"><b>错误：</b>能力失败会 reject，带可读消息；不要静默吞掉，写进插件日志。</div>
""",

"plugins/ui.html": """
<h2>组件表</h2>
<table><thead><tr><th>组件</th><th>说明</th></tr></thead><tbody>
<tr><td><code>panel</code></td><td>带标题的容器</td></tr>
<tr><td><code>row</code></td><td>横向排列</td></tr>
<tr><td><code>text</code></td><td>纯文本</td></tr>
<tr><td><code>button</code></td><td>触发 <code>ui.onAction(name)</code></td></tr>
<tr><td><code>input</code></td><td>文本输入</td></tr>
<tr><td><code>table</code></td><td>列 + 行</td></tr>
<tr><td><code>list</code></td><td>项目列表</td></tr>
<tr><td><code>badge</code></td><td>状态徽章</td></tr>
<tr><td><code>image</code></td><td>沙箱内图片</td></tr>
<tr><td><code>divider</code></td><td>分隔线</td></tr>
</tbody></table>
<h2>事件回传</h2>
<pre><code>vein.ui.onAction(async (action) =&gt; {
  if (action === "refresh") await render();
  if (action === "open") await vein.ui.openPage("tools");
});</code></pre>
<div class="callout warn"><b>样式隔离：</b>UI 渲染在 closed Shadow DOM，插件 CSS 不会影响启动器，也拿不到启动器的 DOM。</div>
""",

"plugins/examples.html": """
<h2>每个示例教什么</h2>
<table><thead><tr><th>目录</th><th>演示点</th></tr></thead><tbody>
<tr><td><code>template</code></td><td>最小可运行骨架</td></tr>
<tr><td><code>game-log</code></td><td>订阅日志事件、写沙箱文件</td></tr>
<tr><td><code>lua-ui</code></td><td>Lua 面板、按钮动作</td></tr>
<tr><td><code>mlc-panel</code></td><td>读取 MLC 状态并渲染</td></tr>
<tr><td><code>status-panel</code></td><td>版本 / 实例 / 运行中游戏 / MLC 汇总</td></tr>
</tbody></table>
<h2>运行示例</h2>
<ol><li>把示例目录复制到 <code>VeinLauncher/plugin/</code>。</li>
<li>打开插件页，启用该插件。</li>
<li>在日志 <code>log/plugin-*.log</code> 里确认「已激活」。</li></ol>
<h2>自己写第一个插件</h2>
<pre><code>{
  "name": "vein-plugin-first",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": { "displayName": "First", "permissions": ["ui.notify"] }
}</code></pre>
<pre><code>export async function activate(vein) {
  await vein.ui.notify("First", "插件已启动");
}</code></pre>
""",

"plugins/debugging.html": """
<h2>日志与状态</h2>
<table><thead><tr><th>位置</th><th>内容</th></tr></thead><tbody>
<tr><td><code>log/plugin-*.log</code></td><td>宿主与插件输出、能力错误</td></tr>
<tr><td>插件页</td><td>启用状态、版本、失败原因</td></tr>
<tr><td>进程列表</td><td>每个插件一个 node 进程</td></tr>
</tbody></table>
<h2>常见问题</h2>
<ul><li>启用后立刻失败：入口文件语法错误或权限未声明。</li>
<li>能力超时：回调里做了同步阻塞；拆成异步并给宿主留响应。</li>
<li>UI 不显示：<code>ui.render</code> 需要 <code>ui.lua</code> 权限。</li>
<li>插件页看不到：目录层级不对，必须是 <code>plugin/&lt;name&gt;/package.json</code>。</li></ul>
<h2>热重载</h2>
<p>插件页的「重载」会结束进程并重新激活；修改代码后用它，不必重启启动器。</p>
""",

"mlc/overview.html": """
<h2>能读到的状态</h2>
<table><thead><tr><th>字段</th><th>示例</th></tr></thead><tbody>
<tr><td>name</td><td>Player</td></tr>
<tr><td>x / y / z</td><td>-1044.9 / 64.0 / -1068.1</td></tr>
<tr><td>health / food</td><td>20.0 / 20.0</td></tr>
<tr><td>xpLevel</td><td>0</td></tr>
<tr><td>yaw / pitch</td><td>-40.68 / 19.5</td></tr>
<tr><td>dimension</td><td>minecraft:overworld</td></tr>
</tbody></table>
<h2>能做什么 / 不能做什么</h2>
<table><thead><tr><th>能做</th><th>不能做</th></tr></thead><tbody>
<tr><td>读玩家与维度状态</td><td>读写背包 / 实体列表</td></tr>
<tr><td>发送聊天指令</td><td>绕过 OP / 作弊权限</td></tr>
<tr><td>订阅进出世界等事件</td><td>修改游戏内存或文件</td></tr>
</tbody></table>
<h2>总开关</h2>
<p>默认关闭。关闭时 MLC 页的发送、读取、事件都会被后端拒绝，热键回退为复制。开启后只对原版实例生效。</p>
""",

"mlc/how-it-works.html": """
<h2>agent 如何生成</h2>
<ol class="steps"><li><h3>取映射</h3><p>下载 Mojang 官方 client mappings（对应游戏版本）。</p></li>
<li><h3>解析混淆名</h3><p>找到 <code>Minecraft</code>、<code>Player</code>、<code>ClientPacketListener</code> 等类与字段。</p></li>
<li><h3>渲染源码</h3><p>把混淆名填进 Java 模板，<code>premain</code> 里起本地 TCP 服务。</p></li>
<li><h3>编译</h3><p>javac 编译并打成约 5 KB 的 jar，放到 <code>agent/vein-agent-&lt;版本&gt;.jar</code>。</p></li></ol>
<h2>注入参数</h2>
<pre><code>-javaagent:&lt;数据目录&gt;/agent/vein-agent-1.20.1.jar
-Dvein.agent.port=25566</code></pre>
<p>启动器只对非加载器实例追加这两个参数；端口从 25566 起自动寻找空闲并预留。</p>
<h2>连接与轮询</h2>
<p>agent 在游戏主线程外接受连接，反射调用需要主线程的操作时切回主线程。启动器每秒查询一次 <code>state</code>，与上一帧对比后发事件。</p>
""",

"mlc/protocol.html": """
<h2>请求 / 响应示例</h2>
<pre><code>→ {"cmd":"state"}
← {"inGame":true,"player":{"name":"Player","x":-1044.99,"y":64.0,
    "z":-1068.19,"health":20.0,"food":20.0,"xpLevel":0,
    "yaw":-40.68,"pitch":19.5,"dimension":"minecraft:overworld"}}</code></pre>
<pre><code>→ {"cmd":"chat","text":"/time set day"}
← {"ok":true}</code></pre>
<h2>自己手测</h2>
<pre><code>$c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 25566)
$s = $c.GetStream(); $w = New-Object System.IO.StreamWriter($s)
$w.WriteLine('{"cmd":"state"}'); $w.Flush()
(New-Object System.IO.StreamReader($s)).ReadLine()
$c.Close()</code></pre>
<h2>注意</h2>
<ul><li>一行一个 JSON，不要发多行。</li>
<li>未进世界时 <code>inGame:false</code>，指令会失败。</li>
<li>端口只监听本机，没有鉴权，不要转发到公网。</li></ul>
""",

"mlc/events.html": """
<h2>事件与负载</h2>
<table><thead><tr><th>事件</th><th>触发</th><th>负载</th></tr></thead><tbody>
<tr><td><code>mlc.agent.game.enter</code></td><td>进入世界</td><td>player</td></tr>
<tr><td><code>mlc.agent.game.leave</code></td><td>退回菜单 / 退出</td><td>pid</td></tr>
<tr><td><code>mlc.agent.player.dimension</code></td><td>切换维度</td><td>from / to</td></tr>
<tr><td><code>mlc.agent.player.death</code></td><td>血量归零</td><td>player</td></tr>
</tbody></table>
<h2>前端订阅</h2>
<pre><code>on('vein:mlcEvent', (evt) =&gt; {
  if (evt.topic === 'mlc.agent.game.enter') toast('已进入世界');
});</code></pre>
<h2>插件订阅</h2>
<pre><code>vein.mlc.on("player.death", (p) =&gt; vein.ui.notify("死亡", `坐标 ${p.x}, ${p.y}, ${p.z}`));</code></pre>
<div class="callout"><b>去抖：</b>事件来自每秒状态对比，瞬移或快速切维度可能只记录最终状态。</div>
""",

"mlc/troubleshooting.html": """
<h2>症状对照</h2>
<table><thead><tr><th>症状</th><th>可能原因</th><th>处理</th></tr></thead><tbody>
<tr><td>MLC 页显示未连接</td><td>加载器实例 / 未进世界 / 端口未监听</td><td>换原版实例，进世界，看 mlc 日志</td></tr>
<tr><td>指令发送失败</td><td>总开关关闭、作弊未开</td><td>开启总开关；单机允许作弊</td></tr>
<tr><td>状态一直是菜单</td><td>游戏还在标题界面</td><td>进入存档</td></tr>
<tr><td>多实例发错对象</td><td>端口解析到最近实例</td><td>用指定 pid 或先只开一个</td></tr>
</tbody></table>
<h2>日志定位</h2>
<pre><code>log/mlc-2026-11-09.log
# 关注 agent 连接、端口、cmd 与 error 行</code></pre>
<h2>终极排查</h2>
<ol><li>关闭所有游戏实例；</li>
<li>用原版 1.20.1 启动，确认命令行里有 <code>-javaagent</code> 与 <code>-Dvein.agent.port</code>；</li>
<li>进世界后在 PowerShell 里手测 <code>state</code>；</li>
<li>仍失败则提 issue，附启动命令与 mlc 日志。</li></ol>
""",

"reference/config.html": """
<h2>完整字段</h2>
<table><thead><tr><th>字段</th><th>类型</th><th>说明</th></tr></thead><tbody>
<tr><td><code>ui.language</code></td><td>string</td><td><code>zh_CN</code> / <code>en_US</code></td></tr>
<tr><td><code>ui.theme</code></td><td>string</td><td><code>light</code> / <code>dark</code> / <code>clear</code> / <code>system</code></td></tr>
<tr><td><code>ui.accent</code></td><td>string</td><td>自定义主色 <code>#rrggbb</code>，空为默认橙色</td></tr>
<tr><td><code>launch.memory_min</code></td><td>int</td><td>最小堆（MB）</td></tr>
<tr><td><code>launch.memory_max</code></td><td>int</td><td>最大堆（MB）</td></tr>
<tr><td><code>launch.jvm_args</code></td><td>list</td><td>额外 JVM 参数</td></tr>
<tr><td><code>download.source</code></td><td>string</td><td><code>auto</code> / <code>bmclapi</code> / <code>official</code></td></tr>
<tr><td><code>download.max_concurrent</code></td><td>int</td><td>并发下载数</td></tr>
<tr><td><code>mlc.enabled</code></td><td>bool</td><td>MLC 总开关</td></tr>
</tbody></table>
<h2>手动改配置</h2>
<ol><li>退出启动器；</li>
<li>编辑 <code>VeinLauncher/config/config.json</code>；</li>
<li>保存为 UTF-8，重新启动。</li></ol>
<div class="callout warn"><b>先备份：</b>非法 JSON 会让启动器回退默认配置，改前复制一份。</div>
""",

"reference/faq.html": """
<h2>下载与安装</h2>
<h3>压缩包解压后报缺少 dll</h3><p>解压不完整。用系统解压或 7-Zip 重新解压，确认 <code>_internal/</code> 存在。</p>
<h3>能装在 U 盘里吗</h3><p>可以。数据目录跟着 exe 走，但 U 盘读写慢会影响启动与加载。</p>
<h2>游戏与账号</h2>
<h3>正版服务器进不去</h3><p>确认使用微软账号登录且网络能访问验证服务；离线账号只能进离线服。</p>
<h3>换了电脑皮肤还在吗</h3><p>LittleSkin 皮肤跟着账号；本地皮肤文件在实例目录，需要一起复制。</p>
<h2>MLC</h2>
<h3>为什么 MLC 对 Fabric 实例无效</h3><p>agent 依赖官方映射，加载器会改动类结构；当前只在原版实例注入。</p>
<h3>关闭总开关后热键为什么还能用</h3><p>热键会回退为复制到剪贴板，不会发进游戏。</p>
<h2>插件</h2>
<h3>安装插件需要重启吗</h3><p>不需要。放到 <code>plugin/</code> 后在插件页启用即可。</p>
<h3>插件能读我的存档吗</h3><p>不能直接读；文件能力限制在插件自己的沙箱目录。</p>
""",

"reference/glossary.html": """
<h2>更多术语</h2>
<table><thead><tr><th>术语</th><th>含义</th></tr></thead><tbody>
<tr><td>加载器</td><td>Fabric / Forge / Quilt / NeoForge，用于加载 mod</td></tr>
<tr><td>继承链</td><td>加载器版本 JSON 通过 <code>inheritsFrom</code> 指向原版</td></tr>
<tr><td>natives</td><td>平台相关库（dll），解压到实例的 natives 目录</td></tr>
<tr><td>资源索引</td><td>assets 的索引文件，决定游戏资源哈希与路径</td></tr>
<tr><td>authlib-injector</td><td>把皮肤站认证注入原版的 javaagent</td></tr>
<tr><td>MLC agent</td><td>本项目自研的游戏控制 javaagent</td></tr>
<tr><td>能力（capability）</td><td>插件可调用的后端函数，需要权限</td></tr>
</tbody></table>
""",

"reference/security.html": """
<h2>权限模型</h2>
<table><thead><tr><th>主体</th><th>可访问</th></tr></thead><tbody>
<tr><td>启动器前端</td><td>仅 RPC 暴露的方法</td></tr>
<tr><td>插件</td><td>声明过的能力 + 沙箱目录</td></tr>
<tr><td>MLC agent</td><td>本机 127.0.0.1 端口</td></tr>
<tr><td>外部程序</td><td>无法直接调用插件能力</td></tr>
</tbody></table>
<h2>网络请求一览</h2>
<table><thead><tr><th>目标</th><th>用途</th></tr></thead><tbody>
<tr><td>BMCLAPI / Mojang</td><td>版本清单、客户端、资源</td></tr>
<tr><td>LittleSkin</td><td>皮肤站认证与皮肤</td></tr>
<tr><td>GitHub</td><td>更新检查</td></tr>
<tr><td>Adoptium</td><td>Java 运行时下载</td></tr>
</tbody></table>
<h2>漏洞上报</h2>
<p>使用 GitHub 私密漏洞报告，不要在公开 issue 里贴可复现细节。我们会在确认后给出修复版本。</p>
""",
}
