"""首页内容（v6：动效 + 更多面向用户的板块）。"""

ZIP = "https://vl.zhanjhn.cn/downloads/VeinLauncher-0.5.1-win64.zip"
GH = "https://github.com/zhanjhn-studio/vein_launcher"

HOME_ZH = f"""<main>
  <section class="hero hero-anim">
    <div class="hero-aurora" aria-hidden="true">
      <span class="a1"></span><span class="a2"></span><span class="a3"></span>
    </div>
    <div class="wrap hero-grid">
      <div class="hero-copy">
        <span class="eyebrow">Minecraft Java Edition · Windows</span>
        <h1>Vein，<br /><span class="grad-text">掌控 Minecraft</span>
          <em>安装、管理、启动，一步到位；还能在不装 mod 的原版里直接执行指令。</em>
        </h1>
        <p class="lead">面向 Minecraft Java 版的便携启动器：镜像优先下载、真实例管理、LittleSkin 皮肤、沙箱插件宿主，以及 MLC 控制层。</p>
        <div class="cta-row">
          <a class="btn primary lg shine" href="{ZIP}">下载 v0.5.1</a>
          <a class="btn lg" href="docs.html" data-order="1">阅读文档</a>
          <a class="btn ghost lg" href="{GH}" target="_blank" rel="noopener">GitHub</a>
        </div>
        <div class="quickjump">
          <a href="docs.html" data-order="1">文档</a>
          <a href="faq.html">FAQ</a>
          <a href="download.html" data-order="2">下载</a>
          <a href="{GH}" target="_blank" rel="noopener">GitHub</a>
        </div>
        <div class="stat-row">
          <div class="stat"><b data-count="51">0</b><span>项单元测试</span></div>
          <div class="stat"><b data-count="4">0</b><span>种加载器</span></div>
          <div class="stat"><b data-count="2">0</b><span>种界面语言</span></div>
          <div class="stat"><b data-count="0">0</b><span>写入注册表</span></div>
        </div>
      </div>
      <div class="hero-visual" data-parallax="0.03">
        <span class="float-chip fc1">MLC 原版直连</span>
        <span class="float-chip fc2">附魔书指令速查</span>
        <div class="shot"><img src="assets/shot-launch.png" alt="启动页" /></div>
      </div>
    </div>
  </section>

  <section class="feature-band">
    <div class="wrap feature-grid">
      <article class="feature" data-tilt><h3>原版直连（MLC）</h3><p>5 KB javaagent + 官方映射，不装 mod 也能读状态、发指令、收事件。</p></article>
      <article class="feature" data-tilt><h3>附魔书指令速查</h3><p>Ctrl+Alt+Q 打开，Enter 直接发送进游戏，失败自动复制。</p></article>
      <article class="feature" data-tilt><h3>沙箱插件宿主</h3><p>独立 Node 进程、权限声明、Lua UI，越权直接拒绝。</p></article>
      <article class="feature" data-tilt><h3>皮肤直接进游戏</h3><p>LittleSkin 走 authlib-injector；本地皮肤配 Fabric 注入。</p></article>
      <article class="feature" data-tilt><h3>多实例并行</h3><p>每个实例独立进程与端口，同时开多个游戏互不干扰。</p></article>
      <article class="feature" data-tilt><h3>中英双语</h3><p>界面、文档、公告都支持简体中文与 English。</p></article>
    </div>
  </section>

  <section class="section steps-sec">
    <div class="wrap">
      <div class="section-head reveal"><span class="eyebrow">Get started</span><h2>三步就能开始</h2><p>不折腾环境，不用装依赖。</p></div>
      <div class="step-grid">
        <div class="step-card reveal d1"><b>01</b><h3>下载解压</h3><p>取一个 zip，解压到任意目录，双击 exe。</p></div>
        <div class="step-card reveal d2"><b>02</b><h3>安装版本</h3><p>选原版或加载器，镜像优先下载，断点续传。</p></div>
        <div class="step-card reveal d3"><b>03</b><h3>开玩</h3><p>选账号、点启动；Ctrl+Alt+Q 直接发指令。</p></div>
      </div>
    </div>
  </section>

  <section class="marquee-sec">
    <div class="marquee">
      <div class="marquee-track">
        <span>Vanilla</span><span>Fabric</span><span>Forge</span><span>Quilt</span><span>NeoForge</span>
        <span>LittleSkin</span><span>authlib-injector</span><span>CustomSkinLoader</span><span>BMCLAPI</span>
        <span>Vanilla</span><span>Fabric</span><span>Forge</span><span>Quilt</span><span>NeoForge</span>
        <span>LittleSkin</span><span>authlib-injector</span><span>CustomSkinLoader</span><span>BMCLAPI</span>
      </div>
    </div>
  </section>

  <section class="identity"><div class="wrap">
    <div class="identity-head reveal"><span class="eyebrow">Choose your path</span><h2>你是来玩的，还是来造的？</h2><p>三种入口，都有可直接复制的命令与完整文档。</p></div>
    <div class="role-row reveal"><div><div class="role-kicker">01 · For players</div><h3>我只想玩游戏</h3>
      <p>下载、选版本、进游戏。皮肤、附魔书指令速查、多实例，都在五分钟里。</p>
      <ul class="role-points"><li>附魔书风格指令速查，回车直接发进游戏</li><li>LittleSkin 账号皮肤直接进游戏</li><li>多实例并行，每实例独立进程与端口</li></ul>
      <a class="btn primary" href="docs.html" data-order="1">玩家文档 →</a></div>
      <div class="role-visual"><img src="assets/shot-launch.png" alt="" /></div></div>
    <div class="role-row reveal"><div><div class="role-kicker">02 · For builders</div><h3>我要改它 / 扩展它</h3>
      <p>五层架构、JSON-RPC 桥、沙箱插件宿主、Lua UI 与 MLC 控制层，全部开放。</p>
      <ul class="role-points"><li>严格分层 + 全局事件总线</li><li>Bridge 注册一个方法就能扩展一个 RPC</li><li>构建、测试、打包流程齐全</li></ul>
      <a class="btn primary" href="docs.html" data-order="1">开发文档 →</a></div>
      <div class="role-visual"><img src="assets/shot-tools.png" alt="" /></div></div>
    <div class="role-row reveal"><div><div class="role-kicker">03 · For plugin devs</div><h3>我要写插件</h3>
      <p>Node 独立进程、权限沙箱、Lua UI、示例与调试。</p>
      <ul class="role-points"><li>package.json 声明权限，越权直接拒绝</li><li>MLC 事件、运行中游戏、实例列表都能读</li><li>自带 status-panel 示例，抄一个就能跑</li></ul>
      <a class="btn primary" href="docs.html" data-order="1">插件文档 →</a></div>
      <div class="role-visual"><img src="assets/shot-palette.png" alt="" /></div></div>
  </div></section>

  <section class="section section-soft"><div class="wrap">
    <div class="section-head reveal"><span class="eyebrow">Screenshots</span><h2>0.5.1 长什么样</h2></div>
    <div class="gallery">
      <figure class="reveal d1"><img src="assets/shot-launch.png" alt="" /><figcaption>启动页</figcaption></figure>
      <figure class="reveal d2"><img src="assets/shot-download.png" alt="" /><figcaption>下载页</figcaption></figure>
      <figure class="reveal d3"><img src="assets/shot-skins.png" alt="" /><figcaption>皮肤</figcaption></figure>
      <figure class="reveal d1"><img src="assets/shot-mlc-switch.png" alt="" /><figcaption>MLC 总开关</figcaption></figure>
      <figure class="reveal d2"><img src="assets/shot-palette.png" alt="" /><figcaption>指令速查</figcaption></figure>
      <figure class="reveal d3"><img src="assets/shot-tools.png" alt="" /><figcaption>工具箱</figcaption></figure>
    </div>
  </div></section>

  <section class="section faq-sec"><div class="wrap">
    <div class="section-head reveal"><span class="eyebrow">FAQ</span><h2>常见问题</h2></div>
    <div class="faq-grid">
      <details class="faq reveal d1"><summary>没有安装包，怎么装？</summary><p>下载 zip 解压即用，数据目录在 exe 同级；删除目录就是卸载。</p></details>
      <details class="faq reveal d2"><summary>需要自己装 Java 吗？</summary><p>不用。启动器会检测本机 Java，缺了会自动下载对应大版本。</p></details>
      <details class="faq reveal d3"><summary>皮肤为什么不显示？</summary><p>LittleSkin 账号直接启动；本地 PNG 皮肤需要 Fabric + CustomSkinLoader。</p></details>
      <details class="faq reveal d1"><summary>能同时开两个游戏吗？</summary><p>可以，但要用不同实例；同一实例双开会抢存档。</p></details>
    </div>
    <p class="center" style="margin-top:28px;"><a href="docs.html" data-order="1">查看全部文档 →</a></p>
  </div></section>

  <section class="download"><div class="wrap"><div class="download-card">
    <div><span class="eyebrow">Download</span><h2>下载 Windows 版</h2>
      <p>解压即用，不写注册表；删除目录即卸载。需要 Java 时启动器会自动下载。</p>
      <div class="cta-row"><a class="btn primary lg shine" href="{ZIP}">下载 v0.5.1（232 MB）</a><a class="btn lg" href="download.html" data-order="2">全部版本</a></div>
      <div class="download-meta"><span>v0.5.1</span><span>2026-11-09</span><span>Windows 10/11 x64</span><span>SHA-256 BD6ADBC3…BC5E0</span></div>
    </div>
    <div class="role-visual"><img src="assets/shot-download.png" alt="" /></div>
  </div></div></section>
</main>"""

