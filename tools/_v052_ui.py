"""下载页：项目版本列表 + 指定版本安装；下载总览页；监视器可点开。"""

from pathlib import Path

src = Path(r"Z:\Vein Launche\vein_launcher\presentation\webui\src")

# ---------------------------------------------------------------- 下载页
p = src / "downloadPage.tsx"
t = p.read_text(encoding="utf-8")

if "ModVersion" not in t:
    t = t.replace("""interface RemoteVersion {
  id: string;
  type?: string;
  release_time?: string;
}""",
"""interface RemoteVersion {
  id: string;
  type?: string;
  release_time?: string;
}

interface ModVersion {
  id: string;
  version_number: string;
  name?: string;
  game_versions: string[];
  loaders: string[];
  date?: string;
  file?: { name: string; size?: number };
}""", 1)

    t = t.replace("  const [modTasks, setModTasks] = useState<{ id: string; title: string; state: string }[]>([]);",
"""  const [modTasks, setModTasks] = useState<{ id: string; title: string; state: string }[]>([]);
  const [projectVersions, setProjectVersions] = useState<ModVersion[]>([]);
  const [pvLoading, setPvLoading] = useState(false);""", 1)

    # 打开详情时拉版本列表
    t = t.replace("""  const installProject = async (item: ModItem) => {""",
"""  const openDetail = async (item: ModItem) => {
    setDetail(item);
    setProjectVersions([]);
    setPvLoading(true);
    try {
      const list = await rpc<ModVersion[]>('mods.versions', [item.slug, mcVersion, loader]);
      setProjectVersions(list);
    } catch (err) {
      notify(`版本列表加载失败：${(err as Error).message}`);
    } finally {
      setPvLoading(false);
    }
  };

  const installProject = async (item: ModItem, versionId = '') => {""", 1)

    t = t.replace("await rpc<{ needsLoader?: boolean; mcVersion?: string; justInstalled?: boolean }>(\n        'mods.install',\n        [item.slug, instance, projectType || 'mod', loader]\n      );",
                  "await rpc<{ needsLoader?: boolean; mcVersion?: string; justInstalled?: boolean }>(\n        'mods.install',\n        [item.slug, instance, projectType || 'mod', loader, versionId]\n      );", 1)

    # 卡片点击改为加载详情
    t = t.replace("onClick={() => setDetail(item)}", "onClick={() => openDetail(item)}", 1)

    # 详情页加版本列表
    old = """          <div className="row-actions">
            <select value={targetInstance} onChange={(e) => setTargetInstance(e.target.value)}>
              {installed.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id}
                </option>
              ))}
            </select>
            <button className="btn primary" onClick={() => installProject(detail)} disabled={busy === 'install'}>
              {busy === 'install' ? 'Installing…' : 'Install'}
            </button>
          </div>"""
    new = """          <div className="row-actions">
            <select value={targetInstance} onChange={(e) => setTargetInstance(e.target.value)}>
              {installed.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id}
                </option>
              ))}
            </select>
            <button
              className="btn primary"
              onClick={() => installProject(detail)}
              disabled={!!installing}
            >
              {installing ? 'Installing…' : 'Install latest'}
            </button>
          </div>

          <div className="version-list">
            <div className="card-title">
              版本列表 {pvLoading ? '· 加载中…' : `· ${projectVersions.length}`}
            </div>
            {projectVersions.length === 0 && !pvLoading && (
              <div className="muted">没有匹配当前版本 / 加载器的文件，可以清空上方筛选再试。</div>
            )}
            {projectVersions.map((v) => (
              <div className="version-row" key={v.id}>
                <div className="version-main">
                  <b>{v.version_number || v.name || v.id}</b>
                  <span className="muted">
                    {(v.game_versions || []).slice(0, 4).join(' / ') || 'any'}
                    {v.loaders?.length ? ` · ${v.loaders.join(' / ')}` : ''}
                    {v.date ? ` · ${v.date.slice(0, 10)}` : ''}
                  </span>
                </div>
                <button
                  className="btn sm"
                  onClick={() => installProject(detail, v.id)}
                  disabled={!!installing}
                >
                  安装
                </button>
              </div>
            ))}
          </div>"""
    assert old in t
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("download page versions")

