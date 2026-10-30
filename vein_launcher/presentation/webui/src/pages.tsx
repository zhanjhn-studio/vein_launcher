import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
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
  { key: 'vanilla', label: '游戏本体' },
  { key: 'modpack', label: '整合包' },
  { key: 'mod', label: '模组' },
  { key: 'plugin', label: '服务器插件' },
  { key: 'resourcepack', label: '资源包' },
  { key: 'shader', label: '光影' },
  { key: 'datapack', label: '数据包' },
];

const LOADERS = [
  { key: '', title: '原版', desc: 'Vanilla' },
  { key: 'fabric', title: 'Fabric', desc: '轻量模组' },
  { key: 'quilt', title: 'Quilt', desc: 'Fabric 分支' },
  { key: 'forge', title: 'Forge', desc: '经典模组' },
  { key: 'neoforge', title: 'NeoForge', desc: '1.20.2+' },
];

// ---------------------------------------------------------------- 启动
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
      notify('还没有可用版本，先去下载');
      return;
    }
    setBusy(true);
    setStatus('正在启动…');
    try {
      const result = await rpc<{ pid: number }>('launch', [selected, account?.username ?? 'Player']);
      setStatus(`已启动，PID ${result.pid}`);
    } catch (err) {
      setStatus('');
      notify(`启动失败：${(err as Error).message}`);
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
            <span className="chip">{account ? `离线 · ${account.username}` : '未登录'}</span>
            <span className="chip">{installed.length} 个实例</span>
            <span className="chip">{status || '就绪'}</span>
          </div>
          <button className="launch-btn" onClick={launch} disabled={busy}>
            {busy ? '启动中…' : '启动游戏'}
          </button>
        </div>
        <div className="hero-right">
          <div className="card-title">{t('游戏日志')}</div>
          {logs.length === 0 ? (
            <Empty>启动后这里会实时显示游戏输出</Empty>
          ) : (
            <div className="log-view">{logs.join('\n')}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- 下载
export function DownloadPage({
  installed,
  onInstalled,
  notify,
}: {
  installed: VersionInfo[];
  onInstalled: () => Promise<void>;
  notify: (text: string) => void;
}) {
  const [category, setCategory] = useState<Category>('vanilla');
  const [items, setItems] = useState<VersionInfo[]>([]);
  const [mods, setMods] = useState<ModItem[]>([]);
  const [picked, setPicked] = useState<VersionInfo | ModItem | null>(null);
  const [pickedMod, setPickedMod] = useState<ModItem | null>(null);
  const [loader, setLoader] = useState('');
  const [busy, setBusy] = useState(false);
  const [activity, setActivity] = useState<string[]>([]);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);

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
        log(`版本列表 ${list.length} 个`);
      } else {
        const list = await rpc<ModItem[]>('mods.featured', [category, '', 'fabric', 40]);
        setMods(list);
        setItems([]);
        log(`${category} 推荐 ${list.length} 个`);
      }
    } catch (err) {
      log(`加载失败：${(err as Error).message}`);
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

  const installedIds = useMemo(() => new Set(installed.map((v) => v.id)), [installed]);
  const targetId = picked ? (loader ? `${loader}-${(picked as VersionInfo).id}` : (picked as VersionInfo).id) : '';

  const installVersion = async () => {
    if (!picked) return;
    setBusy(true);
    log(`开始安装 ${targetId}`);
    try {
      const result = await rpc<{ loader_version?: string; ok?: number; failed?: number; files?: number }>(
        'versions.install',
        [(picked as VersionInfo).id, loader]
      );
      log(
        result.loader_version
          ? `加载器安装完成：${targetId}（${result.loader_version}）`
          : `安装完成：成功 ${result.ok ?? 0} / 失败 ${result.failed ?? 0}`
      );
      await onInstalled();
    } catch (err) {
      log(`安装失败：${(err as Error).message}`);
      notify(`安装失败：${(err as Error).message}`);
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
    log(`安装 ${item.title} → ${instance}`);
    try {
      const result = await rpc<{ installed?: number; files?: number }>('mods.install', [
        item.slug,
        instance,
        category,
        'fabric',
      ]);
      log(`安装完成：${result.installed ?? result.files ?? 1} 个文件`);
    } catch (err) {
      log(`安装失败：${(err as Error).message}`);
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
            <span>{category === 'vanilla' ? '版本' : '推荐'}</span>
            <button className="btn sm" onClick={load} disabled={busy}>
              {busy ? '加载中' : '刷新'}
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
                    <span className="sub">{v.release_time}{installedIds.has(v.id) ? ' · 已安装' : ''}</span>
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
            {!busy && items.length === 0 && mods.length === 0 && <Empty>{t('暂无内容')}</Empty>}
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
                    <b>{l.title}</b>
                    <small>{l.desc}</small>
                  </button>
                ))}
              </div>
              {progress && (
                <div className="progress">
                  <i style={{ width: `${progress.total ? Math.round((progress.done / progress.total) * 100) : 0}%` }} />
                </div>
              )}
              <button className="btn primary block" onClick={installVersion} disabled={busy}>
                {busy ? '安装中…' : '开始安装'}
              </button>
              <div className="activity">{activity.join('\n') || '（进度会显示在这里）'}</div>
            </div>
          ) : (
            <Empty>选择左侧版本查看安装选项</Empty>
          )
        ) : pickedMod ? (
          <div className="detail">
            <div className="mod-head">
              {pickedMod.icon && <img src={pickedMod.icon} alt="" onError={(e) => (e.currentTarget.style.display = 'none')} />}
              <div>
                <h2>{pickedMod.title}</h2>
                <div className="muted">{pickedMod.author} · ⬇ {pickedMod.downloads.toLocaleString()}</div>
              </div>
            </div>
            <p className="desc">{pickedMod.description}</p>
            <button className="btn primary block" onClick={() => installMod(pickedMod)} disabled={busy}>
              安装到 {installed[0]?.id ?? '（无实例）'}
            </button>
            <div className="activity">{activity.join('\n') || '（安装进度会显示在这里）'}</div>
          </div>
        ) : (
          <Empty>选择左侧条目查看详情</Empty>
        )
      }
    />
  );
}

