"""示例级长文（中文）：插件开发与 MLC 的完整可运行示例。"""

EXTRA2 = {
"plugins/api.html": """
<h2>示例 1：最小可用插件（通知 + 日志）</h2>
<p>目的：确认插件能被加载、能调用能力。只需要 <code>ui.notify</code> 权限。</p>
<pre><code>// package.json
{
  "name": "vein-plugin-hello",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": { "displayName": "Hello", "permissions": ["ui.notify"] }
}</code></pre>
<pre><code>// index.js
export async function activate(vein) {
  vein.log("hello plugin activated");
  await vein.ui.notify("Hello", "插件已启动");
}

export async function deactivate() {
  // 进程结束前调用；做收尾即可
}</code></pre>
<p>验证：插件页启用后右下角出现通知，<code>log/plugin-*.log</code> 出现 <code>hello plugin activated</code>。</p>

<h2>示例 2：实例与运行状态面板</h2>
<p>需要 <code>app.info</code>、<code>versions.read</code>、<code>game.state</code>、<code>ui.lua</code> 权限。</p>
<pre><code>export async function activate(vein) {
  async function render() {
    const info = await vein.app.info();
    const versions = await vein.versions.list();
    const running = await vein.game.running();

    await vein.ui.render({
      type: "panel",
      title: `Vein ${info.version}`,
      children: [
        { type: "text", value: `数据目录：${info.dataDir}` },
        { type: "table",
          columns: ["实例", "类型"],
          rows: versions.map((v) => [v.id, v.type || "release"]) },
        { type: "table",
          columns: ["进程", "版本", "来源"],
          rows: running.games.length
            ? running.games.map((g) => [String(g.pid), g.version_id, g.source])
            : [["-", "没有运行中的游戏", "-"]] },
        { type: "button", label: "刷新", action: "refresh" },
      ],
    });
  }

  vein.ui.onAction(async (action) => {
    if (action === "refresh") await render();
  });

  await render();
}</code></pre>

<h2>示例 3：订阅 MLC 事件并在进世界时通知</h2>
<p>需要 <code>mlc.state</code> 与 <code>ui.notify</code>。MLC 总开关关闭时不会收到事件。</p>
<pre><code>export async function activate(vein) {
  vein.mlc.on("game.enter", async (player) => {
    await vein.ui.notify("进入世界", `${player?.name ?? "Player"} 已进入存档`);
  });

  vein.mlc.on("player.death", async (player) => {
    await vein.ui.notify("你死了", `坐标 ${player?.x?.toFixed?.(1)}, ${player?.y?.toFixed?.(1)}, ${player?.z?.toFixed?.(1)}`);
  });
}</code></pre>

<h2>示例 4：把指令发进游戏</h2>
<p>需要 <code>game.command</code>（受 MLC 总开关限制）。适合做「一键白天 / 一键回城」。</p>
<pre><code>export async function activate(vein) {
  await vein.ui.render({
    type: "panel",
    title: "快捷指令",
    children: [
      { type: "button", label: "设为白天", action: "day" },
      { type: "button", label: "清空天气", action: "clear" },
      { type: "button", label: "保存坐标", action: "save" },
    ],
  });

  vein.ui.onAction(async (action) => {
    if (action === "day") await vein.game.command("/time set day");
    if (action === "clear") await vein.game.command("/weather clear");
    if (action === "save") {
      const st = await vein.mlc.state();
      await vein.file.writeText("pos.txt", JSON.stringify(st.player ?? {}, null, 2));
      await vein.ui.notify("已保存", "坐标写入插件沙箱 pos.txt");
    }
  });
}</code></pre>

<h2>示例 5：带配置的插件</h2>
<p>需要 <code>config.read</code>、<code>config.write</code>、<code>ui.notify</code>。</p>
<pre><code>const DEFAULTS = { welcome: true, keyword: "hello" };

export async function activate(vein) {
  const saved = await vein.config.read().catch(() =&gt; ({}));
  const cfg = { ...DEFAULTS, ...(saved || {}) };
  if (!saved || !Object.keys(saved).length) await vein.config.write(cfg);

  if (cfg.welcome) await vein.ui.notify("配置示例", `关键词：${cfg.keyword}`);
  vein.log(`config: ${JSON.stringify(cfg)}`);
}</code></pre>
""",

"plugins/ui.html": """
<h2>示例 1：带按钮的面板</h2>
<pre><code>export async function activate(vein) {
  await vein.ui.render({
    type: "panel",
    title: "我的面板",
    children: [
      { type: "text", value: "点下面的按钮试试" },
      { type: "row", children: [
        { type: "button", label: "打招呼", action: "hello" },
        { type: "button", label: "刷新状态", action: "refresh" },
      ]},
    ],
  });

  vein.ui.onAction(async (action) =&gt; {
    if (action === "hello") await vein.ui.notify("Hi", "来自插件的问候");
    if (action === "refresh") await vein.ui.notify("状态", JSON.stringify(await vein.mlc.state()));
  });
}</code></pre>

<h2>示例 2：表格 + 徽章的状态页</h2>
<pre><code>export async function activate(vein) {
  const versions = await vein.versions.list();
  const mlc = await vein.mlc.state();

  await vein.ui.render({
    type: "panel",
    title: "实例状态",
    children: [
      { type: "row", children: [
        { type: "badge", value: `${versions.length} 个实例`, tone: "info" },
        { type: "badge", value: mlc.enabled ? "MLC 开" : "MLC 关", tone: mlc.enabled ? "ok" : "warn" },
      ]},
      { type: "divider" },
      { type: "table",
        columns: ["实例", "类型"],
        rows: versions.length ? versions.map((v) =&gt; [v.id, v.type || "release"]) : [["-", "暂无"]] },
    ],
  });
}</code></pre>

<h2>示例 3：Lua 文件 + 动态数据</h2>
<p>Lua 负责结构，数据由 JS 渲染前补齐。适合面板较复杂、想让 UI 与逻辑分离的插件。</p>
<pre><code>-- ui.lua
return ui.panel{
  title = "服务器信息",
  children = {
    ui.text{ value = "实例：" .. (data.versions or "") },
    ui.text{ value = "运行中：" .. (data.running or "0") },
    ui.row{ children = {
      ui.button{ label = "刷新", action = "refresh" },
      ui.button{ label = "打开工具", action = "open-tools" },
    }},
  },
}</code></pre>
<pre><code>export async function activate(vein) {
  vein.globals = { data: {} }; // 演示用，真实插件用模块变量
  await vein.ui.lua("./ui.lua");
  vein.ui.onAction(async (action) =&gt; {
    if (action === "open-tools") await vein.ui.openPage("tools");
  });
}</code></pre>
<div class="callout"><b>注意：</b>Lua 里拿不到 Node 变量，需要的数据应在渲染前写入共享状态或通过 <code>ui.render</code> 的 tree 传。</div>
""",

"plugins/examples.html": """
<h2>完整示例 1：status-panel（官方示例）</h2>
<p>把版本、实例、运行中游戏与 MLC 状态放进一个面板，带刷新按钮与进世界通知。</p>
<pre><code>// package.json
{
  "name": "vein-plugin-status-panel",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "Status panel",
    "activateOnStartup": false,
    "permissions": ["game.state", "versions.read", "mlc.state", "ui.lua", "ui.notify", "app.info"]
  }
}</code></pre>
<pre><code>// index.js（节选）
export async function activate(vein) {
  async function refresh() {
    const [info, versions, running, mlc] = await Promise.all([
      vein.app.info().catch(() =&gt; ({ version: "?", dataDir: "?" })),
      vein.versions.list().catch(() =&gt; []),
      vein.game.running().catch(() =&gt; ({ games: [] })),
      vein.mlc.state().catch(() =&gt; ({ enabled: false })),
    ]);

    await vein.ui.render({
      type: "panel",
      title: "Status",
      children: [
        { type: "badge", value: `v${info.version}`, tone: "info" },
        { type: "badge", value: `${versions.length} instances` },
        { type: "badge", value: `${(running.games || []).length} running` },
        { type: "button", label: "Refresh", action: "refresh" },
      ],
    });
  }

  vein.ui.onAction((a) =&gt; a === "refresh" ? refresh() : undefined);
  vein.mlc.on("game.enter", () =&gt; vein.ui.notify("进入世界", "MLC 检测到游戏已进入世界"));
  await refresh();
}</code></pre>

<h2>完整示例 2：game-log（把游戏日志写入沙箱）</h2>
<pre><code>{
  "name": "vein-plugin-game-log",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": { "displayName": "Game log", "permissions": ["game.state", "file.write", "config.read"] }
}</code></pre>
<pre><code>export async function activate(vein) {
  const cfg = await vein.config.read().catch(() =&gt; ({}));
  const file = cfg.file || "game.log";

  // 通过事件或轮询拿到日志行；示例用轮询状态生成摘要
  setInterval(async () =&gt; {
    const st = await vein.mlc.state().catch(() =&gt; null);
    if (!st?.player) return;
    const line = `[${new Date().toISOString()}] ${st.player.name} @ ${st.player.x.toFixed(1)},${st.player.y.toFixed(1)},${st.player.z.toFixed(1)}\\n`;
    const old = await vein.file.readText(file).catch(() =&gt; "");
    await vein.file.writeText(file, old + line);
  }, 60000);
}</code></pre>

<h2>完整示例 3：lua-ui（Lua 面板 + 动作）</h2>
<pre><code>{
  "name": "vein-plugin-lua-ui",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": { "displayName": "Lua UI", "permissions": ["ui.lua", "ui.notify"] }
}</code></pre>
<pre><code>export async function activate(vein) {
  await vein.ui.lua("./ui.lua");
  vein.ui.onAction(async (action) =&gt; {
    await vein.ui.notify("Lua UI", `你点了 ${action}`);
  });
}</code></pre>
<pre><code>return ui.panel{
  title = "Lua UI",
  children = {
    ui.text{ value = "这是一个由 Lua 描述的面板" },
    ui.row{ children = {
      ui.button{ label = "按钮 A", action = "a" },
      ui.button{ label = "按钮 B", action = "b" },
    }},
  },
}</code></pre>

<h2>运行与验证</h2>
<ol><li>把目录放进 <code>VeinLauncher/plugin/</code>；</li>
<li>插件页启用；</li>
<li><code>log/plugin-*.log</code> 看到 activated；</li>
<li>面板出现在插件页；点按钮看通知。</li></ol>
""",

"plugins/manifest.html": """
<h2>最小清单</h2>
<pre><code>{
  "name": "vein-plugin-min",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": { "permissions": ["ui.notify"] }
}</code></pre>
<h2>完整清单（含展示信息与自动激活）</h2>
<pre><code>{
  "name": "vein-plugin-demo",
  "version": "0.2.0",
  "type": "module",
  "main": "index.js",
  "vein": {
    "displayName": "Demo",
    "activateOnStartup": true,
    "permissions": ["ui.notify", "ui.lua", "config.read", "game.state", "mlc.state"]
  }
}</code></pre>
<h2>校验清单</h2>
<ul><li><code>type</code> 必须是 <code>module</code>；</li>
<li><code>main</code> 文件存在且能被 Node 解析；</li>
<li>权限名与能力表完全一致（大小写敏感）；</li>
<li>目录层级为 <code>plugin/&lt;name&gt;/package.json</code>。</li></ul>
""",

"plugins/permissions.html": """
<h2>按用途组合权限</h2>
<table><thead><tr><th>想做的事</th><th>需要的权限</th></tr></thead><tbody>
<tr><td>只弹通知</td><td><code>ui.notify</code></td></tr>
<tr><td>渲染面板</td><td><code>ui.lua</code></td></tr>
<tr><td>读写自己的配置</td><td><code>config.read</code> + <code>config.write</code></td></tr>
<tr><td>查看实例与运行状态</td><td><code>versions.read</code> + <code>game.state</code></td></tr>
<tr><td>发指令 / 读 MLC 状态</td><td><code>game.command</code> + <code>mlc.state</code></td></tr>
<tr><td>下载文件</td><td><code>download.queue</code></td></tr>
</tbody></table>
<h2>一个真实清单</h2>
<pre><code>"permissions": [
  "game.state", "versions.read", "mlc.state",
  "ui.lua", "ui.notify", "app.info"
]</code></pre>
<h2>被拒绝时怎么排查</h2>
<ol><li>看错误里的权限名；</li>
<li>确认清单里有这一项（不是写在别的地方）；</li>
<li>重载插件让宿重新读取清单；</li>
<li>仍然失败就看 <code>log/plugin-*.log</code> 的栈。</li></ol>
""",

"plugins/debugging.html": """
<h2>示例：给插件加最小日志</h2>
<pre><code>export async function activate(vein) {
  vein.log("activate start");
  try {
    const cfg = await vein.config.read();
    vein.log(`config loaded: ${JSON.stringify(cfg)}`);
  } catch (err) {
    vein.log(`config failed: ${err.message}`);
  }
  vein.log("activate done");
}</code></pre>
<h2>示例：带重试的能力调用</h2>
<pre><code>async function withRetry(fn, times = 3, delay = 500) {
  let last;
  for (let i = 0; i &lt; times; i += 1) {
    try { return await fn(); } catch (err) { last = err; await new Promise((r) =&gt; setTimeout(r, delay)); }
  }
  throw last;
}

// 用法
const st = await withRetry(() =&gt; vein.mlc.state());
</code></pre>
<h2>错误对照</h2>
<table><thead><tr><th>报错</th><th>处理</th></tr></thead><tbody>
<tr><td><code>permission denied: game.state</code></td><td>权限未声明</td></tr>
<tr><td><code>timeout</code></td><td>宿主 30 秒超时；拆异步</td></tr>
<tr><td><code>agent not reachable</code></td><td>MLC 未开或游戏未进世界</td></tr>
<tr><td><code>ENOENT</code></td><td>沙箱内文件不存在，先创建或捕获</td></tr>
</tbody></table>
""",

"mlc/protocol.html": """
<h2>示例 1：Python 客户端（读状态）</h2>
<pre><code>import json, socket

with socket.create_connection(("127.0.0.1", 25566), timeout=5) as sock:
    f = sock.makefile("rwb")
    f.write(b'{"cmd":"state"}\\n'); f.flush()
    state = json.loads(f.readline())
    print(state["inGame"], state.get("player", {}).get("x"))

    f.write(b'{"cmd":"chat","text":"/time set day"}\\n'); f.flush()
    print(json.loads(f.readline()))  # {"ok": true}</code></pre>
<h2>示例 2：PowerShell 一行测</h2>
<pre><code>$c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 25566)
$s = $c.GetStream(); $w = New-Object System.IO.StreamWriter($s)
$r = New-Object System.IO.StreamReader($s)
$w.WriteLine('{"cmd":"ping"}'); $w.Flush(); $r.ReadLine()
$c.Close()</code></pre>
<h2>示例 3：Node（插件里不必自己连，这里演示协议）</h2>
<pre><code>import net from "node:net";
const sock = net.connect(25566, "127.0.0.1");
sock.write(JSON.stringify({ cmd: "state" }) + "\\n");
let buf = "";
sock.on("data", (d) =&gt; {
  buf += d.toString();
  const i = buf.indexOf("\\n");
  if (i &gt;= 0) { console.log(JSON.parse(buf.slice(0, i))); sock.end(); }
});</code></pre>
<div class="callout warn"><b>端口不固定：</b>多实例时会顺延。自己手测前从启动器日志里确认实际 <code>-Dvein.agent.port</code>。</div>
""",

"mlc/events.html": """
<h2>示例 1：前端监听（网页/调试）</h2>
<pre><code>window.addEventListener("vein:mlcEvent", (e) =&gt; {
  const { topic, payload } = e.detail || {};
  console.log(topic, payload);
});</code></pre>
<h2>示例 2：插件里做「进世界播报」</h2>
<pre><code>export async function activate(vein) {
  let lastWorld = null;
  vein.mlc.on("game.enter", async (player) =&gt; {
    if (player?.name === lastWorld) return; // 去抖
    lastWorld = player?.name;
    await vein.ui.notify("进入世界", `玩家：${player?.name ?? "Player"}`);
  });

  vein.mlc.on("game.leave", async () =&gt; {
    lastWorld = null;
    await vein.ui.notify("离开世界", "已回到菜单");
  });
}</code></pre>
<h2>示例 3：死亡坐标记录</h2>
<pre><code>vein.mlc.on("player.death", async (p) =&gt; {
  const line = `${new Date().toISOString()} death @ ${p.x.toFixed(1)}, ${p.y.toFixed(1)}, ${p.z.toFixed(1)}\\n`;
  const old = await vein.file.readText("deaths.log").catch(() =&gt; "");
  await vein.file.writeText("deaths.log", old + line);
});</code></pre>
<h2>事件时序</h2>
<pre><code>进入世界   → game.enter
切换维度   → player.dimension
血量归零   → player.death
退回菜单   → game.leave</code></pre>
""",

"mlc/how-it-works.html": """
<h2>示例：生成 agent</h2>
<pre><code>python tools/build_vanilla_agent.py 1.20.1
# 输出：VeinLauncher/agent/vein-agent-1.20.1.jar</code></pre>
<p>脚本会下载官方 mappings、解析类与字段、渲染 Java 源码并用 javac 编译。换版本时改参数重跑。</p>
<h2>示例：确认注入成功</h2>
<ol><li>启动游戏；</li>
<li>打开 <code>log/launcher-*.log</code>；</li>
<li>搜索 <code>-javaagent</code> 与 <code>-Dvein.agent.port</code>；</li>
<li>在 PowerShell 里 <code>Test-NetConnection 127.0.0.1 -Port &lt;端口&gt;</code>。</li></ol>
<h2>agent 做什么</h2>
<table><thead><tr><th>阶段</th><th>行为</th></tr></thead><tbody>
<tr><td>premain</td><td>读取端口参数，启动本地 TCP 服务</td></tr>
<tr><td>收到 state</td><td>在主线程反射读玩家、坐标、血量、维度</td></tr>
<tr><td>收到 chat</td><td>拿到 <code>ClientPacketListener</code> 调 <code>sendCommand</code></td></tr>
<tr><td>异常</td><td>返回 <code>{"ok":false,"error":...}</code>，不崩溃游戏</td></tr>
</tbody></table>
""",

"mlc/overview.html": """
<h2>示例：一次完整交互</h2>
<pre><code># 启动器侧（等价于 MLC 页点「发送到游戏」）
POST / RPC: mlc.agentChat("/time set day", 0)
  → MlcService 解析端口（最近运行的原版实例）
  → TCP: {"cmd":"chat","text":"/time set day"}
  → agent 反射到 ClientPacketListener.sendCommand
  → 游戏聊天框执行
  ← {"ok":true}</code></pre>
<h2>快速验证状态</h2>
<pre><code>mlc.agentState → {"inGame":true,
  "player":{"name":"Player","x":-1044.9,"y":64.0,"z":-1068.1,
            "health":20.0,"food":20.0,"dimension":"minecraft:overworld"}}</code></pre>
<h2>什么时候不该用 MLC</h2>
<ul><li>实例是 Fabric / Forge：不注入 agent，用热键的键盘桥方案。</li>
<li>只想复制指令：关闭总开关后热键会自动回退复制。</li>
<li>需要读写背包 / 实体：MLC 不提供，别用错工具。</li></ul>
""",
}
