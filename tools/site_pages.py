"""根页面内容（v7）：关于/下载/社区/路线图/安全/贡献/展示墙/许可/FAQ/文档入口。"""

ZIP = "https://github.com/zhanjhn-studio/vein_launcher/releases/download/v0.5.0/VeinLauncher-0.5.0-win64.zip"
REL = "https://github.com/zhanjhn-studio/vein_launcher/releases/tag/v0.5.0"
GH = "https://github.com/zhanjhn-studio/vein_launcher"
ISSUES = f"{GH}/issues"
DISCUSS = f"{GH}/discussions"
SHA = "1F3FDBFEB2B3E2E612EA6DC94B27570810CCD72F1F70F71C42ACA665EE8A176C"

DOWNLOAD_ZH = f"""
<h1>下载</h1>
<p class="lead">Windows 10/11 x64 · 便携免安装 · 解压即用。需要 Java 时启动器会自动下载。</p>
<div class="download-card" style="margin:30px 0 46px;">
  <div>
    <span class="eyebrow">Latest · 2026-11-08</span>
    <h2>Vein Launcher 0.5.0</h2>
    <p>MLC 原版控制、附魔书指令速查、插件能力补全、总开关硬拦截。</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <a class="btn primary lg" href="{ZIP}">下载 zip（199 MB）</a>
      <a class="btn lg" href="{REL}" target="_blank" rel="noopener">Release 说明</a>
      <a class="btn ghost lg" href="../changelog.html">更新日志</a>
    </div>
  </div>
  <div class="role-visual"><img src="../assets/shot-download.png" alt="下载页" /></div>
</div>
<div class="meta-grid">
  <div><b>Windows 10 / 11 x64</b><span>支持平台</span></div>
  <div><b>199 MB</b><span>压缩包大小</span></div>
  <div><b>2026-11-08</b><span>更新时间</span></div>
  <div><b>v0.5.0</b><span>当前版本</span></div>
</div>
<h2>SHA-256 校验</h2>
<pre><code>{SHA}</code></pre>
<p>下载后可执行 <code>certutil -hashfile VeinLauncher-0.5.0-win64.zip SHA256</code> 比对。</p>
<h2>历史版本</h2>
<table><thead><tr><th>版本</th><th>日期</th><th>说明</th><th>下载</th></tr></thead><tbody>
<tr><td>v0.5.0</td><td>2026-11-08</td><td>MLC、指令速查、插件能力</td><td><a href="{ZIP}">zip</a></td></tr>
<tr><td>v0.1.0</td><td>2026-10-31</td><td>首个公开版本</td><td><a href="{GH}/releases/tag/v0.1.0" target="_blank" rel="noopener">Release</a></td></tr>
</tbody></table>
<h2>升级说明</h2>
<ul><li>关闭启动器与游戏后，用新目录覆盖旧目录；<code>VeinLauncher/</code> 数据目录保持不动。</li>
<li>升级不会删除实例、存档、配置与插件。</li>
<li>跨大版本升级前建议备份 <code>config/</code>。</li></ul>
"""

DOWNLOAD_EN = f"""
<h1>Download</h1>
<p class="lead">Windows 10/11 x64 · portable · unzip and run. Java is downloaded automatically when needed.</p>
<div class="download-card" style="margin:30px 0 46px;">
  <div>
    <span class="eyebrow">Latest · 2026-11-08</span>
    <h2>Vein Launcher 0.5.0</h2>
    <p>MLC vanilla control, enchanted-book command palette, plugin capabilities, hard master switch.</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <a class="btn primary lg" href="{ZIP}">Download zip (199 MB)</a>
      <a class="btn lg" href="{REL}" target="_blank" rel="noopener">Release notes</a>
      <a class="btn ghost lg" href="../changelog.html">Changelog</a>
    </div>
  </div>
  <div class="role-visual"><img src="../assets/shot-download.png" alt="Download page" /></div>
</div>
<div class="meta-grid">
  <div><b>Windows 10 / 11 x64</b><span>Platform</span></div>
  <div><b>199 MB</b><span>Archive size</span></div>
  <div><b>2026-11-08</b><span>Updated</span></div>
  <div><b>v0.5.0</b><span>Version</span></div>
</div>
<h2>SHA-256</h2>
<pre><code>{SHA}</code></pre>
<h2>Previous versions</h2>
<table><thead><tr><th>Version</th><th>Date</th><th>Notes</th><th>Download</th></tr></thead><tbody>
<tr><td>v0.5.0</td><td>2026-11-08</td><td>MLC, command palette, plugin capabilities</td><td><a href="{ZIP}">zip</a></td></tr>
<tr><td>v0.1.0</td><td>2026-10-31</td><td>First public release</td><td><a href="{GH}/releases/tag/v0.1.0" target="_blank" rel="noopener">Release</a></td></tr>
</tbody></table>
<h2>Upgrading</h2>
<ul><li>Close the launcher and the game, replace the app folder; keep <code>VeinLauncher/</code>.</li>
<li>Instances, saves, config and plugins are preserved.</li>
<li>Back up <code>config/</code> before a major upgrade.</li></ul>
"""

