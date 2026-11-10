"""前端：插件页 Node 一键安装、下载页原版装 mod 引导 + loader 跟随实例。"""

from pathlib import Path

web = Path(r"Z:\Vein Launche\vein_launcher\presentation\webui\src")

# ---------------- 插件页
p = web / "pages.tsx"
t = p.read_text(encoding="utf-8")

if "installNode" not in t:
    t = t.replace("  const [pendingGrant, setPendingGrant] = useState<string>('');",
                  "  const [pendingGrant, setPendingGrant] = useState<string>('');\n  const [nodeBusy, setNodeBusy] = useState(false);", 1)

    anchor = """  return (
    <>
      <ThreePane"""
    assert anchor in t
    t = t.replace(anchor, """  const installNode = async () => {
    setNodeBusy(true);
    try {
      const res = await rpc<{ path: string; status: { version?: string } }>('plugins.installNode');
      notify(`Node.js 已安装：${res.status?.version || res.path}`);
      await refresh();
    } catch (err) {
      notify(`Node.js 安装失败：${(err as Error).message}`);
    } finally {
      setNodeBusy(false);
    }
  };

  return (
    <>
      {!state.host.node && (
        <div className="node-banner">
          <div className="node-banner-text">
            <b>Node.js 未安装，插件功能不可用</b>
            <p>
              插件宿主需要 Node.js 18+。点右侧一键安装：会从 nodejs.org 下载官方 LTS
              并解压到 VeinLauncher/runtime/node，不需要管理员权限，也不会改系统环境变量。
            </p>
          </div>
          <button className="btn primary" onClick={installNode} disabled={nodeBusy}>
            {nodeBusy ? '正在安装 Node.js…' : '一键安装 Node.js'}
          </button>
        </div>
      )}
      <ThreePane""", 1)
    p.write_text(t, encoding="utf-8")
    print("plugins page install banner")

# ---------------- 下载页
d = web / "downloadPage.tsx"
t = d.read_text(encoding="utf-8")

if "needsLoader" not in t:
    t = t.replace("""  useEffect(() => {
    if (installed.length && !targetInstance) setTargetInstance(installed[0].id);
  }, [installed, targetInstance]);""",
"""  useEffect(() => {
    if (installed.length && !targetInstance) setTargetInstance(installed[0].id);
  }, [installed, targetInstance]);

  // 选中实例后自动识别加载器，模组搜索/安装都按它过滤
  useEffect(() => {
    const id = (targetInstance || '').toLowerCase();
    const detected = ['fabric', 'quilt', 'neoforge', 'forge'].find((k) => id.includes(k)) || '';
    setLoader(detected);
  }, [targetInstance]);""", 1)

    old = """    try {
      await rpc('mods.install', [item.slug, instance, projectType || 'mod', loader]);
      notify(`${item.title} installed to ${instance}`);
      await onInstalled();
      setDetail(null);
    } catch (err) {"""
    new = """    try {
      const res = await rpc<{ needsLoader?: boolean; mcVersion?: string; justInstalled?: boolean }>(
        'mods.install',
        [item.slug, instance, projectType || 'mod', loader]
      );
      if (res?.needsLoader) {
        const mc = res.mcVersion || instance;
        const ok = window.confirm(
          `实例 ${instance} 是原版，没有模组加载器，模组不会被加载。\\n\\n是否创建 Fabric ${mc} 实例，并把 ${item.title} 装进去？`
        );
        if (!ok) {
          notify('已取消：原版实例无法加载模组');
          return;
        }
        const created = await rpc<{ version_id?: string }>('versions.install', [mc, 'fabric', '', '']);
        const target = created?.version_id || `fabric-${mc}`;
        await rpc('mods.install', [item.slug, target, projectType || 'mod', 'fabric']);
        notify(`已创建 ${target} 并安装 ${item.title}`);
        await onInstalled();
        setTargetInstance(target);
      } else {
        notify(`${item.title} installed to ${instance}`);
      }
      await onInstalled();
      setDetail(null);
    } catch (err) {"""
    assert old in t
    t = t.replace(old, new, 1)
    d.write_text(t, encoding="utf-8")
    print("download page loader flow")

# ---------------- 样式
css = Path(r"Z:\Vein Launche\vein_launcher\presentation\webui\src\styles.css")
c = css.read_text(encoding="utf-8")
if ".node-banner" not in c:
    c += """

/* 0.5.1 插件页：Node.js 安装提示 */
.node-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 18px;
  margin: 14px 22px 0; padding: 16px 18px;
  border: 1px solid color-mix(in srgb, var(--accent) 35%, var(--line));
  border-radius: var(--radius); background: var(--accent-faint);
}
.node-banner-text b { display: block; margin-bottom: 4px; }
.node-banner-text p { margin: 0; color: var(--text-2); font-size: 12.5px; line-height: 1.6; max-width: 720px; }
.node-banner .btn { flex: none; }
@media (max-width: 760px) { .node-banner { flex-direction: column; align-items: flex-start; } }
"""
    css.write_text(c, encoding="utf-8")
    print("node banner css")