HOME_EN = f"""<main>
  <section class="hero hero-anim">
    <div class="hero-aurora" aria-hidden="true"><span class="a1"></span><span class="a2"></span><span class="a3"></span></div>
    <div class="wrap hero-grid">
      <div class="hero-copy">
        <span class="eyebrow">Minecraft Java Edition · Windows</span>
        <h1>Vein,<br /><span class="grad-text">take control of Minecraft</span>
          <em>Install, manage, launch — and drive vanilla Minecraft without a single mod.</em>
        </h1>
        <p class="lead">A portable launcher for Minecraft Java Edition: mirror-first downloads, real instance management, LittleSkin skins, a sandboxed plugin host and the MLC control layer.</p>
        <div class="cta-row">
          <a class="btn primary lg shine" href="{ZIP}">Download v0.5.1</a>
          <a class="btn lg" href="docs.html" data-order="1">Read the docs</a>
          <a class="btn ghost lg" href="{GH}" target="_blank" rel="noopener">GitHub</a>
        </div>
        <div class="stat-row">
          <div class="stat"><b data-count="51">0</b><span>unit tests</span></div>
          <div class="stat"><b data-count="4">0</b><span>loaders</span></div>
          <div class="stat"><b data-count="2">0</b><span>languages</span></div>
          <div class="stat"><b data-count="0">0</b><span>registry writes</span></div>
        </div>
      </div>
      <div class="hero-visual" data-parallax="0.03">
        <span class="float-chip fc1">Vanilla via MLC</span>
        <span class="float-chip fc2">Command palette</span>
        <div class="shot"><img src="assets/shot-launch.png" alt="Launch page" /></div>
      </div>
    </div>
  </section>

  <section class="feature-band"><div class="wrap feature-grid">
    <article class="feature" data-tilt><h3>Vanilla control (MLC)</h3><p>A 5 KB javaagent plus official mappings: state, commands and events without a mod.</p></article>
    <article class="feature" data-tilt><h3>Command palette</h3><p>Ctrl+Alt+Q, Enter sends straight into the game; failures copy to clipboard.</p></article>
    <article class="feature" data-tilt><h3>Sandboxed plugins</h3><p>Isolated Node processes, declared permissions and Lua UI.</p></article>
    <article class="feature" data-tilt><h3>Skins in game</h3><p>LittleSkin through authlib-injector; local skins with Fabric support.</p></article>
    <article class="feature" data-tilt><h3>Multiple instances</h3><p>Separate processes and agent ports; run several games at once.</p></article>
    <article class="feature" data-tilt><h3>Bilingual</h3><p>Launcher, docs and announcements in English and Simplified Chinese.</p></article>
  </div></section>

  <section class="section steps-sec"><div class="wrap">
    <div class="section-head reveal"><span class="eyebrow">Get started</span><h2>Three steps to play</h2><p>No toolchain to set up.</p></div>
    <div class="step-grid">
      <div class="step-card reveal d1"><b>01</b><h3>Unzip</h3><p>Grab the zip, extract anywhere, run the exe.</p></div>
      <div class="step-card reveal d2"><b>02</b><h3>Install a version</h3><p>Vanilla or a loader; mirrors first, resumable downloads.</p></div>
      <div class="step-card reveal d3"><b>03</b><h3>Play</h3><p>Pick an account, launch, and send commands with Ctrl+Alt+Q.</p></div>
    </div>
  </div></section>

  <section class="marquee-sec"><div class="marquee"><div class="marquee-track">
    <span>Vanilla</span><span>Fabric</span><span>Forge</span><span>Quilt</span><span>NeoForge</span>
    <span>LittleSkin</span><span>authlib-injector</span><span>CustomSkinLoader</span><span>BMCLAPI</span>
    <span>Vanilla</span><span>Fabric</span><span>Forge</span><span>Quilt</span><span>NeoForge</span>
    <span>LittleSkin</span><span>authlib-injector</span><span>CustomSkinLoader</span><span>BMCLAPI</span>
  </div></div></section>

  <section class="identity"><div class="wrap">
    <div class="identity-head reveal"><span class="eyebrow">Choose your path</span><h2>Here to play, or here to build?</h2><p>Three entry points, each with copy-paste commands and complete docs.</p></div>
    <div class="role-row reveal"><div><div class="role-kicker">01 · For players</div><h3>I just want to play</h3>
      <p>Download, pick a version, launch. Skins, the command palette and multi-instance support in five minutes.</p>
      <ul class="role-points"><li>Enchanted-book command palette — Enter sends</li><li>LittleSkin skins work in-game</li><li>Multiple instances with separate ports</li></ul>
      <a class="btn primary" href="docs.html" data-order="1">Player docs →</a></div>
      <div class="role-visual"><img src="assets/shot-launch.png" alt="" /></div></div>
    <div class="role-row reveal"><div><div class="role-kicker">02 · For builders</div><h3>I want to change it</h3>
      <p>Five layers, a JSON-RPC bridge, a sandboxed plugin host, Lua UI and MLC — all open.</p>
      <ul class="role-points"><li>Strict layering + global event bus</li><li>Add one handler to expose one RPC</li><li>Build, test and packaging scripts included</li></ul>
      <a class="btn primary" href="docs.html" data-order="1">Developer docs →</a></div>
      <div class="role-visual"><img src="assets/shot-tools.png" alt="" /></div></div>
    <div class="role-row reveal"><div><div class="role-kicker">03 · For plugin devs</div><h3>I want to write plugins</h3>
      <p>Isolated Node processes, permission sandbox, Lua UI, examples and debugging.</p>
      <ul class="role-points"><li>Permissions declared in package.json</li><li>Read MLC events, running games and instances</li><li>A ready-made status-panel example</li></ul>
      <a class="btn primary" href="docs.html" data-order="1">Plugin docs →</a></div>
      <div class="role-visual"><img src="assets/shot-palette.png" alt="" /></div></div>
  </div></section>

  <section class="section section-soft"><div class="wrap">
    <div class="section-head reveal"><span class="eyebrow">Screenshots</span><h2>What 0.5.1 looks like</h2></div>
    <div class="gallery">
      <figure class="reveal d1"><img src="assets/shot-launch.png" alt="" /><figcaption>Launch</figcaption></figure>
      <figure class="reveal d2"><img src="assets/shot-download.png" alt="" /><figcaption>Download</figcaption></figure>
      <figure class="reveal d3"><img src="assets/shot-skins.png" alt="" /><figcaption>Skins</figcaption></figure>
      <figure class="reveal d1"><img src="assets/shot-mlc-switch.png" alt="" /><figcaption>MLC switch</figcaption></figure>
      <figure class="reveal d2"><img src="assets/shot-palette.png" alt="" /><figcaption>Command palette</figcaption></figure>
      <figure class="reveal d3"><img src="assets/shot-tools.png" alt="" /><figcaption>Tools</figcaption></figure>
    </div>
  </div></section>

  <section class="section faq-sec"><div class="wrap">
    <div class="section-head reveal"><span class="eyebrow">FAQ</span><h2>Common questions</h2></div>
    <div class="faq-grid">
      <details class="faq reveal d1"><summary>Where is the installer?</summary><p>There isn't one: unzip and run. Delete the folder to uninstall.</p></details>
      <details class="faq reveal d2"><summary>Do I need Java?</summary><p>No — the launcher detects or downloads the right runtime.</p></details>
      <details class="faq reveal d3"><summary>Why are skins missing?</summary><p>Use LittleSkin, or a Fabric instance with CustomSkinLoader.</p></details>
      <details class="faq reveal d1"><summary>Can I run two games?</summary><p>Yes, with different instances. The same instance twice will fight over saves.</p></details>
    </div>
    <p class="center" style="margin-top:28px;"><a href="docs.html" data-order="1">Browse all docs →</a></p>
  </div></section>

  <section class="download"><div class="wrap"><div class="download-card">
    <div><span class="eyebrow">Download</span><h2>Download for Windows</h2>
      <p>Unzip and run. No registry writes, delete the folder to uninstall. Java is downloaded automatically if needed.</p>
      <div class="cta-row"><a class="btn primary lg shine" href="{ZIP}">Download v0.5.1 (232 MB)</a><a class="btn lg" href="download.html" data-order="2">All versions</a></div>
      <div class="download-meta"><span>v0.5.1</span><span>2026-11-09</span><span>Windows 10/11 x64</span><span>SHA-256 BD6ADBC3…BC5E0</span></div>
    </div>
    <div class="role-visual"><img src="assets/shot-download.png" alt="" /></div>
  </div></div></section>
</main>"""
