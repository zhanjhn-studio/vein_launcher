import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import { LayuiCheckbox, LayuiProgress, RemoteIcon } from './ui';
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
      notify('还没有版本，请先去下载一个。');
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
          <div className="label">当前版本</div>
          {installed.length === 0 ? (
            <div className="hero-version">未安装</div>
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
            {busy ? '启动中…' : '启动游戏'}
          </button>
        </div>
        <div className="hero-right">
          <div className="card-title">{t('游戏日志')}</div>
          {logs.length === 0 ? (
            <Empty>启动后这里会显示游戏输出</Empty>
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
      notify('请先安装一个实例');
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
              <div className="kv"><span>实例 ID</span><b>{targetId}</b></div>
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
              <div className="kv"><span>类型</span><b>{(picked as VersionInfo).type ?? 'release'}</b></div>
              <div className="kv"><span>发布时间</span><b>{(picked as VersionInfo).release_time ?? '—'}</b></div>

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
                      <button className="btn sm" onClick={() => loadFiles(fileTarget)}>刷新</button>
                      <button className="btn sm" onClick={() => rpc('versions.openFolder', [fileTarget]).catch(() => {})}>
                        Open folder
                      </button>
                    </div>
                  </div>
                  {files.length === 0 ? (
                    <div className="empty">文件夹为空，或安装不完整</div>
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
            <Empty>选一个版本，查看安装选项</Empty>
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
          <Empty>选一项查看详情</Empty>
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
      notify(`读取插件失败：${(err as Error).message}`);
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
      notify(`操作失败：${(err as Error).message}`);
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
      notify(`${name} 已重载`);
    } catch (err) {
      notify(`重载失败：${(err as Error).message}`);
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
              { key: 'all', label: '全部', hint: String(state.plugins.length) },
              { key: 'enabled', label: '已启用', hint: String(state.plugins.filter((p) => p.enabled).length) },
              { key: 'disabled', label: '已禁用', hint: String(state.plugins.filter((p) => !p.enabled).length) },
            ]}
            active={filter}
            onPick={setFilter}
          />
        }
        middle={
          <>
            <div className="pane-head">
              <span>{t('Plugins')}</span>
              <StatusDot on={state.host.running} label={state.host.running ? `宿主进程 ${state.host.pid}` : '宿主未运行'} />
            </div>
            <div className="list">
              {shown.length === 0 && <Empty>还没有插件</Empty>}
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
                  <span className="muted">未声明权限</span>
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
              <div className="card-title" style={{ marginTop: 16 }}>宿主日志</div>
              <div className="activity">{logs.join('\n') || 'No logs'}</div>
            </div>
          ) : (
            <Empty>选一个插件，查看权限与日志</Empty>
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
  const [state, setState] = useState<MlcState>({ connected: false, pid: null, enabled: false });
  const [mlcOn, setMlcOn] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [command, setCommand] = useState('/time set day');
  const [sending, setSending] = useState(false);
  const [agent, setAgent] = useState<{ ok?: boolean; inGame?: boolean; player?: any; error?: string } | null>(null);
  const [result, setResult] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [busy, setBusy] = useState('');
  const [saveWorlds, setSaveWorlds] = useState<
    { name: string; seed: number; version: string; instance: string; path: string; folder: string }[]
  >([]);

  useEffect(() => {
    const tick = async () => {
      try {
        const next = await rpc<MlcState>('mlc.state');
        setState(next);
        setMlcOn(Boolean(next.enabled));
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
      notify('没有可用的实例');
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

  const toggleMlc = async (next: boolean) => {
    setToggling(true);
    try {
      const res = await rpc<{ enabled: boolean }>('mlc.setEnabled', [next]);
      setMlcOn(Boolean(res.enabled));
      notify(next ? 'MLC enabled' : 'MLC disabled');
    } catch (err) {
      notify(`MLC switch failed: ${(err as Error).message}`);
    } finally {
      setToggling(false);
    }
  };

  useEffect(() => {
    let alive = true;
    // 页面打开就开启事件监听（进世界/离开/切维度/死亡）
    rpc('mlc.watchStart', [1.0]).catch(() => {});
    const tick = async () => {
      try {
        const state = await rpc<{ ok?: boolean; inGame?: boolean; player?: any }>('mlc.agentState', [0]);
        if (alive) setAgent(state);
      } catch (err) {
        if (alive) setAgent({ ok: false, error: (err as Error).message });
      }
    };
    tick();
    const timer = window.setInterval(tick, 3000);
    return () => {
      alive = false;
      window.clearInterval(timer);
      rpc('mlc.watchStop').catch(() => {});
    };
  }, []);

  const sendCommand = async () => {
    if (!command.trim()) return;
    setSending(true);
    try {
      try {
        await rpc('mlc.agentChat', [command.trim(), 0]);
        notify(`Agent sent: ${command.trim()}`);
        setResult(`mlc.agentChat → ${command.trim()}`);
      } catch {
        const result = await rpc<{ sent: boolean }>('game.command', [command.trim(), 0]);
        notify(result.sent ? `Sent: ${command.trim()}` : 'Command not sent');
        setResult(`game.command → ${command.trim()}`);
      }
    } catch (err) {
      notify(`Send failed: ${(err as Error).message}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="page">
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Vanilla control</div>
        <p className="muted" style={{ marginTop: 0 }}>
          Types the command into the running Minecraft window and presses Enter — works in vanilla, no mods.
        </p>
        <div className="kv">
          <span>Agent</span>
          <b>
            {agent?.ok === false
              ? 'offline'
              : agent?.inGame
              ? `in game · ${agent.player?.x?.toFixed?.(1) ?? '?'}, ${agent.player?.y?.toFixed?.(1) ?? '?'}, ${agent.player?.z?.toFixed?.(1) ?? '?'}`
              : 'connected · menu'}
          </b>
        </div>
        <div className="row-actions">
          <input
            className="input"
            value={command}
            placeholder="/time set day"
            onChange={(event) => setCommand(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') sendCommand();
            }}
          />
          <button className="btn primary" onClick={sendCommand} disabled={sending || !command.trim()}>
            {sending ? 'Sending…' : 'Send to game'}
          </button>
        </div>
      </div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="switch-row">
          <div className="switch-copy">
            <div className="switch-title">MLC master switch</div>
            <p className="muted" style={{ margin: '6px 0 0' }}>
              When off, MLC data calls (saves, player data, mod install) are rejected.
            </p>
          </div>
          <div className="switch-control">
            <span className={`switch-state ${mlcOn ? 'on' : ''}`}>{mlcOn ? 'On' : 'Off'}</span>
            <LayuiCheckbox
              checked={mlcOn}
              disabled={toggling}
              onChange={toggleMlc}
              label=""
            />
          </div>
        </div>
      </div>
      <div className="pane-head">
        <span>VL-MLC 控制层</span>
        <StatusDot
          on={state.connected}
          label={state.connected ? `Connected · pid ${state.pid}` : 'Disconnected'}
          tone="ok"
        />
      </div>
      <div className="cards">
        <div className="card">
          <div className="card-title">{t('Connection')}</div>
          <div className="kv"><span>状态</span><b>{state.connected ? '运行中' : '空闲'}</b></div>
          <div className="kv"><span>实例</span><b>{selected || '—'}</b></div>
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
          <pre className="activity">{result || t('(Results appear here)')}</pre>
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <div className="pane-head" style={{ padding: '0 0 10px', border: 0 }}>
          <span>MC2 · 世界数据</span>
          <button className="btn sm" onClick={loadWorlds} disabled={busy === 'mc2'}>
            {busy === 'mc2' ? '…' : 'Scan saves'}
          </button>
        </div>
        {saveWorlds.length === 0 ? (
          <div className="empty">没找到存档。先在游戏里创建世界，再扫描一次。</div>
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
            <div className="empty">这个世界没有 region 文件。</div>
          )}
        </div>
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">{t('Event stream')}</div>
        <div className="activity">{logs.join('\n') || t('MLC events appear here after launch')}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Multiplayer
export function MultiplayerPage() {
  return (
    <div className="page center">
      <h2>联机</h2>
      <p className="muted">即将推出</p>
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
              <h2>关于</h2>
              <div className="kv"><span>{t('Versions')}</span><b>{info?.version ?? '—'}</b></div>
              <div className="kv"><span>数据目录</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
              <div className="kv"><span>架构</span><b>Python + PySide6 WebView + React + TS</b></div>
            </>
          )}
          {section === 'java' && (
            <>
              <h2>Java 环境</h2>
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
                <Empty>点「检测」扫描本机 Java</Empty>
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
              <h2>游戏目录（.minecraft）</h2>
              <p className="muted">
                Use an existing .minecraft directory, or keep the launcher-managed one.。
              </p>
              <div className="kv">
                <span>当前</span>
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
              <h2>语言</h2>
              <p className="muted">切换立即生效并自动保存。</p>
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
                  Chinese (Simplified)
                </button>
              </div>
            </>
          )}
          {section === 'logs' && (
            <>
              <h2>日志</h2>
              <p className="muted">按天写入 VeinLauncher/log/YYYY-MM-DD.log</p>
              <button className="btn" onClick={() => rpc('logs.openDir').catch(() => {})}>
                Open log folder
              </button>
            </>
          )}
        </div>
      }
      right={<Empty>选一个设置分组</Empty>}
    />
  );
}

