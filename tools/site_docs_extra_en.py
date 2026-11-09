"""Documentation extras (English)."""

EXTRA = {
"getting-started/install.html": """
<h2>Verify the download</h2>
<pre><code>certutil -hashfile VeinLauncher-0.5.1-win64.zip SHA256</code></pre>
<p>Compare with the SHA-256 on the release page before extracting. The extracted folder should contain <code>VeinLauncher.exe</code> and <code>_internal/</code>.</p>
<h2>Where to install</h2>
<table><thead><tr><th>Location</th><th>Suitable for</th></tr></thead><tbody>
<tr><td>A short path on a data drive</td><td>Everyday use</td></tr>
<tr><td>Desktop / Downloads</td><td>Trying it out</td></tr>
<tr><td>A cloud sync folder</td><td>Not recommended (large caches)</td></tr>
</tbody></table>
<h2>Upgrade and uninstall</h2>
<p>Close the launcher and the game, extract the new build to a new folder, verify it starts, then point it at the existing <code>VeinLauncher/</code> data folder or move the folder next to the new build.</p>
<div class="callout warn"><b>Do not overwrite a running install:</b> Windows locks the exe and DLLs, leaving a half-updated folder.</div>
""",

"getting-started/first-launch.html": """
<h2>What to check after launch</h2>
<table><thead><tr><th>Area</th><th>Expected</th></tr></thead><tbody>
<tr><td>Version cards</td><td>The version you installed, with its loader tag</td></tr>
<tr><td>Account row</td><td>Offline name or LittleSkin / Microsoft account</td></tr>
<tr><td>Announcements / game log</td><td>Latest announcement, then live game log</td></tr>
</tbody></table>
<h2>First-run files</h2>
<p>The first start creates <code>VeinLauncher/</code> with config and logs. Instances appear only after you install a version. Logs go to <code>log/launcher-YYYY-MM-DD.log</code>.</p>
<div class="callout tip"><b>Switching accounts is safe:</b> instances and saves are not tied to the account.</div>
""",

"getting-started/java.html": """
<h2>How Java is chosen</h2>
<ol class="steps"><li><h3>Read the version JSON</h3><p>Use <code>javaVersion.majorVersion</code> (8 / 17 / 21).</p></li>
<li><h3>Check the machine</h3><p>Scan recorded paths, registry entries and common install folders, preferring 64-bit.</p></li>
<li><h3>Download if missing</h3><p>Fetch the matching Temurin JRE from Adoptium into the data folder.</p></li>
<li><h3>Launch</h3><p>Build the command with the resolved <code>javaw.exe</code>; the log records the exact path.</p></li></ol>
<h2>Memory guidance</h2>
<table><thead><tr><th>Scenario</th><th>Suggested Xmx</th></tr></thead><tbody>
<tr><td>Vanilla / light mods</td><td>2048–4096 MB</td></tr>
<tr><td>Medium modpacks</td><td>4096–6144 MB</td></tr>
<tr><td>Large modpacks</td><td>6144–8192 MB</td></tr>
</tbody></table>
<div class="callout warn"><b>Stay under ~60% of RAM:</b> leaving headroom avoids swapping.</div>
""",

"getting-started/directories.html": """
<h2>Folder responsibilities</h2>
<table><thead><tr><th>Folder</th><th>Safe to delete</th><th>Notes</th></tr></thead><tbody>
<tr><td><code>config/</code></td><td>No</td><td>Accounts, launch options, UI prefs</td></tr>
<tr><td><code>log/</code></td><td>Yes</td><td>Diagnostics only</td></tr>
<tr><td><code>minecraft/instances/</code></td><td>Careful</td><td>Mods and saves live here</td></tr>
<tr><td><code>downloads/</code></td><td>Yes</td><td>Cache, re-downloaded on demand</td></tr>
<tr><td><code>agent/</code></td><td>Yes</td><td>Copied back from the app folder</td></tr>
</tbody></table>
<h2>Backup</h2>
<p>Saves live in <code>instances/&lt;id&gt;/saves</code>. For a full migration copy the whole <code>VeinLauncher/</code> folder; it contains account tokens, so keep backups private.</p>
""",

"play/instances.html": """
<h2>Inside an instance</h2>
<pre><code>instances/1.20.1/
  mods/ config/ saves/ resourcepacks/ shaderpacks/
  options.txt
  &lt;version&gt;.jar</code></pre>
<h2>Duplicating safely</h2>
<p>Close the instance first; copying while it runs can capture half-written saves and lock files. After copying, rename the folder to avoid collisions.</p>
<div class="callout warn"><b>Never run the same instance twice:</b> saves share one session and overwrite each other.</div>
<h2>Deleting</h2>
<p>Deleting removes mods and saves permanently. Move any world you want to keep before deleting.</p>
""",

"play/skins.html": """
<h2>LittleSkin flow</h2>
<ol class="steps"><li><h3>Sign in</h3><p>Enter the LittleSkin email and password on the skins page.</p></li>
<li><h3>Pick a character</h3><p>Choose the skin-site character to use.</p></li>
<li><h3>Launch</h3><p>The launcher prepares authlib-injector and injects it with <code>-javaagent</code>.</p></li></ol>
<h2>Local PNG skins</h2>
<p>Vanilla cannot read local skin files. Create a Fabric instance with CustomSkinLoader:</p>
<pre><code>python tools/install_skin_support.py 1.20.1</code></pre>
<h2>Troubleshooting</h2>
<table><thead><tr><th>Symptom</th><th>Check</th></tr></thead><tbody>
<tr><td>Default skin only</td><td>Account type; authlib line in the log</td></tr>
<tr><td>Skin shows offline</td><td>Vanilla instance without CustomSkinLoader</td></tr>
</tbody></table>
""",

"play/commands.html": """
<h2>Useful commands</h2>
<table><thead><tr><th>Command</th><th>Effect</th></tr></thead><tbody>
<tr><td><code>/time set day</code></td><td>Set daytime</td></tr>
<tr><td><code>/weather clear</code></td><td>Clear weather</td></tr>
<tr><td><code>/gamemode creative</code></td><td>Creative mode</td></tr>
<tr><td><code>/give @s minecraft:diamond 64</code></td><td>64 diamonds</td></tr>
<tr><td><code>/gamerule keepInventory true</code></td><td>Keep inventory on death</td></tr>
</tbody></table>
<h2>Builder vs search mode</h2>
<ul><li><strong>Builder</strong>: the prefix matches the command tree, candidates append one by one.</li>
<li><strong>Search</strong>: keywords (Chinese or item IDs) match across the whole library.</li></ul>
<div class="callout tip"><b>Enter:</b> sends when the command is complete, otherwise appends. Use Ctrl+Enter to force send.</div>
<h2>Permissions</h2>
<p>Commands still need cheats enabled or server OP. MLC only types them into chat — it does not bypass permissions.</p>
""",

"play/hotkeys.html": """
<h2>Binding</h2>
<ol><li>Open Tools → Commands.</li>
<li>Type a command and pick a numeric slot (0–9).</li>
<li>Save; the hotkey is registered globally and rebound on the next start.</li></ol>
<h2>Fallbacks</h2>
<table><thead><tr><th>Situation</th><th>Result</th></tr></thead><tbody>
<tr><td>Hotkey already taken</td><td>Registration fails; the tools page lists the slot</td></tr>
<tr><td>MLC available</td><td>Command sent into the game</td></tr>
<tr><td>MLC unavailable</td><td>Command copied to clipboard</td></tr>
</tbody></table>
<h2>Multiple instances</h2>
<p>Hotkeys target the most recently launched running vanilla instance. Switch instances on the MLC page to change the target.</p>
""",

"play/troubleshooting.html": """
<h2>Collect these first</h2>
<ol><li>Launcher version (Settings → About)</li><li>Last 30 lines of <code>log/launcher-*.log</code></li><li>Exact steps that triggered the issue</li></ol>
<h2>Reading logs</h2>
<table><thead><tr><th>Keyword</th><th>Meaning</th></tr></thead><tbody>
<tr><td>exit code</td><td>Game exit status; non-zero usually means a crash</td></tr>
<tr><td>missing java</td><td>No runtime found</td></tr>
<tr><td>incomplete jar</td><td>Client jar missing or locked</td></tr>
<tr><td>mirror / fallback</td><td>Download source fallback</td></tr>
</tbody></table>
<h2>Common combos</h2>
<ul><li>Mods not loading: confirm the selected instance is the loader build.</li>
<li>Corrupted saves after double-launch: duplicate instances instead.</li>
<li>HTTPS failures: fix the system clock.</li>
<li>Proxy interference: configure or disable the system proxy.</li></ul>
""",

"develop/architecture.html": """
<h2>Launch data flow</h2>
<pre><code>React Launch button
  → bridge.launch(version, account)
  → LauncherService.launch()
      → VersionService.merged()     inherit chain
      → JavaManager.ensure()        runtime
      → libraries / natives / agent args
      → Popen(javaw ...)
  → event_bus.publish("game.started")
  → bridge pushes __veinGameStarted</code></pre>
<h2>Event list</h2>
<table><thead><tr><th>Event</th><th>Publisher</th></tr></thead><tbody>
<tr><td><code>download.progress</code></td><td>download service</td></tr>
<tr><td><code>game.log</code> / <code>game.exited</code></td><td>process watcher</td></tr>
<tr><td><code>mlc.agent.*</code></td><td>MLC poller</td></tr>
<tr><td><code>plugin.*</code></td><td>plugin service</td></tr>
</tbody></table>
<h2>Checklist for a new service</h2>
<ul><li>Put it in <code>application/services/</code> with injected dependencies.</li>
<li>Wire it in <code>presentation/context.py</code>; expose it through bridge.</li>
<li>Never touch Qt from services — publish events instead.</li>
<li>Add tests and a docs page.</li></ul>
""",

"develop/rpc.html": """
<h2>Request / response</h2>
<pre><code>// frontend
const info = await rpc&lt;VersionInfo[]&gt;('versions.info', []);

// bridge.py
async def _versions_info(self) -&gt; list[dict]:
    return self._ctx.versions.list_installed()</code></pre>
<h2>Errors</h2>
<p>Backend exceptions become <code>{ code, message }</code> and are thrown as <code>Error</code> on the frontend. Keep stack traces in logs, not in user-facing text.</p>
<h2>Push channels</h2>
<table><thead><tr><th>Function</th><th>Purpose</th></tr></thead><tbody>
<tr><td><code>__veinResult</code></td><td>RPC result</td></tr>
<tr><td><code>__veinProgress</code></td><td>Download progress</td></tr>
<tr><td><code>__veinLog</code></td><td>Log lines</td></tr>
<tr><td><code>__veinNotify</code></td><td>Notifications</td></tr>
<tr><td><code>__veinMlcEvent</code></td><td>MLC events</td></tr>
</tbody></table>
""",

"develop/frontend.html": """
<h2>Pages</h2>
<table><thead><tr><th>Page</th><th>File</th></tr></thead><tbody>
<tr><td>Launch</td><td><code>launchPage.tsx</code></td></tr>
<tr><td>Download</td><td><code>downloadPage.tsx</code></td></tr>
<tr><td>Instances</td><td><code>instancePage.tsx</code></td></tr>
<tr><td>Skins</td><td><code>skinsPage.tsx</code></td></tr>
<tr><td>Settings</td><td><code>settingsPage.tsx</code></td></tr>
<tr><td>Tools</td><td><code>toolsPage.tsx</code></td></tr>
</tbody></table>
<h2>Theming</h2>
<p>All colors come from CSS variables in <code>styles.css</code>. Accent overrides live in <code>accent.ts</code>; radius, zoom and motion are handled by <code>uiCustom.ts</code> through <code>data-*</code> attributes.</p>
<div class="callout warn"><b>Always rebuild:</b> Qt loads <code>dist/app.js</code>, not the source.</div>
""",

"develop/testing.html": """
<h2>Test layers</h2>
<table><thead><tr><th>Layer</th><th>Command</th></tr></thead><tbody>
<tr><td>Unit</td><td><code>python -m unittest discover -s tests</code></td></tr>
<tr><td>Plugin integration</td><td><code>python tools/plugin_selftest.py</code></td></tr>
<tr><td>MLC smoke</td><td><code>python tools/mlc_selftest.py</code></td></tr>
<tr><td>Real game</td><td><code>python tools/agent_smoke.py</code></td></tr>
</tbody></table>
<h2>Writing tests</h2>
<pre><code>class MyTest(unittest.TestCase):
    def test_something(self):
        self.assertEqual(foo(), expected)</code></pre>
<p>Do not depend on the network or a running game; mock or use temporary directories.</p>
""",

"develop/packaging.html": """
<h2>What goes into the package</h2>
<ul><li><code>webui/dist</code> — built frontend</li><li><code>assets</code> — logo and icons</li>
<li>Plugin host runtime (<code>node_host.js</code>, <code>lua.js</code>)</li>
<li><code>i18n/locales</code> and <code>plugins_examples</code></li><li><code>agent/*.jar</code> for MLC</li></ul>
<h2>Size</h2>
<p>PyInstaller ships a lot of Qt by default; the build script trims translations, QML and opengl32sw. Current output: ~495 MB folder, ~199 MB zip.</p>
<h2>Release checklist</h2>
<ol><li>Run the unit tests.</li><li>Build with <code>--version X.Y.Z</code>.</li>
<li>Smoke-test the exe and check the window title version.</li>
<li>Upload the zip and <code>latest.json</code>; verify the SHA-256.</li>
<li>Update download page, changelog and screenshots.</li></ol>
""",

"plugins/overview.html": """
<h2>Process model</h2>
<pre><code>Launcher (Python)
  └─ node_host.js (one child process per plugin)
       ├─ stdin/stdout JSON lines
       ├─ host.call → Python capability registry
       └─ event.emit ← Python event bus</code></pre>
<h2>Lifecycle</h2>
<table><thead><tr><th>Stage</th><th>Behaviour</th></tr></thead><tbody>
<tr><td>Scan</td><td>Read <code>package.json</code>, require the <code>vein</code> block</td></tr>
<tr><td>Activate</td><td>Call <code>activate(vein)</code>, 30 s timeout</td></tr>
<tr><td>Run</td><td>Serve capability calls and events</td></tr>
<tr><td>Stop</td><td>Call <code>deactivate()</code>, then end the process</td></tr>
</tbody></table>
<h2>Isolation</h2>
<ul><li>A crashing plugin never takes down the launcher.</li>
<li>File access is limited to the plugin sandbox.</li>
<li>Network and downloads go through the launcher for consistent timeouts and proxies.</li></ul>
""",

"plugins/manifest.html": """
<h2>Fields</h2>
<table><thead><tr><th>Field</th><th>Required</th><th>Notes</th></tr></thead><tbody>
<tr><td><code>name</code></td><td>yes</td><td>Unique id, ideally <code>vein-plugin-*</code></td></tr>
<tr><td><code>version</code></td><td>yes</td><td>Semver</td></tr>
<tr><td><code>type</code></td><td>yes</td><td><code>module</code></td></tr>
<tr><td><code>main</code></td><td>yes</td><td>Entry file</td></tr>
<tr><td><code>vein.displayName</code></td><td>no</td><td>Shown in the plugins page</td></tr>
<tr><td><code>vein.activateOnStartup</code></td><td>no</td><td>Auto-activate</td></tr>
<tr><td><code>vein.permissions</code></td><td>yes</td><td>Capability allow-list</td></tr>
</tbody></table>
<h2>Validation errors</h2>
<ul><li>Missing <code>vein</code> block → not recognised.</li><li><code>main</code> missing → activation fails.</li>
<li>CommonJS <code>require</code> → must use ESM.</li></ul>
""",

"plugins/permissions.html": """
<h2>Capability → permission</h2>
<table><thead><tr><th>Capability</th><th>Permission</th></tr></thead><tbody>
<tr><td>file.readText / listDir</td><td>file.read</td></tr>
<tr><td>file.writeText</td><td>file.write</td></tr>
<tr><td>config.*</td><td>config.read / config.write</td></tr>
<tr><td>ui.notify / openPage</td><td>ui.notify / ui.open_page</td></tr>
<tr><td>ui.render / ui.lua</td><td>ui.lua</td></tr>
<tr><td>http.getJson</td><td>network.http</td></tr>
<tr><td>download.queueTask</td><td>download.queue</td></tr>
<tr><td>game.launch</td><td>game.launch</td></tr>
<tr><td>game.running / command</td><td>game.state / game.command</td></tr>
<tr><td>app.info / versions.list</td><td>app.info / versions.read</td></tr>
<tr><td>mlc.*</td><td>mlc.state / mlc.player / mlc.world / mlc.mod</td></tr>
</tbody></table>
<h2>Denied calls</h2>
<p>Node rejects before IPC with <code>permission denied: NAME</code>; Python validates again. The plugins page records the failure.</p>
""",

"plugins/api.html": """
<h2>Example</h2>
<pre><code>export async function activate(vein) {
  const info = await vein.app.info();
  const versions = await vein.versions.list();
  const running = await vein.game.running();
  const mlc = await vein.mlc.state();

  await vein.ui.render({
    type: "panel",
    title: `Vein ${info.version}`,
    children: [
      { type: "text", value: `${versions.length} instances` },
      { type: "badge", value: mlc.enabled ? "MLC on" : "MLC off" },
    ],
  });
}</code></pre>
<h2>Return shapes</h2>
<table><thead><tr><th>Method</th><th>Result</th></tr></thead><tbody>
<tr><td><code>app.info()</code></td><td><code>{ version, dataDir }</code></td></tr>
<tr><td><code>versions.list()</code></td><td><code>[{ id, type }]</code></td></tr>
<tr><td><code>game.running()</code></td><td><code>{ games: [...] }</code></td></tr>
<tr><td><code>mlc.state()</code></td><td><code>{ enabled }</code></td></tr>
</tbody></table>
""",

"plugins/ui.html": """
<h2>Components</h2>
<table><thead><tr><th>Component</th><th>Purpose</th></tr></thead><tbody>
<tr><td>panel</td><td>Titled container</td></tr><tr><td>row</td><td>Horizontal layout</td></tr>
<tr><td>text</td><td>Plain text</td></tr><tr><td>button</td><td>Emits <code>ui.onAction</code></td></tr>
<tr><td>input</td><td>Text input</td></tr><tr><td>table</td><td>Columns and rows</td></tr>
<tr><td>list</td><td>Item list</td></tr><tr><td>badge</td><td>Status badge</td></tr>
<tr><td>image</td><td>Sandboxed image</td></tr><tr><td>divider</td><td>Separator</td></tr>
</tbody></table>
<h2>Actions</h2>
<pre><code>vein.ui.onAction(async (action) =&gt; {
  if (action === "refresh") await render();
});</code></pre>
<div class="callout warn"><b>Shadow DOM:</b> plugin styles cannot affect the launcher, and the launcher DOM is not reachable.</div>
""",

"plugins/examples.html": """
<h2>What each example shows</h2>
<table><thead><tr><th>Folder</th><th>Demonstrates</th></tr></thead><tbody>
<tr><td>template</td><td>Minimal skeleton</td></tr>
<tr><td>game-log</td><td>Log events to a sandbox file</td></tr>
<tr><td>lua-ui</td><td>Lua panel with actions</td></tr>
<tr><td>mlc-panel</td><td>Reading MLC state</td></tr>
<tr><td>status-panel</td><td>Version, instances, games and MLC in one panel</td></tr>
</tbody></table>
<h2>Run one</h2>
<ol><li>Copy the folder into <code>VeinLauncher/plugin/</code>.</li><li>Enable it on the plugins page.</li>
<li>Check <code>log/plugin-*.log</code> for “activated”.</li></ol>
""",

"plugins/debugging.html": """
<h2>Where to look</h2>
<table><thead><tr><th>Location</th><th>Content</th></tr></thead><tbody>
<tr><td><code>log/plugin-*.log</code></td><td>Host and plugin output, capability errors</td></tr>
<tr><td>Plugins page</td><td>Enabled state, version, failure reason</td></tr>
</tbody></table>
<h2>Common issues</h2>
<ul><li>Fails immediately: syntax error or missing permission.</li>
<li>Timeouts: blocking work in a callback.</li>
<li>UI missing: <code>ui.render</code> needs <code>ui.lua</code>.</li>
<li>Not listed: wrong folder depth.</li></ul>
<h2>Reload</h2>
<p>The reload button restarts the plugin process; no launcher restart needed.</p>
""",

"mlc/overview.html": """
<h2>State you can read</h2>
<table><thead><tr><th>Field</th><th>Example</th></tr></thead><tbody>
<tr><td>name</td><td>Player</td></tr><tr><td>x / y / z</td><td>-1044.9 / 64.0 / -1068.1</td></tr>
<tr><td>health / food</td><td>20.0 / 20.0</td></tr><tr><td>dimension</td><td>minecraft:overworld</td></tr>
</tbody></table>
<h2>Capabilities / limits</h2>
<table><thead><tr><th>Can</th><th>Cannot</th></tr></thead><tbody>
<tr><td>Read player and dimension state</td><td>Read or write inventory or entities</td></tr>
<tr><td>Send chat commands</td><td>Bypass OP or cheats</td></tr>
<tr><td>Subscribe to world events</td><td>Modify game memory or files</td></tr>
</tbody></table>
<h2>Master switch</h2>
<p>Off by default. While off, sending, reading and events are rejected by the backend and hotkeys fall back to copying.</p>
""",

"mlc/how-it-works.html": """
<h2>Agent generation</h2>
<ol class="steps"><li><h3>Mappings</h3><p>Download the official client mappings for the target version.</p></li>
<li><h3>Resolve names</h3><p>Find <code>Minecraft</code>, <code>Player</code>, <code>ClientPacketListener</code>, etc.</p></li>
<li><h3>Render source</h3><p>Fill the Java template and start a local TCP server in <code>premain</code>.</p></li>
<li><h3>Compile</h3><p>javac produces a ~5 KB jar under <code>agent/</code>.</p></li></ol>
<h2>Injection</h2>
<pre><code>-javaagent:&lt;data&gt;/agent/vein-agent-1.20.1.jar
-Dvein.agent.port=25566</code></pre>
<p>Only vanilla instances get these flags; ports are allocated from 25566 upward.</p>
""",

"mlc/protocol.html": """
<h2>Examples</h2>
<pre><code>→ {"cmd":"state"}
← {"inGame":true,"player":{"name":"Player","health":20.0,"dimension":"minecraft:overworld"}}</code></pre>
<pre><code>→ {"cmd":"chat","text":"/time set day"}
← {"ok":true}</code></pre>
<h2>Manual test</h2>
<pre><code>$c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 25566)
$s = $c.GetStream(); $w = New-Object System.IO.StreamWriter($s)
$w.WriteLine('{"cmd":"state"}'); $w.Flush()
(New-Object System.IO.StreamReader($s)).ReadLine()</code></pre>
<h2>Notes</h2>
<ul><li>One JSON object per line.</li><li><code>inGame:false</code> means commands will fail.</li>
<li>Localhost only, no authentication — never expose it.</li></ul>
""",

"mlc/events.html": """
<h2>Events</h2>
<table><thead><tr><th>Event</th><th>Trigger</th></tr></thead><tbody>
<tr><td><code>mlc.agent.game.enter</code></td><td>World entered</td></tr>
<tr><td><code>mlc.agent.game.leave</code></td><td>Back to menu</td></tr>
<tr><td><code>mlc.agent.player.dimension</code></td><td>Dimension change</td></tr>
<tr><td><code>mlc.agent.player.death</code></td><td>Health reaches zero</td></tr>
</tbody></table>
<h2>Subscribing</h2>
<pre><code>vein.mlc.on("game.enter", () =&gt; vein.log("entered"));</code></pre>
<div class="callout"><b>Debounce:</b> events come from a 1 s state diff, so rapid changes collapse into the final state.</div>
""",

"mlc/troubleshooting.html": """
<h2>Symptoms</h2>
<table><thead><tr><th>Symptom</th><th>Cause</th><th>Fix</th></tr></thead><tbody>
<tr><td>Not connected</td><td>Loader instance / not in world</td><td>Use vanilla, enter a world</td></tr>
<tr><td>Commands fail</td><td>Switch off or cheats disabled</td><td>Enable both</td></tr>
<tr><td>Wrong instance</td><td>Port resolved to newest instance</td><td>Target a pid or run one game</td></tr>
</tbody></table>
<h2>Manual check</h2>
<p>Look for <code>-javaagent</code> and <code>-Dvein.agent.port</code> in the launch command, then test <code>state</code> over TCP.</p>
""",

"reference/config.html": """
<h2>Fields</h2>
<table><thead><tr><th>Field</th><th>Notes</th></tr></thead><tbody>
<tr><td><code>ui.language</code></td><td><code>zh_CN</code> / <code>en_US</code></td></tr>
<tr><td><code>ui.theme</code></td><td>light / dark / clear / system</td></tr>
<tr><td><code>ui.accent</code></td><td>Hex accent, empty for the default orange</td></tr>
<tr><td><code>launch.memory_min/max</code></td><td>Heap in MB</td></tr>
<tr><td><code>launch.jvm_args</code></td><td>Extra JVM flags</td></tr>
<tr><td><code>download.source</code></td><td>auto / bmclapi / official</td></tr>
<tr><td><code>mlc.enabled</code></td><td>MLC master switch</td></tr>
</tbody></table>
<div class="callout warn"><b>Back up first:</b> invalid JSON falls back to defaults.</div>
""",

"reference/faq.html": """
<h2>Install</h2><h3>Missing DLL after unzip</h3><p>Extract again with 7-Zip; make sure <code>_internal/</code> exists.</p>
<h3>USB drive?</h3><p>Works, but slower I/O will affect loading times.</p>
<h2>Accounts</h2><h3>Cannot join an online server</h3><p>Use a Microsoft account; offline accounts only work on offline servers.</p>
<h2>MLC</h2><h3>Why not on Fabric?</h3><p>The agent relies on official mappings; loaders change class structure.</p>
<h3>Hotkeys after turning MLC off</h3><p>They fall back to copying the command.</p>
<h2>Plugins</h2><h3>Restart needed?</h3><p>No — enable it on the plugins page.</p>
<h3>Can plugins read saves?</h3><p>No, file access is limited to the plugin sandbox.</p>
""",

"reference/glossary.html": """
<table><thead><tr><th>Term</th><th>Meaning</th></tr></thead><tbody>
<tr><td>Loader</td><td>Fabric / Forge / Quilt / NeoForge</td></tr>
<tr><td>Inheritance chain</td><td>Loader JSON pointing at a vanilla version via <code>inheritsFrom</code></td></tr>
<tr><td>Natives</td><td>Platform DLLs extracted per instance</td></tr>
<tr><td>Asset index</td><td>Hash and path list for game resources</td></tr>
<tr><td>authlib-injector</td><td>Java agent that injects skin-site authentication</td></tr>
<tr><td>Capability</td><td>Backend function a plugin may call with permission</td></tr>
</tbody></table>
""",

"reference/security.html": """
<h2>Trust boundaries</h2>
<table><thead><tr><th>Subject</th><th>Access</th></tr></thead><tbody>
<tr><td>Frontend</td><td>Only exposed RPC methods</td></tr>
<tr><td>Plugins</td><td>Declared capabilities and sandbox folder</td></tr>
<tr><td>MLC agent</td><td>127.0.0.1 only</td></tr>
</tbody></table>
<h2>Network endpoints</h2>
<table><thead><tr><th>Host</th><th>Purpose</th></tr></thead><tbody>
<tr><td>BMCLAPI / Mojang</td><td>Versions and assets</td></tr>
<tr><td>LittleSkin</td><td>Skins</td></tr>
<tr><td>GitHub</td><td>Updates</td></tr>
<tr><td>Adoptium</td><td>Java runtime</td></tr>
</tbody></table>
<h2>Reporting</h2>
<p>Use GitHub private vulnerability reporting; avoid public repro details.</p>
""",
}
