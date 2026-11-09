"""Example-heavy documentation (English): plugins and MLC."""

EXTRA2 = {
"plugins/api.html": """
<h2>Example 1: minimal plugin (notify + log)</h2>
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
  await vein.ui.notify("Hello", "Plugin started");
}
export async function deactivate() {}</code></pre>
<p>Verify: a toast appears and <code>log/plugin-*.log</code> contains the log line.</p>

<h2>Example 2: instances and running games</h2>
<pre><code>export async function activate(vein) {
  async function render() {
    const info = await vein.app.info();
    const versions = await vein.versions.list();
    const running = await vein.game.running();

    await vein.ui.render({
      type: "panel",
      title: `Vein ${info.version}`,
      children: [
        { type: "text", value: info.dataDir },
        { type: "table",
          columns: ["Instance", "Type"],
          rows: versions.map((v) => [v.id, v.type || "release"]) },
        { type: "table",
          columns: ["PID", "Version", "Source"],
          rows: running.games.length
            ? running.games.map((g) => [String(g.pid), g.version_id, g.source])
            : [["-", "no game running", "-"]] },
        { type: "button", label: "Refresh", action: "refresh" },
      ],
    });
  }

  vein.ui.onAction((a) => (a === "refresh" ? render() : undefined));
  await render();
}</code></pre>

<h2>Example 3: MLC event notifications</h2>
<pre><code>export async function activate(vein) {
  vein.mlc.on("game.enter", async (p) => {
    await vein.ui.notify("World entered", `${p?.name ?? "Player"} joined a world`);
  });

  vein.mlc.on("player.death", async (p) => {
    await vein.ui.notify("You died", `${p?.x?.toFixed?.(1)}, ${p?.y?.toFixed?.(1)}, ${p?.z?.toFixed?.(1)}`);
  });
}</code></pre>

<h2>Example 4: send commands</h2>
<pre><code>export async function activate(vein) {
  await vein.ui.render({
    type: "panel",
    title: "Quick commands",
    children: [
      { type: "button", label: "Day", action: "day" },
      { type: "button", label: "Clear weather", action: "clear" },
      { type: "button", label: "Save position", action: "save" },
    ],
  });

  vein.ui.onAction(async (a) => {
    if (a === "day") await vein.game.command("/time set day");
    if (a === "clear") await vein.game.command("/weather clear");
    if (a === "save") {
      const st = await vein.mlc.state();
      await vein.file.writeText("pos.txt", JSON.stringify(st.player ?? {}, null, 2));
      await vein.ui.notify("Saved", "Position written to the sandbox");
    }
  });
}</code></pre>

<h2>Example 5: config-backed plugin</h2>
<pre><code>const DEFAULTS = { welcome: true, keyword: "hello" };

export async function activate(vein) {
  const saved = await vein.config.read().catch(() => ({}));
  const cfg = { ...DEFAULTS, ...(saved || {}) };
  if (!saved || !Object.keys(saved).length) await vein.config.write(cfg);
  if (cfg.welcome) await vein.ui.notify("Config example", `keyword: ${cfg.keyword}`);
}</code></pre>
""",

"plugins/ui.html": """
<h2>Example 1: panel with buttons</h2>
<pre><code>export async function activate(vein) {
  await vein.ui.render({
    type: "panel",
    title: "My panel",
    children: [
      { type: "text", value: "Try the buttons" },
      { type: "row", children: [
        { type: "button", label: "Say hi", action: "hello" },
        { type: "button", label: "Refresh", action: "refresh" },
      ]},
    ],
  });
  vein.ui.onAction(async (a) => {
    if (a === "hello") await vein.ui.notify("Hi", "from the plugin");
    if (a === "refresh") await vein.ui.notify("State", JSON.stringify(await vein.mlc.state()));
  });
}</code></pre>

<h2>Example 2: table + badges</h2>
<pre><code>export async function activate(vein) {
  const versions = await vein.versions.list();
  const mlc = await vein.mlc.state();
  await vein.ui.render({
    type: "panel",
    title: "Instances",
    children: [
      { type: "badge", value: `${versions.length} instances`, tone: "info" },
      { type: "badge", value: mlc.enabled ? "MLC on" : "MLC off", tone: mlc.enabled ? "ok" : "warn" },
      { type: "divider" },
      { type: "table", columns: ["Instance", "Type"],
        rows: versions.map((v) => [v.id, v.type || "release"]) },
    ],
  });
}</code></pre>

<h2>Example 3: Lua file</h2>
<pre><code>-- ui.lua
return ui.panel{
  title = "Lua demo",
  children = {
    ui.text{ value = "Declarative panel" },
    ui.row{ children = {
      ui.button{ label = "A", action = "a" },
      ui.button{ label = "B", action = "b" },
    }},
  },
}</code></pre>
<pre><code>export async function activate(vein) {
  await vein.ui.lua("./ui.lua");
  vein.ui.onAction(async (a) => vein.ui.notify("Lua UI", a));
}</code></pre>
""",

"plugins/examples.html": """
<h2>Full example 1: status-panel</h2>
<pre><code>{
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
<pre><code>export async function activate(vein) {
  async function refresh() {
    const [info, versions, running, mlc] = await Promise.all([
      vein.app.info().catch(() => ({ version: "?", dataDir: "?" })),
      vein.versions.list().catch(() => []),
      vein.game.running().catch(() => ({ games: [] })),
      vein.mlc.state().catch(() => ({ enabled: false })),
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
  vein.ui.onAction((a) => (a === "refresh" ? refresh() : undefined));
  vein.mlc.on("game.enter", () => vein.ui.notify("World", "MLC detected a world"));
  await refresh();
}</code></pre>

<h2>Full example 2: game-log</h2>
<pre><code>export async function activate(vein) {
  setInterval(async () => {
    const st = await vein.mlc.state().catch(() => null);
    if (!st?.player) return;
    const line = `[${new Date().toISOString()}] ${st.player.name} @ ${st.player.x.toFixed(1)},${st.player.y.toFixed(1)},${st.player.z.toFixed(1)}\\n`;
    const old = await vein.file.readText("samples.log").catch(() => "");
    await vein.file.writeText("samples.log", old + line);
  }, 60000);
}</code></pre>

<h2>Full example 3: lua-ui</h2>
<pre><code>export async function activate(vein) {
  await vein.ui.lua("./ui.lua");
  vein.ui.onAction(async (a) => vein.ui.notify("Lua UI", `clicked ${a}`));
}</code></pre>
""",

"plugins/manifest.html": """
<h2>Minimal</h2>
<pre><code>{
  "name": "vein-plugin-min",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "vein": { "permissions": ["ui.notify"] }
}</code></pre>
<h2>Full</h2>
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
<h2>Checklist</h2>
<ul><li><code>type</code> must be <code>module</code>.</li><li><code>main</code> must exist.</li>
<li>Permission names are case-sensitive.</li><li>Folder: <code>plugin/&lt;name&gt;/package.json</code>.</li></ul>
""",

"plugins/permissions.html": """
<h2>Permission sets by goal</h2>
<table><thead><tr><th>Goal</th><th>Permissions</th></tr></thead><tbody>
<tr><td>Notifications only</td><td><code>ui.notify</code></td></tr>
<tr><td>Render a panel</td><td><code>ui.lua</code></td></tr>
<tr><td>Read/write config</td><td><code>config.read</code> + <code>config.write</code></td></tr>
<tr><td>Instance and game state</td><td><code>versions.read</code> + <code>game.state</code></td></tr>
<tr><td>Commands / MLC state</td><td><code>game.command</code> + <code>mlc.state</code></td></tr>
</tbody></table>
<h2>Denied calls</h2>
<ol><li>Read the permission name in the error.</li><li>Add it to the manifest.</li>
<li>Reload the plugin.</li><li>Check <code>log/plugin-*.log</code> if it still fails.</li></ol>
""",

"plugins/debugging.html": """
<h2>Minimal logging</h2>
<pre><code>export async function activate(vein) {
  vein.log("activate start");
  try {
    await vein.config.read();
  } catch (err) {
    vein.log(`config failed: ${err.message}`);
  }
  vein.log("activate done");
}</code></pre>
<h2>Retry helper</h2>
<pre><code>async function withRetry(fn, times = 3, delay = 500) {
  let last;
  for (let i = 0; i &lt; times; i += 1) {
    try { return await fn(); } catch (err) { last = err; await new Promise((r) =&gt; setTimeout(r, delay)); }
  }
  throw last;
}</code></pre>
<table><thead><tr><th>Error</th><th>Fix</th></tr></thead><tbody>
<tr><td><code>permission denied</code></td><td>Add the permission</td></tr>
<tr><td><code>timeout</code></td><td>Keep callbacks async</td></tr>
<tr><td><code>agent not reachable</code></td><td>Enable MLC and enter a world</td></tr>
</tbody></table>
""",

"mlc/protocol.html": """
<h2>Python client</h2>
<pre><code>import json, socket
with socket.create_connection(("127.0.0.1", 25566), timeout=5) as sock:
    f = sock.makefile("rwb")
    f.write(b'{"cmd":"state"}\\n'); f.flush()
    print(json.loads(f.readline()))
    f.write(b'{"cmd":"chat","text":"/time set day"}\\n'); f.flush()
    print(json.loads(f.readline()))</code></pre>
<h2>PowerShell one-liner</h2>
<pre><code>$c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 25566)
$s = $c.GetStream(); $w = New-Object System.IO.StreamWriter($s)
$r = New-Object System.IO.StreamReader($s)
$w.WriteLine('{"cmd":"ping"}'); $w.Flush(); $r.ReadLine()
$c.Close()</code></pre>
<h2>Node client</h2>
<pre><code>import net from "node:net";
const sock = net.connect(25566, "127.0.0.1");
sock.write(JSON.stringify({ cmd: "state" }) + "\\n");
sock.on("data", (d) =&gt; console.log(JSON.parse(d.toString())));</code></pre>
<div class="callout warn"><b>Ports vary:</b> read <code>-Dvein.agent.port</code> from the launcher log first.</div>
""",

"mlc/events.html": """
<h2>Frontend listener</h2>
<pre><code>window.addEventListener("vein:mlcEvent", (e) => {
  console.log(e.detail.topic, e.detail.payload);
});</code></pre>
<h2>World enter watcher (plugin)</h2>
<pre><code>export async function activate(vein) {
  let last = null;
  vein.mlc.on("game.enter", async (p) => {
    if (p?.name === last) return;
    last = p?.name;
    await vein.ui.notify("World entered", p?.name ?? "Player");
  });
  vein.mlc.on("game.leave", async () => {
    last = null;
    await vein.ui.notify("Left world", "back to menu");
  });
}</code></pre>
<h2>Death log</h2>
<pre><code>vein.mlc.on("player.death", async (p) => {
  const line = `${new Date().toISOString()} death @ ${p.x}, ${p.y}, ${p.z}\\n`;
  const old = await vein.file.readText("deaths.log").catch(() => "");
  await vein.file.writeText("deaths.log", old + line);
});</code></pre>
""",

"mlc/how-it-works.html": """
<h2>Generate an agent</h2>
<pre><code>python tools/build_vanilla_agent.py 1.20.1</code></pre>
<p>The script pulls official mappings, resolves class and field names, renders Java source and compiles with javac.</p>
<h2>Verify injection</h2>
<ol><li>Start the game.</li><li>Search <code>log/launcher-*.log</code> for <code>-javaagent</code> and <code>-Dvein.agent.port</code>.</li>
<li>Test the port with <code>Test-NetConnection 127.0.0.1 -Port &lt;port&gt;</code>.</li></ol>
<h2>What the agent does</h2>
<table><thead><tr><th>Stage</th><th>Behaviour</th></tr></thead><tbody>
<tr><td>premain</td><td>Reads the port and starts a local TCP server</td></tr>
<tr><td>state</td><td>Reflects player, position, health, dimension</td></tr>
<tr><td>chat</td><td>Calls <code>ClientPacketListener.sendCommand</code></td></tr>
<tr><td>errors</td><td>Return <code>{"ok":false,"error":...}</code></td></tr>
</tbody></table>
""",

"mlc/overview.html": """
<h2>One round trip</h2>
<pre><code>mlc.agentChat("/time set day", 0)
  → resolve port of the newest vanilla instance
  → TCP {"cmd":"chat","text":"/time set day"}
  → agent calls sendCommand on the game thread
  ← {"ok":true}</code></pre>
<h2>State sample</h2>
<pre><code>{"inGame":true,"player":{"name":"Player","x":-1044.9,"y":64.0,
 "z":-1068.1,"health":20.0,"food":20.0,"dimension":"minecraft:overworld"}}</code></pre>
<h2>When not to use MLC</h2>
<ul><li>Fabric/Forge instances — no agent is attached.</li>
<li>You only need a command copied — turn the switch off and use hotkeys.</li>
<li>Inventory or entity access — out of scope.</li></ul>
""",
}
