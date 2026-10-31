import React, { useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import type { ModItem, VersionInfo } from './types';

type Category = 'version' | 'mod' | 'modpack' | 'datapack' | 'shader' | 'resourcepack' | 'optifine';

const CATEGORIES: { key: Category; label: string; desc: string; icon: string; project?: string }[] = [
  { key: 'version', label: 'Vanilla & Loaders', desc: 'Install game versions with Fabric, Forge, Quilt, NeoForge', icon: 'grass_block.png' },
  { key: 'mod', label: 'Mods', desc: 'Mods from Modrinth, filtered by game version and loader', icon: 'chest.png', project: 'mod' },
  { key: 'modpack', label: 'Modpacks', desc: 'Full modpacks (.mrpack) with automatic setup', icon: 'hopper.png', project: 'modpack' },
  { key: 'resourcepack', label: 'Resource packs', desc: 'Textures and resource packs', icon: 'writable_book.png', project: 'resourcepack' },
  { key: 'shader', label: 'Shaders', desc: 'Shader packs for Iris / OptiFine', icon: 'grass_block.png', project: 'shader' },
  { key: 'datapack', label: 'Datapacks', desc: 'Datapacks for worlds and servers', icon: 'chest.png', project: 'datapack' },
  { key: 'optifine', label: 'OptiFine', desc: 'Run the OptiFine installer against your game folder', icon: 'anvil.png' },
];

const LOADERS = [
  { key: '', label: 'Vanilla', icon: 'grass_block.png' },
  { key: 'fabric', label: 'Fabric', icon: 'loom.png' },
  { key: 'quilt', label: 'Quilt', icon: 'string.png' },
  { key: 'forge', label: 'Forge', icon: 'anvil.png' },
  { key: 'neoforge', label: 'NeoForge', icon: 'anvil.png' },
];

interface RemoteVersion {
  id: string;
  type?: string;
  release_time?: string;
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
        .catch(() => {});
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
    setInstalling(`${chosenVersion}${loader ? ` + ${loader}` : ''}`);
    setProgress({ done: 0, total: 1 });
    try {
      await rpc('versions.install', [chosenVersion, loader, '', custom.trim()]);
      await onInstalled();
    } catch (err) {
      notify(`Install failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
      setProgress(null);
    }
  };

  const installProject = async (item: ModItem) => {
    const instance = targetInstance || installed[0]?.id;
    if (!instance) {
      notify('Install a game version first');
      return;
    }
    setBusy('install');
    setInstalling(item.title);
    setProgress({ done: 0, total: 1 });
    try {
      await rpc('mods.install', [item.slug, instance, projectType || 'mod', loader]);
      notify(`${item.title} installed to ${instance}`);
      await onInstalled();
      setDetail(null);
    } catch (err) {
      notify(`Install failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
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
          <div className="card" style={{ marginTop: 12 }}>
            <div className="card-title">{installing}</div>
            <div className="progress">
              <i style={{ width: `${Math.max(percent, 4)}%` }} />
            </div>
          </div>
        )}
      </div>
    );
  }

  // ---------- 二级：分类内页面 ----------
  return (
    <div className="page">
      <div className="dl-head">
        <button className="btn sm" onClick={() => setCategory(null)}>
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
            <b>use 设置 → Game folder</b>
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
            {detail.icon ? <img src={detail.icon} alt="" /> : <img src="icons/chest.png" alt="" />}
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
            <button className="btn primary" onClick={() => installProject(detail)} disabled={busy === 'install'}>
              {busy === 'install' ? 'Installing…' : 'Install'}
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="proj-grid">
            {items.map((item) => (
              <button className="proj-card" key={item.slug} onClick={() => setDetail(item)}>
                {item.icon ? <img src={item.icon} alt="" /> : <img src="icons/chest.png" alt="" />}
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
        <div className="card" style={{ marginTop: 12 }}>
          <div className="card-title">{installing}</div>
          <div className="progress">
            <i style={{ width: `${Math.max(percent, 4)}%` }} />
          </div>
          <div className="kv">
            <span>{progress ? `${progress.done} / ${progress.total}` : 'starting'}</span>
            <b>{percent}%</b>
          </div>
        </div>
      )}
    </div>
  );
}
