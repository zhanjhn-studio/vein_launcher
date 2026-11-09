"""English content for the site (mirrors site_content.py paths)."""

PAGES_EN = [
    dict(path="getting-started/install.html", group="Getting started", title="Download & install",
         subtitle="Windows 10/11 x64. Unzip and run — no registry writes.",
         tags=["Download", "Install", "Windows"],
         body="""
<p>Vein Launcher ships as an onedir zip. Unzip it and run <code>VeinLauncher.exe</code>. A data folder is created next to the exe; deleting the folder uninstalls everything.</p>
<h2>Requirements</h2>
<table><thead><tr><th>Item</th><th>Requirement</th></tr></thead><tbody>
<tr><td>OS</td><td>Windows 10 / 11 x64</td></tr>
<tr><td>Disk</td><td>~500 MB for the launcher, games not included</td></tr>
<tr><td>Java</td><td>Not required manually — the launcher detects or downloads it</td></tr>
<tr><td>Node.js</td><td>Only for plugins (18+)</td></tr>
</tbody></table>
<h2>Download</h2>
<p>Get the latest build from the <a href="../download.html">download page</a> or GitHub Releases:</p>
<pre><code>https://github.com/zhanjhn-studio/vein_launcher/releases/download/v0.5.1/VeinLauncher-0.5.1-win64.zip</code></pre>
<h2>Steps</h2>
<ol class="steps"><li><h3>Unzip</h3><p>Extract to a path such as <code>D:\\VeinLauncher</code>.</p></li>
<li><h3>Run</h3><p>Double-click <code>VeinLauncher.exe</code>; the <code>VeinLauncher/</code> data folder is created on first launch.</p></li>
<li><h3>Install a version</h3><p>Open “Download”, pick vanilla or a loader, then install. Mirrors are tried first, official sources are the fallback.</p></li></ol>
<div class="callout"><b>No installer:</b> the project intentionally ships as a portable folder. Upgrading means replacing the app folder; config and instances stay.</div>
"""),

    dict(path="getting-started/first-launch.html", group="Getting started", title="First launch",
         subtitle="From opening the launcher to entering the game.",
         tags=["Quick start", "Account", "Launch"],
         body="""
<p>Three steps: install a version, pick an account, press launch.</p>
<h2>1. Install a version</h2>
<p>The download page lists vanilla builds and loader builds (Fabric / Forge / Quilt / NeoForge). Installing downloads the client jar, libraries and asset index.</p>
<h2>2. Pick an account</h2>
<table><thead><tr><th>Type</th><th>Details</th></tr></thead><tbody>
<tr><td>Offline</td><td>Any 3–16 character name; single-player is fine</td></tr>
<tr><td>Microsoft</td><td>OAuth device-code flow; required for online servers</td></tr>
<tr><td>LittleSkin</td><td>Skin-site account; skin injection is configured automatically</td></tr>
</tbody></table>
<h2>3. Launch</h2>
<p>Go back to “Launch”, select the instance and press play. Natives are completed and Java is resolved automatically.</p>
<div class="callout ok"><b>Tip:</b> when a launch fails, read the last 20 lines of <code>VeinLauncher/log/launcher-DATE.log</code> first.</div>
"""),

    dict(path="getting-started/java.html", group="Getting started", title="Java runtime",
         subtitle="Detect, download or point to a JDK explicitly.",
         tags=["Java", "Runtime"],
         body="""
<p>The launcher uses an installed Java when possible, otherwise downloads the right major version from Adoptium.</p>
<h2>Version matrix</h2>
<table><thead><tr><th>Minecraft</th><th>Java</th></tr></thead><tbody>
<tr><td>1.16.5 and older</td><td>Java 8</td></tr>
<tr><td>1.17 – 1.20.4</td><td>Java 17</td></tr>
<tr><td>1.20.5+</td><td>Java 21</td></tr>
</tbody></table>
<h2>Explicit path</h2>
<pre><code>VeinLauncher/config/config.json
{
  "java": { "path": "C:/Program Files/Java/jdk-17/bin/javaw.exe" }
}</code></pre>
<div class="callout warn"><b>Note:</b> 32-bit Java cannot allocate more than 1.5 GB; only 64-bit runtimes are accepted.</div>
"""),

    dict(path="getting-started/directories.html", group="Getting started", title="Data folder",
         subtitle="Config, logs, instances, plugins and caches share one folder.",
         tags=["Folders", "Backup"],
         body="""
<p>Everything lives in <code>VeinLauncher/</code> next to the exe, so the folder can be moved or backed up as a whole.</p>
<pre><code>VeinLauncher/
  config/      config.json / accounts.json / tools.json
  log/         launcher / download / mlc / plugin, one file per day
  minecraft/   instances, assets, libraries
  plugin/      plugins
  downloads/   download cache
  agent/       MLC agent jars</code></pre>
<h2>Backup</h2>
<p>Copy the whole <code>VeinLauncher/</code> folder. Saves live under <code>minecraft/instances/&lt;version&gt;/saves</code>.</p>
"""),

    dict(path="play/instances.html", group="Playing", title="Instances",
         subtitle="Each instance is an isolated game folder with its own mods and saves.",
         tags=["Instances", "Mods", "Saves"],
         body="""
<p>An instance maps to <code>minecraft/instances/&lt;name&gt;/</code> with <code>mods</code>, <code>saves</code>, <code>config</code> and <code>resourcepacks</code>.</p>
<h2>Common operations</h2>
<table><thead><tr><th>Operation</th><th>Where</th></tr></thead><tbody>
<tr><td>Import mods / shaders / resource packs</td><td>Instance page → matching tab → import</td></tr>
<tr><td>Browse saves</td><td>Instance page → saves</td></tr>
<tr><td>Duplicate instance</td><td>Instance card → duplicate</td></tr>
<tr><td>Delete instance</td><td>Instance card → delete (mods and saves included)</td></tr>
</tbody></table>
<div class="callout warn"><b>Do not run the same instance twice:</b> saves share one session. Duplicate the instance instead.</div>
"""),

    dict(path="play/skins.html", group="Playing", title="Skins",
         subtitle="LittleSkin works out of the box; local PNGs need Fabric + CustomSkinLoader.",
         tags=["Skins", "LittleSkin"],
         body="""
<h2>LittleSkin</h2>
<p>Sign in on the skins page and launch. The launcher downloads <code>authlib-injector.jar</code> (~350 KB) and injects it via <code>-javaagent</code>.</p>
<h2>Local PNG</h2>
<p>Vanilla Minecraft does not support local skin files. Add skin support to an instance:</p>
<pre><code>python tools/install_skin_support.py 1.20.1</code></pre>
<p>This creates a <code>fabric-1.20.1</code> instance with CustomSkinLoader installed.</p>
"""),

    dict(path="play/commands.html", group="Playing", title="Command palette",
         subtitle="Ctrl+Alt+Q opens the enchanted-book palette; Enter sends the command.",
         tags=["Commands", "Palette"],
         body="""
<table><thead><tr><th>Action</th><th>Behaviour</th></tr></thead><tbody>
<tr><td>Click a candidate</td><td>Append, or fill in search mode</td></tr>
<tr><td>Double-click</td><td>Send straight to the game</td></tr>
<tr><td>↑ / ↓</td><td>Move selection</td></tr>
<tr><td>Tab / →</td><td>Append the highlighted candidate</td></tr>
<tr><td>Enter</td><td>Send when complete; otherwise append</td></tr>
<tr><td>Ctrl+Enter</td><td>Force send</td></tr>
<tr><td>Esc</td><td>Close</td></tr>
</tbody></table>
<div class="callout warn"><b>On failure:</b> a dialog is shown and the command is copied to the clipboard.</div>
"""),

    dict(path="play/hotkeys.html", group="Playing", title="Global hotkeys",
         subtitle="Ctrl+Alt+0..9 runs a bound command.",
         tags=["Hotkeys"],
         body="""
<p>Bind commands to number slots in the tools page; the launcher registers them as global hotkeys.</p>
<ol><li>Send through MLC when available.</li>
<li>Fall back to copying the command when MLC is off or the game is not running.</li>
<li>A toast tells you which path was used.</li></ol>
"""),

    dict(path="play/troubleshooting.html", group="Playing", title="Troubleshooting",
         subtitle="Launch failures, stuck downloads and missing skins.",
         tags=["Troubleshooting", "Logs"],
         body="""
<table><thead><tr><th>Symptom</th><th>Cause</th><th>Fix</th></tr></thead><tbody>
<tr><td>ClassNotFoundException: net.minecraft.client.main.Main</td><td>Incomplete client jar</td><td>Re-run install to resume, or reinstall the instance</td></tr>
<tr><td>No title bar, cannot resize</td><td>Resolution equals screen size</td><td>Set 1280×720 in config</td></tr>
<tr><td>Exits right after launch</td><td>Java mismatch / low memory</td><td>Check the exit code, switch Java, raise memory</td></tr>
<tr><td>Downloads stall</td><td>Mirror timeout</td><td>Wait for fallback or clear <code>downloads/</code></td></tr>
</tbody></table>
<div class="callout tip"><b>Logs:</b> <code>VeinLauncher/log/</code>, split into launcher / download / mlc / plugin.</div>
"""),

    dict(path="develop/architecture.html", group="Development", title="Architecture",
         subtitle="Five layers plus a global event bus.",
         tags=["Architecture"],
         body="""
<pre><code>presentation/   Qt window, bridge, palette, webui (React + dist)
application/    version / skins / instances / update / plugins
domain/         models, repository contracts, rules
infrastructure/ network, download, process, mc2, plugin host, MLC agent build
common/         event bus, config, logging, i18n, utils</code></pre>
<p>Layers talk through <code>common/events/event_bus.py</code>. The UI pulls state over RPC; the backend pushes notifications.</p>
<h2>Where to put things</h2>
<table><thead><tr><th>Thing</th><th>Layer</th></tr></thead><tbody>
<tr><td>New API or mirror</td><td>infrastructure/</td></tr>
<tr><td>Business flow</td><td>application/services/</td></tr>
<tr><td>UI</td><td>presentation/webui/src/</td></tr>
<tr><td>RPC method</td><td>presentation/bridge.py</td></tr>
</tbody></table>
"""),

    dict(path="develop/rpc.html", group="Development", title="JSON-RPC",
         subtitle="JSON-RPC 2.0 over QWebChannel, handlers registered in bridge.py.",
         tags=["RPC", "Bridge"],
         body="""
<p>The frontend calls <code>rpc(method, params)</code>; the backend pushes events with <code>_run_js</code>.</p>
<table><thead><tr><th>Method</th><th>Purpose</th></tr></thead><tbody>
<tr><td><code>versions.info</code></td><td>Installed instances</td></tr>
<tr><td><code>launch</code></td><td>Start an instance</td></tr>
<tr><td><code>game.running</code> / <code>game.kill</code></td><td>Running games</td></tr>
<tr><td><code>mlc.state</code> / <code>mlc.setEnabled</code></td><td>MLC master switch</td></tr>
<tr><td><code>plugins.state</code> / <code>plugins.setEnabled</code></td><td>Plugin state</td></tr>
</tbody></table>
<h2>Adding a method</h2>
<ol class="steps"><li><h3>Implement</h3><p><code>async def _your_method(self, arg: str = "") -&gt; dict:</code></p></li>
<li><h3>Register</h3><p><code>self._handlers["your.method"] = self._your_method</code></p></li>
<li><h3>Call</h3><p><code>await rpc('your.method', [arg])</code></p></li></ol>
"""),

    dict(path="develop/frontend.html", group="Development", title="Frontend & build",
         subtitle="React 19 + TypeScript, bundled by esbuild into dist.",
         tags=["Frontend", "React"],
         body="""
<pre><code>cd vein_launcher/presentation/webui
powershell -ExecutionPolicy Bypass -File build.ps1</code></pre>
<p>The generated <code>dist/app.js</code> is committed because the launcher loads it directly.</p>
<table><thead><tr><th>File</th><th>Purpose</th></tr></thead><tbody>
<tr><td><code>App.tsx</code></td><td>Routing and layout</td></tr>
<tr><td><code>pages.tsx</code></td><td>Launch / download / MLC pages</td></tr>
<tr><td><code>toolsPage.tsx</code></td><td>Tools and commands</td></tr>
<tr><td><code>bridge.ts</code></td><td>RPC helpers and push callbacks</td></tr>
</tbody></table>
<div class="callout warn"><b>Common mistake:</b> editing <code>webui/src</code> without rebuilding.</div>
"""),

    dict(path="develop/testing.html", group="Development", title="Testing",
         subtitle="Unit tests, plugin self-test, MLC smoke tests.",
         tags=["Testing"],
         body="""
<pre><code>python -m unittest discover -s tests
python tools/plugin_selftest.py
python tools/mlc_selftest.py</code></pre>
<div class="callout ok"><b>Current:</b> 51 unit tests passing.</div>
"""),

    dict(path="develop/packaging.html", group="Development", title="Packaging",
         subtitle="PyInstaller onedir, zip and latest.json.",
         tags=["Packaging", "Release"],
         body="""
<pre><code>python tools/build_exe.py --version 0.5.1</code></pre>
<p>Outputs <code>dist_exe/VeinLauncher/</code>, a ~199 MB zip and <code>latest.json</code>.</p>
<pre><code>gh release upload v0.5.0 dist_exe/VeinLauncher-0.5.1-win64.zip
gh release edit v0.5.0 --draft=false</code></pre>
<div class="callout warn"><b>Before publishing:</b> check the version, asset checksum and latest.json, then point the updater at the new build.</div>
"""),

    dict(path="plugins/overview.html", group="Plugins", title="Plugin system",
         subtitle="Every plugin runs in its own Node process; anything outside its permissions is rejected.",
         tags=["Plugins", "Sandbox"],
         body="""
<p>Plugins live in <code>VeinLauncher/plugin/&lt;name&gt;/</code> and are loaded by the host process.</p>
<ol class="steps"><li><h3>Scan manifest</h3><p>Only <code>package.json</code> files with a <code>vein</code> field are accepted.</p></li>
<li><h3>Spawn process</h3><p>The host starts Node and speaks JSON lines over stdio.</p></li>
<li><h3>Check capabilities</h3><p>Permissions are enforced in Node, then again in Python with a path sandbox.</p></li>
<li><h3>Activate / deactivate</h3><p><code>activate(vein)</code> and <code>deactivate()</code> with a 30-second timeout.</p></li></ol>
"""),

    dict(path="plugins/manifest.html", group="Plugins", title="Manifest",
         subtitle="The vein field controls name, entry, permissions and auto-start.",
         tags=["package.json"],
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
"""),

    dict(path="plugins/permissions.html", group="Plugins", title="Permissions",
         subtitle="Permissions are hard requirements; undeclared access fails in Node.",
         tags=["Permissions"],
         body="""
<table><thead><tr><th>Capability</th><th>Permission</th></tr></thead><tbody>
<tr><td>file.readText / listDir</td><td>file.read</td></tr>
<tr><td>file.writeText</td><td>file.write</td></tr>
<tr><td>config.*</td><td>config.read / config.write</td></tr>
<tr><td>ui.notify / openPage</td><td>ui.notify / ui.open_page</td></tr>
<tr><td>ui.render</td><td>ui.lua</td></tr>
<tr><td>network.http.getJson</td><td>network.http</td></tr>
<tr><td>download.queueTask</td><td>download.queue</td></tr>
<tr><td>game.launch</td><td>game.launch</td></tr>
<tr><td>mlc.*</td><td>mlc.state / mlc.player / mlc.world / mlc.mod</td></tr>
</tbody></table>
"""),

    dict(path="plugins/api.html", group="Plugins", title="Capability API",
         subtitle="Everything on the vein object.",
         tags=["API"],
         body="""
<pre><code>vein.log(msg)
vein.file.readText(path) / writeText(path, text)
vein.config.read() / write(obj)
vein.ui.notify(title, message) / render(tree) / openPage(key)
vein.http.getJson(url)
vein.download.queueTask(url, savePath)
vein.game.launch(versionId) / running() / command("/time set day")
vein.app.info() / vein.versions.list()
vein.mlc.state() / playerInfo() / worldInfo() / modLoad()
vein.mlc.on(topic, cb)</code></pre>
"""),

    dict(path="plugins/ui.html", group="Plugins", title="Lua UI",
         subtitle="Declarative panels rendered inside a Shadow DOM sandbox.",
         tags=["Lua", "UI"],
         body="""
<pre><code>return ui.panel{
  title = "My panel",
  children = {
    ui.text{ value = "Hello from Lua" },
    ui.button{ label = "Refresh", action = "refresh" }
  }
}</code></pre>
<pre><code>export async function activate(vein) {
  vein.ui.onAction(async (action) =&gt; vein.log(action));
  await vein.ui.lua("./ui.lua");
}</code></pre>
"""),

    dict(path="plugins/examples.html", group="Plugins", title="Examples",
         subtitle="From a minimal skeleton to a status panel.",
         tags=["Examples"],
         body="""
<table><thead><tr><th>Folder</th><th>Shows</th></tr></thead><tbody>
<tr><td><code>plugins_examples/template</code></td><td>Minimal skeleton</td></tr>
<tr><td><code>plugins_examples/game-log</code></td><td>Subscribe to game log</td></tr>
<tr><td><code>plugins_examples/lua-ui</code></td><td>Lua UI with actions</td></tr>
<tr><td><code>plugins_examples/mlc-panel</code></td><td>Read MLC state</td></tr>
<tr><td><code>plugins_examples/status-panel</code></td><td>Versions, games, MLC state</td></tr>
</tbody></table>
"""),

    dict(path="plugins/debugging.html", group="Plugins", title="Debugging",
         subtitle="Logs, hot reload and permission errors.",
         tags=["Debugging"],
         body="""
<ul><li>Logs: <code>VeinLauncher/log/plugin-YYYY-MM-DD.log</code>.</li>
<li>Enable, disable or reload from the plugins page.</li>
<li>Self-test: <code>python tools/plugin_selftest.py</code>.</li></ul>
"""),

    dict(path="mlc/overview.html", group="MLC", title="MLC overview",
         subtitle="Drive vanilla Minecraft without installing a mod.",
         tags=["MLC", "Vanilla"],
         body="""
<p>MLC attaches a ~5 KB javaagent to vanilla instances and exposes a local JSON port using official mappings.</p>
<p>The master switch defaults to off. While off, every MLC capability is rejected by the backend.</p>
"""),

    dict(path="mlc/how-it-works.html", group="MLC", title="How it works",
         subtitle="Agent generation, injection and polling.",
         tags=["Agent", "Mappings"],
         body="""
<pre><code>Launcher                              Game process
MlcService  ←── JSON lines ──→  vein-agent.jar (premain)</code></pre>
<p>The agent is generated by <code>tools/build_vanilla_agent.py</code> from official Mojang mappings.</p>
<pre><code>-javaagent:&lt;data&gt;/agent/vein-agent-1.20.1.jar
-Dvein.agent.port=25566</code></pre>
"""),

    dict(path="mlc/protocol.html", group="MLC", title="Protocol",
         subtitle="One JSON request per line, one JSON response per line.",
         tags=["Protocol"],
         body="""
<table><thead><tr><th>Command</th><th>Request</th><th>Response</th></tr></thead><tbody>
<tr><td>ping</td><td><code>{"cmd":"ping"}</code></td><td><code>{"ok":true}</code></td></tr>
<tr><td>state</td><td><code>{"cmd":"state"}</code></td><td><code>{"inGame":true,"player":{…}}</code></td></tr>
<tr><td>chat</td><td><code>{"cmd":"chat","text":"/time set day"}</code></td><td><code>{"ok":true}</code></td></tr>
</tbody></table>
"""),

    dict(path="mlc/events.html", group="MLC", title="Events",
         subtitle="State is diffed every second; changes emit events.",
         tags=["Events"],
         body="""
<table><thead><tr><th>Event</th><th>Trigger</th></tr></thead><tbody>
<tr><td><code>mlc.agent.game.enter</code></td><td>World entered</td></tr>
<tr><td><code>mlc.agent.game.leave</code></td><td>Back to menu / exit</td></tr>
<tr><td><code>mlc.agent.player.dimension</code></td><td>Dimension change</td></tr>
<tr><td><code>mlc.agent.player.death</code></td><td>Health drops to zero</td></tr>
</tbody></table>
"""),

    dict(path="mlc/troubleshooting.html", group="MLC", title="MLC troubleshooting",
         subtitle="Not connected, commands not sending, port conflicts.",
         tags=["Troubleshooting"],
         body="""
<ol><li>Check the master switch.</li>
<li>Use a vanilla instance (Fabric/Forge do not attach the agent).</li>
<li>Make sure you are in a world.</li>
<li>Read <code>log/mlc-*.log</code>.</li></ol>
"""),

    dict(path="reference/config.html", group="Reference", title="Configuration",
         subtitle="Main fields in config.json.",
         tags=["Config"],
         body="""
<pre><code>{
  "launch": { "memory_min": 512, "memory_max": 4096 },
  "download": { "source": "auto" },
  "ui": { "language": "zh_CN", "theme": "light" }
}</code></pre>
"""),

    dict(path="reference/faq.html", group="Reference", title="FAQ",
         subtitle="Answers by symptom.",
         tags=["FAQ"],
         body="""
<h2>Launch</h2>
<h3>ClassNotFoundException</h3><p>The client jar is incomplete — re-run install.</p>
<h3>No window title bar</h3><p>Resolution equals screen size; set 1280×720.</p>
<h2>Skins</h2>
<h3>Skins missing</h3><p>Use LittleSkin, or a Fabric instance with CustomSkinLoader.</p>
<h2>Commands</h2>
<h3>Ctrl+Alt+Q does nothing</h3><p>The hotkey is taken; rebind it in the tools page.</p>
"""),

    dict(path="reference/glossary.html", group="Reference", title="Glossary",
         subtitle="Terms used across the project.",
         tags=["Glossary"],
         body="""
<table><thead><tr><th>Term</th><th>Meaning</th></tr></thead><tbody>
<tr><td>Instance</td><td>Isolated game folder</td></tr>
<tr><td>MLC</td><td>Minecraft Launcher Control</td></tr>
<tr><td>Agent</td><td>5 KB javaagent attached to the game</td></tr>
<tr><td>Bridge</td><td>RPC layer between UI and Python</td></tr>
</tbody></table>
"""),

    dict(path="reference/security.html", group="Reference", title="Security & privacy",
         subtitle="Where data lives and what the launcher connects to.",
         tags=["Security", "Privacy"],
         body="""
<h2>Local data</h2>
<p>Tokens, config and logs stay in <code>VeinLauncher/</code>.</p>
<h2>Network</h2>
<ul><li>Versions and assets: BMCLAPI / Mojang</li><li>Skins: LittleSkin / authlib-injector</li>
<li>Announcements and updates: GitHub</li><li>Java: Adoptium</li></ul>
<div class="callout warn"><b>MLC port:</b> bound to 127.0.0.1 only.</div>
"""),
]
