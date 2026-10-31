import React, { useEffect, useMemo, useRef, useState } from 'react';
import { on, rpc } from './bridge';
import type { ModItem, VersionInfo } from './types';
import { LogPanel } from './ui';

type Tab = 'versions' | 'mods' | 'modpacks';

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'versions', label: 'Versions', icon: 'grass_block.png' },
  { key: 'mods', label: 'Mods', icon: 'chest.png' },
  { key: 'modpacks', label: 'Modpacks', icon: 'hopper.png' },
];

const LOADERS = [
  { key: '', title: 'Vanilla', desc: 'Vanilla', iconImg: 'grass_block.png' },
  { key: 'fabric', title: 'Fabric', desc: 'Light mods', iconImg: 'loom.png' },
  { key: 'quilt', title: 'Quilt', desc: 'Fabric fork', iconImg: 'string.png' },
  { key: 'forge', title: 'Forge', desc: 'Classic mods', iconImg: 'anvil.png' },
  { key: 'neoforge', title: 'NeoForge', desc: '1.20.2+', iconImg: 'anvil.png' },
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
  const [tab, setTab] = useState<Tab>('versions');
  const [query, setQuery] = useState('');
  const [versions, setVersions] = useState<RemoteVersion[]>([]);
  const [mods, setMods] = useState<ModItem[]>([]);
  const [packs, setPacks] = useState<ModItem[]>([]);
  const [busy, setBusy] = useState('');
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [activity, setActivity] = useState<string[]>([]);
  const [loader, setLoader] = useState('');
  const [chosenVersion, setChosenVersion] = useState('');
  const [custom, setCustom] = useState('');
  const [targetInstance, setTargetInstance] = useState('');
  const [installing, setInstalling] = useState('');
  const logRef = useRef<HTMLDivElement | null>(null);

  const log = (line: string) => setActivity((prev) => [...prev.slice(-199), line]);

  const percent = progress && progress.total > 0 ? Math.round((progress.done / progress.total) * 100) : 0;

  useEffect(() => {
    rpc<RemoteVersion[]>('versions.remote', ['release']).then(setVersions).catch(() => {});
    rpc<ModItem[]>('mods.featured', ['mod']).then(setMods).catch(() => {});
    rpc<ModItem[]>('mods.featured', ['modpack']).then(setPacks).catch(() => {});
    const off = on<{ taskId: string; done: number; total: number }>('vein:progress', (d) =>
      setProgress({ done: d.done, total: d.total })
    );
    return () => off();
  }, []);

  useEffect(() => {
    if (installed.length && !targetInstance) setTargetInstance(installed[0].id);
  }, [installed, targetInstance]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [activity]);

  const installedIds = useMemo(() => new Set(installed.map((v) => v.id)), [installed]);

  const search = async () => {
    setBusy('search');
    try {
      if (tab === 'mods') {
        const list = query.trim()
          ? await rpc<ModItem[]>('mods.search', [query.trim(), 'mod', '', ''])
          : await rpc<ModItem[]>('mods.featured', ['mod']);
        setMods(list);
      } else if (tab === 'modpacks') {
        const list = query.trim()
          ? await rpc<ModItem[]>('mods.search', [query.trim(), 'modpack', '', ''])
          : await rpc<ModItem[]>('mods.featured', ['modpack']);
        setPacks(list);
      } else {
        const list = await rpc<RemoteVersion[]>('versions.remote', [query.trim() ? 'release' : 'release']);
        setVersions(list);
      }
      log(`Search: ${query || '(featured)'}`);
    } catch (err) {
      notify(`Search failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const installVersion = async () => {
    if (!chosenVersion) {
      notify('Select a version first');
      return;
    }
    setBusy('install');
    setInstalling(`Installing ${chosenVersion}`);
    setProgress({ done: 0, total: 1 });
    log(`Install ${chosenVersion} (${loader || 'vanilla'})`);
    try {
      const result = await rpc<{ version_id?: string; ok?: number; failed?: number }>('versions.install', [
        chosenVersion,
        loader,
        '',
        custom.trim(),
      ]);
      log(`Done: ${result.ok ?? 0} ok / ${result.failed ?? 0} failed`);
      await onInstalled();
      setCustom('');
    } catch (err) {
      log(`Failed: ${(err as Error).message}`);
      notify(`Install failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
      setProgress(null);
    }
  };

  const installProject = async (item: ModItem, projectType: 'mod' | 'modpack') => {
    const instance = targetInstance || installed[0]?.id;
    if (!instance) {
      notify('Install a game version first');
      return;
    }
    setBusy(`install:${item.slug}`);
    setInstalling(`Installing ${item.title}`);
    setProgress({ done: 0, total: 1 });
    log(`Install ${projectType}: ${item.title} -> ${instance}`);
    try {
      const result = await rpc<{ ok?: number; failed?: number; installed?: number }>('mods.install', [
        item.slug,
        instance,
        projectType,
        loader,
      ]);
      log(`Done: ${JSON.stringify(result)}`);
      await onInstalled();
    } catch (err) {
      log(`Failed: ${(err as Error).message}`);
      notify(`Install failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
      setProgress(null);
    }
  };

  return (
    <div className="page download-page">
      <div className="dl-tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`dl-tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            <img src={`icons/${t.icon}`} alt="" />
            {t.label}
          </button>
        ))}
        <div className="spacer" />
        <div className="dl-search">
          <input
            className="input"
            placeholder={tab === 'versions' ? 'Filter versions' : 'Search Modrinth'}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') search();
            }}
          />
          <button className="btn sm primary" onClick={search} disabled={busy === 'search'}>
            {busy === 'search' ? '…' : 'Search'}
          </button>
        </div>
      </div>

      {tab === 'versions' && (
        <div className="dl-grid">
          <div className="card">
            <div className="card-title">Game versions</div>
            <div className="ver-list">
              {versions.length === 0 && <div className="empty">No versions loaded</div>}
              {versions.slice(0, 120).map((v) => (
                <button
                  key={v.id}
                  className={`ver-row ${chosenVersion === v.id ? 'active' : ''}`}
                  onClick={() => setChosenVersion(v.id)}
                >
                  <img src="icons/grass_block.png" alt="" />
                  <span className="name">{v.id}</span>
                  <span className="tag">{v.type || 'release'}</span>
                  {installedIds.has(v.id) && <span className="badge">installed</span>}
                </button>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-title">Install options</div>
            <div className="kv">
              <span>Selected</span>
              <b>{chosenVersion || '—'}</b>
            </div>
            <div className="loader-grid">
              {LOADERS.map((l) => (
                <button
                  key={l.key || 'vanilla'}
                  className={`loader-card ${loader === l.key ? 'active' : ''}`}
                  onClick={() => setLoader(l.key)}
                >
                  <img className="loader-ico" src={`icons/${l.iconImg}`} alt="" />
                  <b>{l.title}</b>
                  <small>{l.desc}</small>
                </button>
              ))}
            </div>
            <label className="muted">Custom name (optional)</label>
            <input
              className="input"
              placeholder={chosenVersion || 'instance name'}
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
            />
            <button className="btn primary block" style={{ marginTop: 10 }} onClick={installVersion} disabled={busy === 'install'}>
              {busy === 'install' ? 'Installing…' : 'Install'}
            </button>
          </div>
        </div>
      )}

      {(tab === 'mods' || tab === 'modpacks') && (
        <div className="card">
          <div className="dl-instance-row">
            <span className="muted">Install to</span>
            <select value={targetInstance} onChange={(e) => setTargetInstance(e.target.value)}>
              {installed.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id}
                </option>
              ))}
            </select>
          </div>
          <div className="mod-grid">
            {(tab === 'mods' ? mods : packs).map((item) => (
              <div className="mod-card" key={item.slug}>
                {item.icon ? (
                  <img className="mod-icon" src={item.icon} alt="" />
                ) : (
                  <img className="mod-icon" src="icons/chest.png" alt="" />
                )}
                <div className="mod-meta">
                  <div className="mod-title">{item.title}</div>
                  <div className="mod-desc">{item.description}</div>
                  <div className="mod-foot">
                    <span className="chip">{item.author || 'Modrinth'}</span>
                    <span className="chip">{(item.downloads || 0).toLocaleString()} downloads</span>
                    <button
                      className="btn sm"
                      disabled={busy === `install:${item.slug}`}
                      onClick={() => installProject(item, tab === 'modpacks' ? 'modpack' : 'mod')}
                    >
                      {busy === `install:${item.slug}` ? '…' : 'Install'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {(tab === 'mods' ? mods : packs).length === 0 && (
            <div className="empty">Nothing found. Try another keyword.</div>
          )}
        </div>
      )}

      <div className="card install-card">
        <div className="card-title">{installing || 'Install progress'}</div>
        <div className="progress">
          <i style={{ width: `${installing ? Math.max(percent, 6) : 0}%` }} />
        </div>
        <div className="kv">
          <span>{progress ? `${progress.done} / ${progress.total}` : 'idle'}</span>
          <b>{installing ? `${percent}%` : '—'}</b>
        </div>
        <LogPanel lines={activity} title="Install log" height={160} />
      </div>
    </div>
  );
}