// ---------------------------------------------------------------- 插件
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
      notify(`${name} 已热重载`);
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
              <span>{t('插件')}</span>
              <StatusDot on={state.host.running} label={state.host.running ? `宿主 ${state.host.pid}` : '宿主未启动'} />
            </div>
            <div className="list">
              {shown.length === 0 && <Empty>t('还没有插件')</Empty>}
              {shown.map((p) => (
                <button
                  key={p.name}
                  className={`row-item ${current?.name === p.name ? 'active' : ''}`}
                  onClick={() => setPicked(p.name)}
                >
                  <span className="title">{p.displayName}</span>
                  <span className="sub">v{p.version} · {p.loaded ? '已加载' : p.enabled ? '待加载' : '已禁用'}</span>
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
                <div className="card-title">{t('权限')}</div>
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
                  热重载
                </button>
                {current.enabled ? (
                  <button className="btn" onClick={() => toggle(current.name, false)} disabled={busy === current.name}>
                    禁用
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
                    启用
                  </button>
                )}
              </div>
              <div className="card-title" style={{ marginTop: 16 }}>宿主日志</div>
              <div className="activity">{logs.join('\n') || '暂无日志'}</div>
            </div>
          ) : (
            <Empty>选择插件查看权限与日志</Empty>
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
    { name: string; seed: number; version: string; instance: string; path: string }[]
  >([]);

  useEffect(() => {
    const tick = async () => {
      try {
        setState(await rpc<MlcState>('mlc.state'));
      } catch {
        /* 忽略 */
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
      notify('没有可用实例');
      return;
    }
    setBusy('launch');
    try {
      const r = await rpc<{ pid: number }>('launch', [selected, 'Player']);
      setResult(`mlc.launch → pid ${r.pid}`);
    } catch (err) {
      notify(`启动失败：${(err as Error).message}`);
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
      setResult(`mlc.world.info 失败：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const loadWorlds = async () => {
    setBusy('mc2');
    try {
      const list = await rpc<{ name: string; seed: number; version: string; instance: string; path: string }[]>(
        'mc2.worlds',
        ['']
      );
      setSaveWorlds(list);
      setResult(`mc2.worlds → ${list.length} 个存档`);
    } catch (err) {
      setResult(`mc2.worlds 失败：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="page">
      <div className="pane-head">
        <span>VL-MLC 控制层</span>
        <StatusDot
          on={state.connected}
          label={state.connected ? `已连接 · pid ${state.pid}` : '未连接'}
          tone="ok"
        />
      </div>
      <div className="cards">
        <div className="card">
          <div className="card-title">{t('连接')}</div>
          <div className="kv"><span>状态</span><b>{state.connected ? '运行中' : '空闲'}</b></div>
          <div className="kv"><span>实例</span><b>{selected || '—'}</b></div>
          <div className="row-actions">
            <button className="btn primary" onClick={launch} disabled={busy === 'launch'}>
              mlc.launch
            </button>
            <button className="btn" onClick={worlds} disabled={busy === 'worlds'}>
              世界信息
            </button>
          </div>
        </div>
        <div className="card">
          <div className="card-title">{t('调用返回')}</div>
          <pre className="activity">{result || '（调用结果会显示在这里）'}</pre>
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
          <div className="empty">No saves found. Launch the game once to create a world.</div>
        ) : (
          saveWorlds.map((w) => (
            <div className="row-item" key={w.path}>
              <span className="title">{w.name}</span>
              <span className="sub">
                seed {w.seed} · {w.version || '—'} · {w.instance}
              </span>
            </div>
          ))
        )}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">{t('事件流')}</div>
        <div className="activity">{logs.join('\n') || '游戏启动后这里会显示 MLC 事件'}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- 联机
export function MultiplayerPage() {
  return (
    <div className="page center">
      <h2>联机</h2>
      <p className="muted">敬请期待</p>
    </div>
  );
}

// ---------------------------------------------------------------- 设置
export function SettingsPage({ notify }: { notify: (text: string) => void }) {
  const [section, setSection] = useState('about');
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [runtimes, setRuntimes] = useState<JavaRuntime[]>([]);

  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
  }, []);

  const detect = async () => {
    try {
      setRuntimes(await rpc<JavaRuntime[]>('java.detect'));
    } catch (err) {
      notify(`探测失败：${(err as Error).message}`);
    }
  };

  return (
    <ThreePane
      left={
        <CategoryList
          items={[
            { key: 'about', label: '关于' },
            { key: 'java', label: 'Java' },
            { key: 'logs', label: '日志' },
            { key: 'language', label: '语言 / Language' },
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
              <div className="kv"><span>{t('版本列表')}</span><b>{info?.version ?? '—'}</b></div>
              <div className="kv"><span>数据目录</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
              <div className="kv"><span>架构</span><b>Python + PySide6 WebView + React + TS</b></div>
            </>
          )}
          {section === 'java' && (
            <>
              <h2>Java 运行时</h2>
              <button className="btn" onClick={detect}>{t('自动探测')}</button>
              {runtimes.length === 0 ? (
                <Empty>点击探测扫描本机 Java</Empty>
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
          {section === 'language' && (
            <>
              <h2>Language / 语言</h2>
              <p className="muted">The launcher defaults to English. Switching applies immediately and is saved.</p>
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
              <h2>日志</h2>
              <p className="muted">按天写入 %APPDATA%\VeinLauncher\logs\YYYY-MM-DD.log</p>
              <button className="btn" onClick={() => rpc('logs.openDir').catch(() => {})}>
                打开日志目录
              </button>
            </>
          )}
        </div>
      }
      right={<Empty>选择左侧设置项</Empty>}
    />
  );
}

// ---------------------------------------------------------------- 工具箱
export function ToolboxPage({ notify }: { notify: (text: string) => void }) {
  const [info, setInfo] = useState<AppInfo | null>(null);
  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
  }, []);

  return (
    <div className="page">
      <div className="page-head"><h1>{t('工具箱')}</h1><span className="muted">快捷操作</span></div>
      <div className="cards">
        <div className="card">
          <div className="card-title">{t('目录')}</div>
          <div className="kv"><span>数据目录</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
          <div className="row-actions">
            <button className="btn" onClick={() => rpc('logs.openDir').catch(() => {})}>{t('打开日志目录')}</button>
            <button className="btn" onClick={() => rpc('app.openDataDir').catch((e) => notify((e as Error).message))}>
              打开数据目录
            </button>
          </div>
        </div>
        <div className="card">
          <div className="card-title">{t('说明')}</div>
          <p className="muted">下载缓存位于 assets/objects，下载中断会保留 .part 便于续传。</p>
          <div className="row-actions" style={{ marginTop: 10, alignItems: "center" }}>
            <button
              className="btn sm"
              onClick={() =>
                layerMsg(`Layui ${layuiVersion()} 已就绪`).catch(() => notify("layui 加载失败"))
              }
            >
              测试 Layui 弹层
            </button>
            <button
              className="btn sm"
              onClick={() => openLayuiPreview().catch(() => notify("layui 组件加载失败"))}
            >
              Layui 组件预览
            </button>
            <span className="muted">layui {layuiVersion()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
