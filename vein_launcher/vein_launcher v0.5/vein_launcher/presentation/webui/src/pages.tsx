import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import { LayuiProgress, RemoteIcon } from './ui';
import type {
  AccountInfo,
  AppInfo,
  Category,
  DownloadTask,
  JavaRuntime,
  MlcState,
  ModItem,
  PluginState,
  VersionInfo,
} from './types';
import { CategoryList, Empty, PermissionDialog, StatusDot, ThreePane } from './ui';
import { layuiVersion, layerMsg, openLayuiPreview } from './layui';
import { currentLang, setLang, t } from './i18n';

const CATEGORIES: { key: Category; label: string; hint?: string }[] = [
  { key: 'vanilla', label: 'Game versions' },
  { key: 'modpack', label: 'Modpacks' },
  { key: 'mod', label: 'Mods' },
  { key: 'plugin', label: 'Server plugins' },
  { key: 'resourcepack', label: 'Resource packs' },
  { key: 'shader', label: 'Shaders' },
  { key: 'datapack', label: 'Datapacks' },
];

const LOADERS = [
  { key: '', title: 'Vanilla', desc: 'Vanilla', iconImg: 'grass_block.png' },
  { key: 'fabric', title: 'Fabric', desc: 'Light mods', iconImg: 'loom.png' },
  { key: 'quilt', title: 'Quilt', desc: 'Fabric Branch', iconImg: 'string.png' },
  { key: 'forge', title: 'Forge', desc: 'Classic mods', iconImg: 'anvil.png' },
  { key: 'neoforge', title: 'NeoForge', desc: '1.20.2+', iconImg: 'anvil.png' },
];