# ---------------------------------------------------------------- 下载总览页
dl = src / "downloadsPage.tsx"
dl.write_text('''import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';

interface DownloadTask {
  id: string;
  name: string;
  done: number;
  total: number;
  active: boolean;
  error?: string | null;
}

export function DownloadsPage() {
  const [tasks, setTasks] = useState<DownloadTask[]>([]);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const list = await rpc<DownloadTask[]>('downloads.list', []);
        if (alive) setTasks(list);
      } catch {
        /* 忽略单次失败 */
      }
    };
    tick();
    const timer = window.setInterval(tick, 800);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  const active = tasks.filter((t) => t.active);
  const done = tasks.filter((t) => !t.active);

  return (
    <div className="page">
      <div className="page-head">
        <h1>下载</h1>
        <span className="muted">{active.length} 进行中 · {done.length} 已完成</span>
      </div>

      <div className="dl-list">
        {tasks.length === 0 && <div className="empty">还没有下载任务</div>}
        {tasks.map((task) => {
          const pct = task.total > 0 ? Math.min(100, Math.round((task.done / task.total) * 100)) : 0;
          return (
            <div className={`dl-row ${task.active ? 'active' : ''}`} key={task.id}>
              <div className="dl-name" title={task.id}>
                <b>{task.name || task.id}</b>
                <span className="muted">
                  {task.error ? `失败：${task.error}` : task.active ? '下载中' : '已完成'}
                </span>
              </div>
              <div className="dl-bar">
                <i style={{ width: `${Math.max(pct, task.active ? 2 : 0)}%` }} />
              </div>
              <span className="dl-pct">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
''', encoding="utf-8")
print("downloads page")

# ---------------------------------------------------------------- App 路由
app = src / "App.tsx"
t = app.read_text(encoding="utf-8")
if "DownloadsPage" not in t:
    t = t.replace("  PluginsPage,", "  PluginsPage,\n", 1)
    t = t.replace("} from './pages';", "} from './pages';\nimport { DownloadsPage } from './downloadsPage';", 1)
    t = t.replace("const KNOWN_PAGES = new Set([...NAV.map((n) => n.key), 'instance']);",
                  "const KNOWN_PAGES = new Set([...NAV.map((n) => n.key), 'instance', 'downloads']);")
    t = t.replace("          {page === 'plugins' && <PluginsPage notify={notify} />}",
                  "          {page === 'plugins' && <PluginsPage notify={notify} />}\n          {page === 'downloads' && <DownloadsPage />}")
    app.write_text(t, encoding="utf-8")
    print("app route")

# ---------------------------------------------------------------- 监视器可点击
ui = src / "ui.tsx"
t = ui.read_text(encoding="utf-8")
if "downloads'" not in t:
    t = t.replace('<div className={`monitor ${running.length ? \'busy\' : \'\'}`} title="Download monitor">',
                  '<div\n      className={`monitor ${running.length ? \'busy\' : \'\'}`}\n      title="Download monitor"\n      role="button"\n      tabIndex={0}\n      onClick={() => { window.location.hash = \'#/downloads\'; }}\n      onKeyDown={(e) => { if (e.key === \'Enter\') window.location.hash = \'#/downloads\'; }}\n    >', 1)
    ui.write_text(t, encoding="utf-8")
    print("monitor click")

# ---------------------------------------------------------------- 样式
css = src / "styles.css"
c = css.read_text(encoding="utf-8")
if ".dl-row" not in c:
    c += """

/* 下载总览页 + 版本列表 */
.dl-list { display: flex; flex-direction: column; gap: 8px; padding: 4px 22px 22px; overflow: auto; }
.dl-row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2.2fr) 64px; gap: 14px;
  align-items: center; padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--surface-2); }
.dl-row.active { border-color: color-mix(in srgb, var(--accent) 45%, var(--line)); }
.dl-name b { display: block; font-size: 13px; }
.dl-name span { font-size: 11.5px; }
.dl-bar { height: 6px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
.dl-bar i { display: block; height: 100%; background: var(--accent-grad); transition: width .25s linear; }
.dl-pct { text-align: right; font-family: var(--mono); font-size: 12px; color: var(--text-2); }
.monitor { cursor: pointer; }

.version-list { margin-top: 14px; border-top: 1px solid var(--line); padding-top: 12px; }
.version-row { display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 10px; border-radius: 8px; }
.version-row:hover { background: var(--accent-faint); }
.version-main b { display: block; font-size: 12.5px; }
.version-main span { font-size: 11.5px; }
"""
    css.write_text(c, encoding="utf-8")
    print("styles")
