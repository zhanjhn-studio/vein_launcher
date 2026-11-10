import React, { useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import { RemoteIcon } from './ui';
import type { ModItem, VersionInfo } from './types';

type Category = 'version' | 'mod' | 'modpack' | 'datapack' | 'shader' | 'resourcepack' | 'optifine';

const CATEGORIES: { key: Category; label: string; desc: string; icon: string; project?: string }[] = [
  { key: 'version', label: 'Vanilla & Loaders', desc: 'Install game versions with Fabric, Forge, Quilt, NeoForge', icon: 'grass_block.png' },
  { key: 'mod', label: 'Mods', desc: 'Mods from Modrinth, filtered by game version and loader', icon: 'crafting_table.png', project: 'mod' },
  { key: 'modpack', label: 'Modpacks', desc: 'Full modpacks (.mrpack) with automatic setup', icon: 'chest.png', project: 'modpack' },
  { key: 'resourcepack', label: 'Resource packs', desc: 'Textures and resource packs', icon: 'writable_book.png', project: 'resourcepack' },
  { key: 'shader', label: 'Shaders', desc: 'Shader packs for Iris / OptiFine', icon: 'spyglass.png', project: 'shader' },
  { key: 'datapack', label: 'Datapacks', desc: 'Datapacks for worlds and servers', icon: 'command_block.png', project: 'datapack' },
  { key: 'optifine', label: 'OptiFine', desc: 'Run the OptiFine installer against your game folder', icon: 'emerald.png' },
];

const LOADERS = [
  { key: '', label: 'Vanilla', icon: 'grass_block.png' },
  { key: 'fabric', label: 'Fabric', icon: 'loom.png' },
  { key: 'quilt', label: 'Quilt', icon: 'string.png' },
  { key: 'forge', label: 'Forge', icon: 'anvil.png' },
  { key: 'neoforge', label: 'NeoForge', icon: 'golden_apple.png' },
];

interface RemoteVersion {
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
}

export function DownloadPage({
  installed,
  onInstalled,
  notify,
}: {
  installed: VersionInfo[];
  onInstalled: () => Promise<void>;
  notify: (text: string) => void;
}) {
  const [category, setCategory] = useState<Category | null>(null);
  const [versions, setVersions] = useState<RemoteVersion[]>([]);
  const [items, setItems] = useState<ModItem[]>([]);
  const [query, setQuery] = useState('');
  const [mcVersion, setMcVersion] = useState('');
  const [loader, setLoader] = useState('');
  const [busy, setBusy] = useState('');
  const [chosenVersion, setChosenVersion] = useState('');
  const [custom, setCustom] = useState('');
  const [detail, setDetail] = useState<ModItem | null>(null);
  const [targetInstance, setTargetInstance] = useState('');
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [installing, setInstalling] = useState('');
  const [modTasks, setModTasks] = useState<{ id: string; title: string; state: string }[]>([]);
  const [projectVersions, setProjectVersions] = useState<ModVersion[]>([]);
  const [pvLoading, setPvLoading] = useState(false);
  const [optiLog, setOptiLog] = useState('');

  useEffect(() => {
    rpc<RemoteVersion[]>('versions.remote', [200]).then(setVersions).catch(() => {});
    const off = on<{ done: number; total: number }>('vein:progress', (d) =>
      setProgress({ done: d.done, total: d.total })
    );
    return () => off();
  }, []);

  useEffect(() => {
    if (installed.length && !targetInstance) setTargetInstance(installed[0].id);
  }, [installed, targetInstance]);

  // 选中实例后自动识别加载器，模组搜索/安装都按它过滤
  useEffect(() => {
    const id = (targetInstance || '').toLowerCase();
    const detected = ['fabric', 'quilt', 'neoforge', 'forge'].find((k) => id.includes(k)) || '';
    setLoader(detected);
  }, [targetInstance]);

  const percent = progress && progress.total > 0 ? Math.round((progress.done / progress.total) * 100) : 0;
  const projectType = CATEGORIES.find((c) => c.key === category)?.project;

  const runOptifine = async () => {
    const picked = await rpc<{ path: string }>('app.pickFile', [
      'Select OptiFine installer (.jar)',
      'OptiFine installer (*.jar);;All files (*.*)',
    ]);
    if (!picked.path) return;
    setBusy('install');
    setInstalling('OptiFine installer');
    setOptiLog('Running installer…');
    try {
      const result = await rpc<{ ok: boolean }>('optifine.install', [picked.path]);
      setOptiLog(result.ok ? 'Installer finished. Refresh versions if it created one.' : 'Failed');
      await onInstalled();
    } catch (err) {
      setOptiLog(`Failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
    }
  };

  const openCategory = (key: Category) => {
    setCategory(key);
    setItems([]);
    setQuery('');
    setChosenVersion('');
    setDetail(null);
    if (key !== 'version') {
      const project = CATEGORIES.find((c) => c.key === key)?.project || 'mod';
      rpc<ModItem[]>('mods.featured', [project, mcVersion, loader])
        .then(setItems)
        .catch((err) => notify(`加载项目列表失败（Modrinth 不可达或被限流）：${(err as Error).message}`));
    }
  };

  const runSearch = async () => {
    if (!category) return;
    setBusy('search');
    try {
      if (category === 'version') {
        if (!versions.length) setVersions(await rpc<RemoteVersion[]>('versions.remote', [200]));
      } else {
        const list = query.trim()
          ? await rpc<ModItem[]>('mods.search', [query.trim(), projectType || 'mod', mcVersion, loader])
          : await rpc<ModItem[]>('mods.featured', [projectType || 'mod', mcVersion, loader]);
        setItems(list);
      }
    } catch (err) {
      notify(`Search failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const installVersion = async () => {
    if (!chosenVersion) {
      notify('Select a game version');
      return;
    }
    setBusy('install');
    const label = `${chosenVersion}${loader ? ` + ${loader}` : ''}`;
    setInstalling(label);
    setProgress({ done: 0, total: 1 });
    notify(`开始下载 ${label}，进度见左下角下载`);
    try {
      const result = await rpc<{ version_id?: string }>('versions.install', [
        chosenVersion,
        loader,
        '',
        custom.trim(),
      ]);
      await onInstalled();
      notify(`${result?.version_id || label} 安装完成，已加入版本列表`);
    } catch (err) {
      notify(`Install failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
      setProgress(null);
    }
  };

  const openDetail = async (item: ModItem) => {
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

  const installProject = async (item: ModItem, versionId = '') => {
    const instance = targetInstance || installed[0]?.id;
    if (!instance) {
      notify('Install a game version first');
      return;
    }
    const taskId = `${item.slug}-${Date.now()}`;
    setModTasks((prev) => [...prev, { id: taskId, title: item.title, state: 'running' }]);
    setInstalling(item.title);
    notify(`开始下载 ${item.title}`);
    try {
      const res = await rpc<{ needsLoader?: boolean; mcVersion?: string; justInstalled?: boolean }>(
        'mods.install',
        [item.slug, instance, projectType || 'mod', loader, versionId]
      );
      if (res?.needsLoader) {
        const mc = res.mcVersion || instance;
        const ok = window.confirm(
          `实例 ${instance} 是原版，没有模组加载器，模组不会被加载。\n\n是否创建 Fabric ${mc} 实例，并把 ${item.title} 装进去？`
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
      setModTasks((prev) => prev.map((x) => (x.id === taskId ? { ...x, state: 'done' } : x)));
    } catch (err) {
      notify(`Install failed: ${(err as Error).message}`);
      setModTasks((prev) => prev.map((x) => (x.id === taskId ? { ...x, state: 'error' } : x)));
    } finally {
      setInstalling('');
      setProgress(null);
    }
  };

  const filteredVersions = useMemo(
    () =>
      versions.filter(
        (v) =>
          (v.type === 'release' || v.id.includes('.')) &&
          (!query.trim() || v.id.includes(query.trim()))
      ),
    [versions, query]
  );

  // ---------- 一级：分类菜单 ----------
  if (!category) {
    return (
      <div className="page">
        <div className="page-head">
          <h1>Download</h1>
          <span className="muted">Pick a category, then choose exactly what to install</span>
        </div>
        <div className="cat-grid">
          {CATEGORIES.map((c) => (
            <button className="cat-card" key={c.key} onClick={() => openCategory(c.key)}>
              <img src={`icons/${c.icon}`} alt="" />
              <div>
                <b>{c.label}</b>
                <p>{c.desc}</p>
              </div>
            </button>
          ))}
        </div>

        {installing && (
          <div className="install-status">
            <i className="layui-icon layui-icon-loading layui-anim layui-anim-rotate layui-anim-loop" />
            <span>Installing {installing}</span>
            <span className="muted">progress is in the sidebar monitor</span>
          </div>
        )}
      </div>
    );
  }

  // ---------- 二级：分类内页面 ----------
  return (
    <div className="page">
      <div className="dl-head">
        <button className="btn sm ghost" onClick={() => setCategory(null)}>
          ← Back
        </button>
        <h1>{CATEGORIES.find((c) => c.key === category)?.label}</h1>
        {category !== 'version' && (
          <span className="muted">
            {mcVersion ? `MC ${mcVersion}` : 'Any MC version'} · {loader || 'Any loader'}
          </span>
        )}
      </div>

      <div className="filter-row">
        <select value={mcVersion} onChange={(e) => setMcVersion(e.target.value)}>
          <option value="">Any MC version</option>
          {versions.slice(0, 80).map((v) => (
            <option key={v.id} value={v.id}>
              {v.id}
            </option>
          ))}
        </select>
        {(category === 'version' || category === 'mod' || category === 'modpack') && (
          <select value={loader} onChange={(e) => setLoader(e.target.value)}>
            {LOADERS.map((l) => (
              <option key={l.key} value={l.key}>
                {l.label}
              </option>
            ))}
          </select>
        )}
        <input
          className="input"
          placeholder={category === 'version' ? 'Filter versions' : 'Search Modrinth'}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') runSearch();
          }}
        />
        <button className="btn primary sm" onClick={runSearch} disabled={busy === 'search'}>
          {busy === 'search' ? '…' : 'Search'}
        </button>
      </div>

      {category === 'optifine' ? (
        <div className="card">
          <div className="card-title">OptiFine installer</div>
          <p className="muted">
            OptiFine is not redistributable, so bring your own installer. The launcher runs it against
            your game folder with Java and then rescans installed versions.
          </p>
          <div className="kv">
            <span>Game folder</span>
            <b>use Settings → Game folder</b>
          </div>
          <div className="row-actions">
            <button className="btn primary" onClick={runOptifine} disabled={busy === 'install'}>
              {busy === 'install' ? 'Running…' : 'Choose installer & run'}
            </button>
          </div>
          {optiLog && <div className="activity">{optiLog}</div>}
        </div>
      ) : category === 'version' ? (
        <div className="dl-grid">
          <div className="card">
            <div className="card-title">Game versions</div>
            <div className="ver-list">
              {filteredVersions.length === 0 && <div className="empty">No versions</div>}
              {filteredVersions.map((v) => (
                <button
                  key={v.id}
                  className={`ver-row ${chosenVersion === v.id ? 'active' : ''}`}
                  onClick={() => setChosenVersion(v.id)}
                >
                  <img src="icons/grass_block.png" alt="" />
                  <span className="name">{v.id}</span>
                  <span className="tag">{v.type || 'release'}</span>
                  {installed.some((i) => i.id === v.id) && <span className="badge">installed</span>}
                </button>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-title">Install</div>
            <div className="kv">
              <span>Game version</span>
              <b>{chosenVersion || '—'}</b>
            </div>
            <div className="kv">
              <span>Loader</span>
              <b>{LOADERS.find((l) => l.key === loader)?.label || 'Vanilla'}</b>
            </div>
            <div className="loader-grid">
              {LOADERS.map((l) => (
                <button
                  key={l.key || 'vanilla'}
                  className={`loader-card ${loader === l.key ? 'active' : ''}`}
                  onClick={() => setLoader(l.key)}
                >
                  <img className="loader-ico" src={`icons/${l.icon}`} alt="" />
                  <b>{l.label}</b>
                </button>
              ))}
            </div>
            <label className="muted">Custom instance name (optional)</label>
            <input
              className="input"
              placeholder={chosenVersion || 'instance name'}
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
            />
            <button className="btn primary block" style={{ marginTop: 10 }} onClick={installVersion} disabled={busy === 'install'}>
              {busy === 'install' ? 'Installing…' : `Install ${chosenVersion || ''}`}
            </button>
          </div>
        </div>
      ) : detail ? (
        <div className="card project-detail">
          <div className="mod-head">
            {detail.icon ? (
              <RemoteIcon src={detail.icon} className="detail-icon" />
            ) : (
              <RemoteIcon className="detail-icon" />
            )}
            <div>
              <h2>{detail.title}</h2>
              <p className="muted">{detail.author} · {(detail.downloads || 0).toLocaleString()} downloads</p>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <button className="btn sm" onClick={() => setDetail(null)}>
                Back
              </button>
            </div>
          </div>
          <p className="desc">{detail.description}</p>
          <div className="kv">
            <span>Category</span>
            <b>{CATEGORIES.find((c) => c.key === category)?.label}</b>
          </div>
          <div className="kv">
            <span>MC version / loader</span>
            <b>
              {mcVersion || 'any'} · {loader || 'any'}
            </b>
          </div>
          <div className="row-actions">
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
          </div>
        </div>
      ) : (
        <>
          <div className="proj-grid">
            {items.map((item) => (
              <button className="proj-card" key={item.slug} onClick={() => openDetail(item)}>
                <RemoteIcon src={item.icon} />
                <div>
                  <b>{item.title}</b>
                  <p>{item.description}</p>
                  <span className="muted">
                    {item.author} · {(item.downloads || 0).toLocaleString()}
                  </span>
                </div>
              </button>
            ))}
          </div>
          {items.length === 0 && <div className="empty">Nothing found. Try another keyword.</div>}
        </>
      )}

      {installing && (
        <div className="install-status">
          <i className="layui-icon layui-icon-loading layui-anim layui-anim-rotate layui-anim-loop" />
          <span>Installing {installing}</span>
          <span className="muted">progress is in the sidebar monitor</span>
        </div>
      )}
    </div>
  );
}