ROADMAP_ZH = """
<h1>路线图</h1>
<p class="lead">项目往哪走：正在做、接下来、以后可能做，以及明确不做的事。</p>
<h2>正在做</h2>
<ul><li>MLC 稳定性：更多游戏版本的 agent 生成与状态字段</li>
<li>插件能力：事件订阅细化、UI 组件补全</li>
<li>下载链路：更多镜像与失败重试策略</li></ul>
<h2>接下来</h2>
<ul><li>MC2 世界数据分析面板（种子、群系、结构）</li>
<li>联机模块占位转为可用</li>
<li>文档站全文搜索与版本归档</li></ul>
<h2>以后可能做</h2>
<ul><li>Modrinth / CurseForge 更完整的整合包安装</li>
<li>Linux 与 macOS 的可行性验证</li></ul>
<h2>明确不做</h2>
<ul><li>绕过正版验证的功能</li>
<li>内置服务器托管、外挂或自动打怪</li>
<li>把账号令牌上传到任何服务器</li></ul>
"""

ROADMAP_EN = """
<h1>Roadmap</h1>
<p class="lead">Where the project is going: now, next, later, and deliberately out of scope.</p>
<h2>Now</h2>
<ul><li>MLC stability: agents and state fields for more game versions</li>
<li>Plugin capabilities: finer event subscriptions, more UI components</li>
<li>Download pipeline: more mirrors and retry strategies</li></ul>
<h2>Next</h2>
<ul><li>MC2 world analysis panel (seed, biomes, structures)</li>
<li>Turn the multiplayer placeholder into a real screen</li>
<li>Docs search and versioned archives</li></ul>
<h2>Later</h2>
<ul><li>Fuller modpack installation from Modrinth / CurseForge</li>
<li>Feasibility checks for Linux and macOS</li></ul>
<h2>Out of scope</h2>
<ul><li>Bypassing account authentication</li>
<li>Built-in server hosting, cheating tools or automation</li>
<li>Uploading account tokens anywhere</li></ul>
"""

SECURITY_ZH = f"""
<h1>安全</h1>
<p class="lead">漏洞上报方式、支持范围与安全策略。</p>
<h2>上报漏洞</h2>
<p>请不要公开提交安全 issue，改用 GitHub 私密漏洞报告，或在 issue 中标注 <code>[security]</code> 并避免贴出可复现的敏感细节。</p>
<ul><li><a href="{GH}/security/advisories/new" target="_blank" rel="noopener">私密上报（GitHub Security Advisory）</a></li>
<li><a href="{ISSUES}" target="_blank" rel="noopener">普通 issue（非敏感问题）</a></li></ul>
<h2>支持范围</h2>
<table><thead><tr><th>版本</th><th>状态</th></tr></thead><tbody>
<tr><td>0.5.x</td><td>接收安全修复</td></tr>
<tr><td>&lt; 0.5</td><td>仅建议升级</td></tr>
</tbody></table>
<h2>安全边界</h2>
<ul><li>账号令牌、配置与日志只保存在本地 <code>VeinLauncher/</code>。</li>
<li>MLC agent 只监听 <code>127.0.0.1</code>，无远程访问。</li>
<li>插件运行在独立 Node 进程，权限与路径双重校验。</li></ul>
"""

SECURITY_EN = f"""
<h1>Security</h1>
<p class="lead">How to report vulnerabilities, supported versions and our security model.</p>
<h2>Report</h2>
<p>Please do not file public security issues. Use private vulnerability reporting on GitHub, or mark an issue <code>[security]</code> without sensitive reproduction details.</p>
<ul><li><a href="{GH}/security/advisories/new" target="_blank" rel="noopener">Private report</a></li>
<li><a href="{ISSUES}" target="_blank" rel="noopener">Normal issues</a></li></ul>
<h2>Supported versions</h2>
<table><thead><tr><th>Version</th><th>Status</th></tr></thead><tbody>
<tr><td>0.5.x</td><td>Receives security fixes</td></tr>
<tr><td>&lt; 0.5</td><td>Upgrade recommended</td></tr>
</tbody></table>
<h2>Model</h2>
<ul><li>Tokens, config and logs stay in local <code>VeinLauncher/</code>.</li>
<li>The MLC agent only listens on <code>127.0.0.1</code>.</li>
<li>Plugins run in isolated Node processes with permission and path checks.</li></ul>
"""