// ---------------------------------------------------------------- Launch
export function LaunchPage({
  installed,
  accounts,
  selected,
  onSelect,
  notify,
}: {
  installed: VersionInfo[];
  accounts: AccountInfo[];
  selected: string;
  onSelect: (id: string) => void;
  notify: (text: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const account = accounts.find((a) => a.selected) || null;

  useEffect(() => on<string>('vein:log', (line) => setLogs((prev) => [...prev.slice(-299), line])), []);

  const launch = async () => {
    if (!selected) {
      notify('No versions yet. Download one first.');
      return;
    }
    setBusy(true);
    setStatus('Starting…');
    try {
      const result = await rpc<{ pid: number }>('launch', [selected, account?.username ?? 'Player']);
      setStatus(`Launched, PID ${result.pid}`);
    } catch (err) {
      setStatus('');
      notify(`Launch failed：${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="hero">
        <div className="hero-left">
          <div className="label">Current version</div>
          {installed.length === 0 ? (
            <div className="hero-version">Not installed</div>
          ) : (
            <select className="hero-select" value={selected} onChange={(e) => onSelect(e.target.value)}>
              {installed.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id}
                </option>
              ))}
            </select>
          )}
          <div className="hero-meta">
            <span className="chip">{account ? `Offline · ${account.username}` : 'Not signed in'}</span>
            <span className="chip">{installed.length} instances</span>
            <span className="chip">{status || 'Ready'}</span>
          </div>
          <button className="launch-btn" onClick={launch} disabled={busy}>
            {busy ? 'Launching…' : 'Launch game'}
          </button>
        </div>
        <div className="hero-right">
          <div className="card-title">{t('Game log')}</div>
          {logs.length === 0 ? (
            <Empty>LaunchGame output appears here after launch</Empty>
          ) : (
            <div className="log-view">{logs.join('\n')}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Download
export function DownloadPage({
  installed,
  onInstalled,
  notify,
}: {
  installed: VersionInfo[];
  onInstalled: () => Promise<void>;
  notify: (text: string) => void;
}) {
  const [category, setCategory] = useState<Category>(
    (sessionStorage.getItem('vl.download.category') as Category) || 'vanilla'
  );
  const [items, setItems] = useState<VersionInfo[]>([]);
  const [mods, setMods] = useState<ModItem[]>([]);
  const [picked, setPicked] = useState<VersionInfo | ModItem | null>(null);
  const [pickedMod, setPickedMod] = useState<ModItem | null>(null);
  const [loader, setLoader] = useState('');
  const [busy, setBusy] = useState(false);
  const [activity, setActivity] = useState<string[]>([]);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [custom, setCustom] = useState('');
  const [fileTarget, setFileTarget] = useState('');
  const [files, setFiles] = useState<{ name: string; dir: boolean; size: number; rel: string }[]>([]);

  const log = useCallback((text: string) => {
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    setActivity((prev) => [...prev.slice(-199), `[${time}] ${text}`]);
  }, []);

  const load = useCallback(async () => {
    setBusy(true);
    setPicked(null);
    setPickedMod(null);
    try {
      if (category === 'vanilla') {
        const list = await rpc<VersionInfo[]>('versions.remote', [200]);
        setItems(list);
        setMods([]);
        log(`Versions ${list.length}`);
      } else {
        const list = await rpc<ModItem[]>('mods.featured', [category, '', 'fabric', 40]);
        setMods(list);
        setItems([]);
        log(`${category} featured ${list.length}`);
      }
    } catch (err) {
      log(`Load failed：${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }, [category, log]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(
    () =>
      on<{ taskId: string; done: number; total: number }>('vein:progress', (detail) =>
        setProgress({ done: detail.done, total: detail.total })
      ),
    []
  );

  const loadFiles = async (instance: string) => {
    try {
      setFiles(await rpc<{ name: string; dir: boolean; size: number; rel: string }[]>('versions.files', [instance, '']));
    } catch {
      setFiles([]);
    }
  };

  useEffect(() => {
    if (!picked) return;
    const candidate = custom.trim() || (loader ? `${loader}-${(picked as VersionInfo).id}` : (picked as VersionInfo).id);
    if (installed.some((v) => v.id === candidate)) {
      setFileTarget(candidate);
      loadFiles(candidate);
    } else {
      setFileTarget('');
      setFiles([]);
    }
  }, [picked, loader, custom, installed]);

  const installedIds = useMemo(() => new Set(installed.map((v) => v.id)), [installed]);
  const targetId = picked ? (loader ? `${loader}-${(picked as VersionInfo).id}` : (picked as VersionInfo).id) : '';

  const installVersion = async () => {
    if (!picked) return;
    setBusy(true);
    log(`Install ${targetId}`);
    try {
      const result = await rpc<{
        loader_version?: string;
        ok?: number;
        failed?: number;
        files?: number;
        version_id?: string;
      }>('versions.install', [(picked as VersionInfo).id, loader, '', custom.trim()]);
      log(
        result.loader_version
          ? `Loader installed：${targetId}（${result.loader_version}）`
          : `Installed：Installed: ${result.ok ?? 0} / Failed ${result.failed ?? 0}`
      );
      const finalId = result.version_id || targetId;
      setFileTarget(finalId);
      await onInstalled();
      loadFiles(finalId);
    } catch (err) {
      log(`Install failed：${(err as Error).message}`);
      notify(`Install failed：${(err as Error).message}`);
    } finally {
      setBusy(false);
      setProgress(null);
    }
  };

  const installMod = async (item: ModItem) => {
    const instance = installed[0]?.id;
    if (!instance) {
      notify('Install an instance first');
      return;
    }
    setBusy(true);
    log(`Install ${item.title} → ${instance}`);
    try {
      const result = await rpc<{ installed?: number; files?: number }>('mods.install', [
        item.slug,
        instance,
        category,
        'fabric',
      ]);
      log(`Installed：${result.installed ?? result.files ?? 1} files`);
    } catch (err) {
      log(`Install failed：${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <ThreePane
      left={<CategoryList items={CATEGORIES} active={category} onPick={(k) => setCategory(k as Category)} />}
      middle={
        <>
          <div className="pane-head">
            <span>{category === 'vanilla' ? 'Version' : 'Featured'}</span>
            <button className="btn sm" onClick={load} disabled={busy}>
              {busy ? 'Loading' : 'Refresh'}
            </button>
          </div>
          <div className="list">
            {category === 'vanilla'
              ? items.map((v) => (
                  <button
                    key={v.id}
                    className={`row-item ${picked && (picked as VersionInfo).id === v.id ? 'active' : ''}`}
                    onClick={() => {
                      setPicked(v);
                      setLoader('');
                    }}
                  >
                    <span className="title">{v.id}</span>
                    <span className="sub">{v.release_time}{installedIds.has(v.id) ? ' · Installed' : ''}</span>
                  </button>
                ))
              : mods.map((m) => (
                  <button
                    key={m.slug}
                    className={`row-item ${pickedMod?.slug === m.slug ? 'active' : ''}`}
                    onClick={() => setPickedMod(m)}
                  >
                    <span className="title">{m.title}</span>
                    <span className="sub">⬇ {m.downloads.toLocaleString()}</span>
                  </button>
                ))}
            {!busy && items.length === 0 && mods.length === 0 && <Empty>{t('Nothing here yet')}</Empty>}
          </div>
        </>
      }
      right={
        category === 'vanilla' ? (
          picked ? (
            <div className="detail">
              <h2>{(picked as VersionInfo).id}</h2>
              <div className="kv"><span>Instance ID</span><b>{targetId}</b></div>
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
              {progress && (
                <LayuiProgress
                  percent={
                    progress.total ? Math.round((progress.done / progress.total) * 100) : 0
                  }
                />
              )}
              <div className="kv"><span>Type</span><b>{(picked as VersionInfo).type ?? 'release'}</b></div>
              <div className="kv"><span>Released</span><b>{(picked as VersionInfo).release_time ?? '—'}</b></div>

              <label className="muted" style={{ marginTop: 6 }}>Custom name (optional, defaults to  {targetId}）</label>
              <input
                className="input"
                placeholder={targetId}
                value={custom}
                onChange={(e) => setCustom(e.target.value)}
              />

              <button className="btn primary block" style={{ marginTop: 10 }} onClick={installVersion} disabled={busy}>
                {busy ? 'Installing…' : 'Install'}
              </button>
              <div className="activity">{activity.join('\n') || '（Progress appears here)'}</div>

              {fileTarget && (
                <>
                  <div className="pane-head" style={{ padding: '14px 0 8px', border: 0 }}>
                    <span>Version files · {fileTarget}</span>
                    <div className="row-actions" style={{ marginTop: 0 }}>
                      <button className="btn sm" onClick={() => loadFiles(fileTarget)}>Refresh</button>
                      <button className="btn sm" onClick={() => rpc('versions.openFolder', [fileTarget]).catch(() => {})}>
                        Open folder
                      </button>
                    </div>
                  </div>
                  {files.length === 0 ? (
                    <div className="empty">Folder is empty or installation is incomplete</div>
                  ) : (
                    files.map((f) => (
                      <div className="row-item" key={f.rel}>
                        <span className="title">{f.dir ? '📁 ' : ''}{f.name}</span>
                        <span className="sub">
                          {f.dir ? 'folder' : `${Math.max(1, Math.round(f.size / 1024))} KB`}
                        </span>
                      </div>
                    ))
                  )}
                </>
              )}
            </div>
          ) : (
            <Empty>Select a version to see install options</Empty>
          )
        ) : pickedMod ? (
          <div className="detail">
            <div className="mod-head">
              <RemoteIcon src={pickedMod.icon} className="mod-icon" fallback="icons/crafting_table.png" />
              <div>
                <h2>{pickedMod.title}</h2>
                <div className="muted">{pickedMod.author} · ⬇ {pickedMod.downloads.toLocaleString()}</div>
              </div>
            </div>
            <p className="desc">{pickedMod.description}</p>
            <button className="btn primary block" onClick={() => installMod(pickedMod)} disabled={busy}>
              Install to {installed[0]?.id ?? '（no instance)'}
            </button>
            <div className="activity">{activity.join('\n') || '（InstallProgress appears here)'}</div>
          </div>
        ) : (
          <Empty>Select an item to see details</Empty>
        )
      }
    />
  );
}

// ---------------------------------------------------------------- Plugins
export function PluginsPage({ notify }: { notify: (text: string) => void }) {
  const [state, setState] = useState<PluginState>({ host: { running: false, pid: null, node: null }, plugins: [] });
  const [filter, setFilter] = useState('all');
  const [picked, setPicked] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [busy, setBusy] = useState('');
  const [pendingGrant, setPendingGrant] = useState<string>('');

  const refresh = useCallback(async () => {
    try {
      const s = await rpc<PluginState>('plugins.state');
      setState(s);
      setLogs(await rpc<string[]>('plugins.logs', [120]));
    } catch (err) {
      notify(`Failed to read plugins: ${(err as Error).message}`);
    }
  }, [notify]);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 4000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const shown = state.plugins.filter((p) =>
    filter === 'all' ? true : filter === 'enabled' ? p.enabled : !p.enabled
  );
  const current = state.plugins.find((p) => p.name === picked) || shown[0] || null;

  const toggle = async (name: string, enable: boolean) => {
    setBusy(name);
    try {
      await rpc('plugins.setEnabled', [name, enable]);
      await refresh();
    } catch (err) {
      notify(`Operation failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setPendingGrant('');
    }
  };

  const hotReload = async (name: string) => {
    setBusy(name);
    try {
      await rpc('plugins.reload', [name]);
      await refresh();
      notify(`${name} Reloaded`);
    } catch (err) {
      notify(`Reload failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  return (
    <>
      <ThreePane
        left={
          <CategoryList
            items={[
              { key: 'all', label: 'All', hint: String(state.plugins.length) },
              { key: 'enabled', label: 'Enabled', hint: String(state.plugins.filter((p) => p.enabled).length) },
              { key: 'disabled', label: 'Disabled', hint: String(state.plugins.filter((p) => !p.enabled).length) },
            ]}
            active={filter}
            onPick={setFilter}
          />
        }
        middle={
          <>
            <div className="pane-head">
              <span>{t('Plugins')}</span>
              <StatusDot on={state.host.running} label={state.host.running ? `Host ${state.host.pid}` : 'Host stopped'} />
            </div>
            <div className="list">
              {shown.length === 0 && <Empty>t('No plugins yet')</Empty>}
              {shown.map((p) => (
                <button
                  key={p.name}
                  className={`row-item ${current?.name === p.name ? 'active' : ''}`}
                  onClick={() => setPicked(p.name)}
                >
                  <span className="title">{p.displayName}</span>
                  <span className="sub">v{p.version} · {p.loaded ? 'Loaded' : p.enabled ? 'Pending' : 'Disabled'}</span>
                </button>
              ))}
            </div>
          </>
        }
        right={
          current ? (
            <div className="detail">
              <h2>{current.displayName}</h2>
              <div className="muted">{current.description || current.name}</div>
              <div className="perm-block">
                <div className="card-title">{t('Permissions')}</div>
                {current.permissions.length === 0 ? (
                  <span className="muted">No permission declared</span>
                ) : (
                  <div className="tags">
                    {current.permissions.map((perm) => (
                      <code key={perm}>{perm}</code>
                    ))}
                  </div>
                )}
              </div>
              <div className="row-actions">
                <button
                  className="btn"
                  onClick={() => hotReload(current.name)}
                  disabled={busy === current.name}
                >
                  Hot reload
                </button>
                {current.enabled ? (
                  <button className="btn" onClick={() => toggle(current.name, false)} disabled={busy === current.name}>
                    Disable
                  </button>
                ) : (
                  <button
                    className="btn primary"
                    onClick={() =>
                      current.permissions.length > 0
                        ? setPendingGrant(current.name)
                        : toggle(current.name, true)
                    }
                    disabled={busy === current.name}
                  >
                    Enable
                  </button>
                )}
              </div>
              <div className="card-title" style={{ marginTop: 16 }}>Host log</div>
              <div className="activity">{logs.join('\n') || 'No logs'}</div>
            </div>
          ) : (
            <Empty>Select a plugin to see permissions and logs</Empty>
          )
        }
      />
      {pendingGrant && current && (
        <PermissionDialog
          plugin={current}
          onCancel={() => setPendingGrant('')}
          onConfirm={() => toggle(current.name, true)}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------- MLC
export function MlcPage({
  installed,
  selected,
  notify,
}: {
  installed: VersionInfo[];
  selected: string;
  notify: (text: string) => void;
}) {
  const [state, setState] = useState<MlcState>({ connected: false, pid: null });
  const [result, setResult] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [busy, setBusy] = useState('');
  const [saveWorlds, setSaveWorlds] = useState<
    { name: string; seed: number; version: string; instance: string; path: string; folder: string }[]
  >([]);

  useEffect(() => {
    const tick = async () => {
      try {
        setState(await rpc<MlcState>('mlc.state'));
      } catch {
        /* ignore */
      }
    };
    tick();
    const timer = window.setInterval(tick, 2000);
    const off = on<string>('vein:log', (line) => setLogs((prev) => [...prev.slice(-199), line]));
    return () => {
      window.clearInterval(timer);
      off();
    };
  }, []);

  const launch = async () => {
    if (!selected) {
      notify('No instance available');
      return;
    }
    setBusy('launch');
    try {
      const r = await rpc<{ pid: number }>('launch', [selected, 'Player']);
      setResult(`mlc.launch → pid ${r.pid}`);
    } catch (err) {
      notify(`Launch failed：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const worlds = async () => {
    setBusy('worlds');
    try {
      const r = await rpc<{ worlds: unknown[] }>('mlc.worlds', [selected]);
      setResult(`mlc.world.info → ${JSON.stringify(r, null, 2)}`);
    } catch (err) {
      setResult(`mlc.world.info Failed：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const [scan, setScan] = useState<any>(null);

  const scanWorld = async (instance: string, folder: string) => {
    setBusy('scan');
    setScan(null);
    try {
      const data = await rpc<any>('mc2.scan', [instance, folder]);
      setScan(data);
      setResult(`mc2.scan → ${folder}`);
    } catch (err) {
      setResult(`mc2.scan Failed：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const loadWorlds = async () => {
    setBusy('mc2');
    try {
      const list = await rpc<{ name: string; seed: number; version: string; instance: string; path: string; folder: string }[]>(
        'mc2.worlds',
        ['']
      );
      setSaveWorlds(list);
      setResult(`mc2.worlds → ${list.length} saves`);
    } catch (err) {
      setResult(`mc2.worlds Failed：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="page">
      <div className="pane-head">
        <span>VL-MLC Control layer</span>
        <StatusDot
          on={state.connected}
          label={state.connected ? `Connected · pid ${state.pid}` : 'Disconnected'}
          tone="ok"
        />
      </div>
      <div className="cards">
        <div className="card">
          <div className="card-title">{t('Connection')}</div>
          <div className="kv"><span>Status</span><b>{state.connected ? 'Running' : 'Idle'}</b></div>
          <div className="kv"><span>Instance</span><b>{selected || '—'}</b></div>
          <div className="row-actions">
            <button className="btn primary" onClick={launch} disabled={busy === 'launch'}>
              mlc.launch
            </button>
            <button className="btn" onClick={worlds} disabled={busy === 'worlds'}>
              World info
            </button>
          </div>
        </div>
        <div className="card">
          <div className="card-title">{t('Call result')}</div>
          <pre className="activity">{result || '（Results appear here)'}</pre>
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <div className="pane-head" style={{ padding: '0 0 10px', border: 0 }}>
          <span>MC2 · World data</span>
          <button className="btn sm" onClick={loadWorlds} disabled={busy === 'mc2'}>
            {busy === 'mc2' ? '…' : 'Scan saves'}
          </button>
        </div>
        {saveWorlds.length === 0 ? (
          <div className="empty">No saves found. Create a world in-game, then scan again.</div>
        ) : (
          saveWorlds.map((w) => (
            <button
              className="row-item"
              key={w.path}
              onClick={() => scanWorld(w.instance, w.folder)}
              disabled={busy === 'scan'}
            >
              <span className="title">{w.name}</span>
              <span className="sub">
                seed {w.seed} · {w.version || '—'} · {w.instance}
              </span>
            </button>
          ))
        )}
      </div>

      {scan && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-title">
            MC2 scan · {scan.name} · seed {scan.seed}
          </div>
          {Object.entries(scan.scan?.dimensions ?? {}).map(([dim, info]: [string, any]) => (
            <div key={dim} style={{ marginTop: 10 }}>
              <div className="kv">
                <span>{dim}</span>
                <b>{info.chunks} chunks · {info.files} region files</b>
              </div>
              <div className="muted" style={{ marginTop: 4 }}>
                biomes： {info.biomes.length ? info.biomes.join(', ') : '—'}
              </div>
              <div className="muted" style={{ marginTop: 2 }}>
                structures： {info.structures.length ? info.structures.join(', ') : '—'}
              </div>
            </div>
          ))}
          {Object.keys(scan.scan?.dimensions ?? {}).length === 0 && (
            <div className="empty">No region files in this world.</div>
          )}
        </div>
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">{t('Event stream')}</div>
        <div className="activity">{logs.join('\n') || 'MLC events appear here after launch'}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Multiplayer
export function MultiplayerPage() {
  return (
    <div className="page center">
      <h2>Multiplayer</h2>
      <p className="muted">Coming soon</p>
    </div>
  );
}

// ---------------------------------------------------------------- Settings
export function SettingsPage({ notify }: { notify: (text: string) => void }) {
  const [section, setSection] = useState('about');
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [runtimes, setRuntimes] = useState<JavaRuntime[]>([]);
  const [mcDir, setMcDir] = useState('');
  const [javaBusy, setJavaBusy] = useState(0);
  const [javaMsg, setJavaMsg] = useState('');

  useEffect(() => {
    rpc<{ path: string }>('minecraft.getDir')
      .then((r) => setMcDir(r.path))
      .catch(() => {});
  }, []);

  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
  }, []);

  const detect = async () => {
    try {
      setRuntimes(await rpc<JavaRuntime[]>('java.detect'));
    } catch (err) {
      notify(`Detect failed: ${(err as Error).message}`);
    }
  };

  return (
    <ThreePane
      left={
        <CategoryList
          items={[
            { key: 'about', label: 'About' },
            { key: 'java', label: 'Java' },
            { key: 'game', label: 'Game folder' },
            { key: 'logs', label: 'Logs' },
            { key: 'language', label: 'Language / Language' },
          ]}
          active={section}
          onPick={setSection}
        />
      }
      middle={
        <div className="detail">
          {section === 'about' && (
            <>
              <h2>About</h2>
              <div className="kv"><span>{t('Versions')}</span><b>{info?.version ?? '—'}</b></div>
              <div className="kv"><span>Data folder</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
              <div className="kv"><span>Architecture</span><b>Python + PySide6 WebView + React + TS</b></div>
            </>
          )}
          {section === 'java' && (
            <>
              <h2>Java Runtime</h2>
              <button className="btn" onClick={detect}>{t('Auto detect')}</button>
              <div className="row-actions" style={{ marginTop: 10 }}>
                {[8, 17, 21].map((major) => (
                  <button
                    key={major}
                    className="btn sm"
                    disabled={javaBusy === major}
                    onClick={async () => {
                      setJavaBusy(major);
                      setJavaMsg(`Installing Java ${major}…`);
                      try {
                        const r = await rpc<{ path: string; downloaded: boolean }>('java.ensure', [
                          major,
                        ]);
                        setJavaMsg(`Java ${major}: ${r.path} (${r.downloaded ? 'downloaded' : 'existing'})`);
                      } catch (err) {
                        setJavaMsg(`Java ${major} failed: ${(err as Error).message}`);
                      } finally {
                        setJavaBusy(0);
                      }
                    }}
                  >
                    {javaBusy === major ? '…' : `Install Java ${major}`}
                  </button>
                ))}
              </div>
              {javaMsg && <p className="muted">{javaMsg}</p>}
              {runtimes.length === 0 ? (
                <Empty>Click detect to scan local Java</Empty>
              ) : (
                runtimes.map((rt) => (
                  <div className="row-item" key={rt.path}>
                    <span className="title">Java {rt.major}</span>
                    <span className="sub mono">{rt.path}</span>
                  </div>
                ))
              )}
            </>
          )}
          {section === 'game' && (
            <>
              <h2>Game folder (.minecraft)</h2>
              <p className="muted">
                Use an existing .minecraft directory, or keep the launcher-managed one.。
              </p>
              <div className="kv">
                <span>Current</span>
                <b className="mono">{mcDir || '—'}</b>
              </div>
              <div className="row-actions">
                <button
                  className="btn"
                  onClick={async () => {
                    const picked = await rpc<{ path: string }>('app.pickDirectory', [
                      'Select .minecraft folder',
                    ]);
                    if (!picked.path) return;
                    const applied = await rpc<{ path: string }>('minecraft.setDir', [picked.path]);
                    setMcDir(applied.path);
                    notify(`Game folder:  ${applied.path}`);
                  }}
                >
                  Choose…
                </button>
                <button
                  className="btn"
                  onClick={async () => {
                    const applied = await rpc<{ path: string }>('minecraft.setDir', ['']);
                    setMcDir(applied.path);
                    notify('Reverted to launcher-managed folder');
                  }}
                >
                  Use default
                </button>
              </div>
            </>
          )}
          {section === 'language' && (
            <>
              <h2>Language</h2>
              <p className="muted">Switching applies immediately and is saved.。</p>
              <div className="row-actions">
                <button
                  className={currentLang() === 'en' ? 'btn primary' : 'btn'}
                  onClick={() => setLang('en')}
                >
                  English
                </button>
                <button
                  className={currentLang() === 'zh' ? 'btn primary' : 'btn'}
                  onClick={() => setLang('zh')}
                >
                  简体中文
                </button>
              </div>
            </>
          )}
          {section === 'logs' && (
            <>
              <h2>Logs</h2>
              <p className="muted">Written daily to VeinLauncher/log/YYYY-MM-DD.log</p>
              <button className="btn" onClick={() => rpc('logs.openDir').catch(() => {})}>
                Open log folder
              </button>
            </>
          )}
        </div>
      }
      right={<Empty>Select a settings group</Empty>}
    />
  );
}

// ---------------------------------------------------------------- Toolbox
export function ToolboxPage({ notify }: { notify: (text: string) => void }) {
  const [info, setInfo] = useState<AppInfo | null>(null);
  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
  }, []);

  return (
    <div className="page">
      <div className="page-head"><h1>{t('Toolbox')}</h1><span className="muted">Quick actions</span></div>
      <div className="cards">
        <div className="card">
          <div className="card-title">{t('Folders')}</div>
          <div className="kv"><span>Data folder</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
          <div className="row-actions">
            <button className="btn" onClick={() => rpc('logs.openDir').catch(() => {})}>{t('Open log folder')}</button>
            <button className="btn" onClick={() => rpc('app.openDataDir').catch((e) => notify((e as Error).message))}>
              Open data folder
            </button>
          </div>
        </div>
        <div className="card">
          <div className="card-title">{t('Notes')}</div>
          <p className="muted">Downloads are cached in assets/objects; interrupted files keep .part for resume.。</p>
          <div className="row-actions" style={{ marginTop: 10, alignItems: "center" }}>
            <button
              className="btn sm"
              onClick={() =>
                layerMsg(`Layui ${layuiVersion()} Ready`).catch(() => notify("layui Load failed"))
              }
            >
              Test Layui layer
            </button>
            <button
              className="btn sm"
              onClick={() => openLayuiPreview().catch(() => notify("layui Component failed to load"))}
            >
              Layui Component preview
            </button>
            <span className="muted">layui {layuiVersion()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