CONTRIBUTE_ZH = f"""
<h1>贡献指南</h1>
<p class="lead">想参与开发、提交插件或改进文档，从这里开始。</p>
<h2>提交代码</h2>
<ol class="steps"><li><h3>Fork 并开分支</h3><p>从 <code>main</code> 切一个描述性的分支。</p></li>
<li><h3>改完跑测试</h3><p><code>python -m unittest discover -s tests</code>；改前端需重新构建 <code>dist</code>。</p></li>
<li><h3>提 PR</h3><p>说明动机、改动点与验证方式；关联 issue。</p></li></ol>
<h2>代码规范</h2>
<ul><li>提交信息使用 Conventional Commits（<code>feat</code> / <code>fix</code> / <code>docs</code> / <code>refactor</code>）。</li>
<li>分层边界不能破：UI 不直接调底层 IO，跨层走事件总线。</li>
<li>新增 RPC、服务或插件能力时，补对应文档与测试。</li></ul>
<h2>提交插件</h2>
<p>插件放在 <code>VeinLauncher/plugin/</code>，清单需带 <code>vein</code> 字段。想收录到展示墙，请开 issue 附仓库地址与截图。</p>
<h2>改文档</h2>
<p>文档由生成器产出：改 <code>tools/site_content*.py</code> 后运行 <code>python tools/gen_site.py</code>。</p>
"""

CONTRIBUTE_EN = f"""
<h1>Contributing</h1>
<p class="lead">Code, plugins and documentation contributions all start here.</p>
<h2>Pull requests</h2>
<ol class="steps"><li><h3>Fork and branch</h3><p>Branch from <code>main</code> with a descriptive name.</p></li>
<li><h3>Test</h3><p><code>python -m unittest discover -s tests</code>; rebuild <code>dist</code> if you touched the frontend.</p></li>
<li><h3>Open a PR</h3><p>Explain motivation, changes and how you verified them.</p></li></ol>
<h2>Style</h2>
<ul><li>Conventional Commits (<code>feat</code> / <code>fix</code> / <code>docs</code> / <code>refactor</code>).</li>
<li>Keep layer boundaries: UI never calls IO directly; cross-layer via the event bus.</li>
<li>Add tests and docs for new RPCs, services or plugin capabilities.</li></ul>
<h2>Plugins</h2>
<p>Plugins live in <code>VeinLauncher/plugin/</code> with a <code>vein</code> manifest field. To be featured in Showcase, open an issue with the repository and screenshots.</p>
"""

SHOWCASE_ZH = f"""
<h1>展示墙</h1>
<p class="lead">用 Vein Launcher 做的插件、整合与作品。</p>
<div class="callout tip"><b>还在征集：</b>提交你的作品请开 <a href="{ISSUES}" target="_blank" rel="noopener">issue</a>，附仓库地址、截图与一句话介绍。</div>
<div class="grid grid-3" style="margin-top:24px;">
  <div class="card"><h3>status-panel</h3><p>官方示例插件：版本、实例、运行中游戏与 MLC 状态面板。</p></div>
  <div class="card"><h3>lua-ui</h3><p>官方示例插件：Lua 声明式面板与按钮动作。</p></div>
  <div class="card"><h3>你的作品</h3><p>等待第一位社区作者。</p></div>
</div>
"""

SHOWCASE_EN = f"""
<h1>Showcase</h1>
<p class="lead">Plugins, packs and projects built with Vein Launcher.</p>
<div class="callout tip"><b>Open call:</b> open an <a href="{ISSUES}" target="_blank" rel="noopener">issue</a> with a repository, screenshots and a one-line description.</div>
<div class="grid grid-3" style="margin-top:24px;">
  <div class="card"><h3>status-panel</h3><p>Official example: versions, instances, running games and MLC state.</p></div>
  <div class="card"><h3>lua-ui</h3><p>Official example: declarative Lua panels with button actions.</p></div>
  <div class="card"><h3>Your work</h3><p>Waiting for the first community author.</p></div>
</div>
"""

COMMUNITY_ZH = f"""
<h1>社区</h1>
<p class="lead">反馈、讨论与贡献的入口。</p>
<div class="grid grid-2" style="margin-top:26px;">
  <a class="card" href="{GH}" target="_blank" rel="noopener"><h3>GitHub 仓库 →</h3><p>源码、提交记录与版本发布。</p></a>
  <a class="card" href="{ISSUES}" target="_blank" rel="noopener"><h3>Issue 反馈 →</h3><p>报告 BUG、提出需求；附日志与复现步骤。</p></a>
  <a class="card" href="{DISCUSS}" target="_blank" rel="noopener"><h3>Discussions 讨论 →</h3><p>使用交流、插件分享与想法讨论。</p></a>
  <a class="card" href="../contribute.html"><h3>参与贡献 →</h3><p>代码规范、PR 流程与插件提交。</p></a>
</div>
<h2>提问前</h2>
<ul><li>先在 <a href="../docs.html">文档</a> 与 <a href="../faq.html">FAQ</a> 搜索。</li>
<li>反馈时附上版本号、日志片段与复现步骤。</li>
<li>安全问题请走私密渠道，见 <a href="../security.html">安全页</a>。</li></ul>
"""

COMMUNITY_EN = f"""
<h1>Community</h1>
<p class="lead">Where to report, discuss and contribute.</p>
<div class="grid grid-2" style="margin-top:26px;">
  <a class="card" href="{GH}" target="_blank" rel="noopener"><h3>GitHub →</h3><p>Source, commits and releases.</p></a>
  <a class="card" href="{ISSUES}" target="_blank" rel="noopener"><h3>Issues →</h3><p>Bug reports and feature requests; include logs and steps.</p></a>
  <a class="card" href="{DISCUSS}" target="_blank" rel="noopener"><h3>Discussions →</h3><p>Usage questions, plugin sharing and ideas.</p></a>
  <a class="card" href="../contribute.html"><h3>Contribute →</h3><p>Code style, PR flow and plugin submissions.</p></a>
</div>
"""

ABOUT_ZH = f"""
<h1>关于</h1>
<p class="lead">Vein Launcher 由 zhanjhn 工作室开发与维护。</p>
<p>项目初衷很简单：把「启动 Minecraft」做成一件不折腾的事，同时给愿意扩展的人留出足够的空间——插件宿主、JSON-RPC 桥与 MLC 控制层都是开放的。</p>
<h2>工作室</h2>
<table><thead><tr><th>项</th><th>信息</th></tr></thead><tbody>
<tr><td>工作室</td><td>zhanjhn studio</td></tr>
<tr><td>开源协议</td><td>MIT</td></tr>
<tr><td>仓库</td><td><a href="{GH}" target="_blank" rel="noopener">github.com/zhanjhn-studio/vein_launcher</a></td></tr>
<tr><td>当前版本</td><td>0.5.0</td></tr>
</tbody></table>
<h2>联系</h2>
<ul><li><a href="{ISSUES}" target="_blank" rel="noopener">Issue</a></li>
<li><a href="{DISCUSS}" target="_blank" rel="noopener">Discussions</a></li></ul>
"""

ABOUT_EN = f"""
<h1>About</h1>
<p class="lead">Vein Launcher is built and maintained by zhanjhn studio.</p>
<p>The idea is simple: make launching Minecraft painless, while leaving room for people who want to extend it — the plugin host, JSON-RPC bridge and MLC layer are all open.</p>
<h2>Studio</h2>
<table><thead><tr><th>Item</th><th>Info</th></tr></thead><tbody>
<tr><td>Studio</td><td>zhanjhn studio</td></tr>
<tr><td>License</td><td>MIT</td></tr>
<tr><td>Repository</td><td><a href="{GH}" target="_blank" rel="noopener">github.com/zhanjhn-studio/vein_launcher</a></td></tr>
<tr><td>Version</td><td>0.5.0</td></tr>
</tbody></table>
"""

PRIVACY_ZH = f"""
<h1>隐私</h1>
<p class="lead">本地优先：账号令牌、配置、日志都不会上传。</p>
<h2>联网请求</h2>
<ul><li>版本清单 / 客户端 / 资源：BMCLAPI 与 Mojang 官方源</li>
<li>皮肤：LittleSkin / authlib-injector</li>
<li>公告与更新：GitHub、公告站</li>
<li>Java：Adoptium</li></ul>
<h2>本地存储</h2>
<p>所有数据位于 exe 同级 <code>VeinLauncher/</code>，可整体删除。</p>
<h2>第三方</h2>
<p>启动器会把必要的请求发往上述服务；这些服务各自的隐私政策独立于本项目。</p>
"""

PRIVACY_EN = f"""
<h1>Privacy</h1>
<p class="lead">Local first: tokens, config and logs never leave your machine.</p>
<h2>Network</h2>
<ul><li>Versions and assets: BMCLAPI / Mojang</li><li>Skins: LittleSkin / authlib-injector</li>
<li>Announcements and updates: GitHub</li><li>Java: Adoptium</li></ul>
<h2>Storage</h2>
<p>Everything lives in <code>VeinLauncher/</code> next to the exe.</p>
"""

LICENSE_ZH = """
<h1>许可证</h1>
<p class="lead">Vein Launcher 以 MIT 协议开源。</p>
<pre><code>MIT License

Copyright (c) 2026 zhanjhn studio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</code></pre>
"""

LICENSE_EN = LICENSE_ZH.replace("<h1>许可证</h1>", "<h1>License</h1>").replace(
    "Vein Launcher 以 MIT 协议开源。", "Vein Launcher is open source under the MIT license."
)
