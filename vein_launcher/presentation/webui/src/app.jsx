import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { call } from './bridge.js';

const PAGES = [
  { key: 'home', label: '启动', icon: '▶' },
  { key: 'download', label: '下载', icon: '↓' },
  { key: 'versions', label: '版本', icon: '▤' },
  { key: 'mods', label: '模组', icon: '▦' },
  { key: 'plugins', label: '插件', icon: '⌘' },
  { key: 'accounts', label: '账号', icon: '◉' },
  { key: 'settings', label: '设置', icon: '⚙' },
];

const LOADERS = [
  { key: '', title: '原版', desc: 'Vanilla' },
  { key: 'fabric', title: 'Fabric', desc: '轻量模组' },
  { key: 'quilt', title: 'Quilt', desc: 'Fabric 分支' },
  { key: 'forge', title: 'Forge', desc: '经典模组' },
  { key: 'neoforge', title: 'NeoForge', desc: '1.20.2+' },
];

const clock = () => new Date().toLocaleTimeString('zh-CN', { hour12: false });

export function App() {
  const [page, setPage] = useState('home');
  const [toast, setToast] = useState('');
  const [installed, setInstalled] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selected, setSelected] = useState('');
  const [gameLogs, setGameLogs] = useState([]);

  const notify = useCallback((message) => {
    setToast(String(message));
    window.clearTimeout(notify._timer);
    notify._timer = window.setTimeout(() => setToast(''), 3600);
  }, []);

  const refreshInstalled = useCallback(async () => {
    const list = await call('versions.info');
    setInstalled(list);
    setSelected((prev) => (prev && list.some((v) => v.id === prev) ? prev : list[0]?.id || ''));
  }, []);

  const refreshAccounts = useCallback(async () => {
    setAccounts(await call('accounts.list'));
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        await Promise.all([refreshInstalled(), refreshAccounts()]);
      } catch (err) {
        if (alive) notify(`初始化失败：${err.message}`);
      }
    })();
    const onNavigate = (event) => setPage(event.detail);
    const onLog = (event) => setGameLogs((prev) => [...prev.slice(-299), String(event.detail)]);
    window.addEventListener('vein:navigate', onNavigate);
    window.addEventListener('vein:log', onLog);
    return () => {
      alive = false;
      window.removeEventListener('vein:navigate', onNavigate);
      window.removeEventListener('vein:log', onLog);
    };
  }, [notify, refreshInstalled, refreshAccounts]);

  const account = accounts.find((a) => a.selected) || null;

  return (
    <div className="shell">
      <aside className="rail">
        <div className="rail-logo">V</div>
        <nav className="rail-nav">
          {PAGES.map((item) => (
            <button
              key={item.key}
              className={`rail-btn ${page === item.key ? 'active' : ''}`}
              onClick={() => setPage(item.key)}
              title={item.label}
            >
              <span className="ico">{item.icon}</span>
              <span className="txt">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="rail-foot">v0.0.1</div>
      </aside>

      <main className="stage">
        {page === 'home' && (
          <HomePage
            installed={installed}
            accounts={accounts}
            selected={selected}
            onSelect={setSelected}
            notify={notify}
            goDownload={() => setPage('download')}
            goAccounts={() => setPage('accounts')}
            pickVersion={(id) => setPage('download')}
            logs={gameLogs}
          />
        )}
        {page === 'download' && (
          <DownloadPage installed={installed} onChange={refreshInstalled} notify={notify} />
        )}
        {page === 'versions' && (
          <VersionsPage installed={installed} onChange={refreshInstalled} notify={notify} />
        )}
        {page === 'mods' && <ModsPage selected={selected} notify={notify} />}
        {page === 'plugins' && <PluginsPage notify={notify} />}
        {page === 'accounts' && (
          <AccountsPage accounts={accounts} onChange={refreshAccounts} notify={notify} />
        )}
        {page === 'settings' && <SettingsPage notify={notify} />}
      </main>

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function HomePage({ installed, accounts, selected, onSelect, notify, goDownload, goAccounts, logs }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [latest, setLatest] = useState([]);
  const account = accounts.find((a) => a.selected) || null;
  const current = installed.find((v) => v.id === selected);

  useEffect(() => {
    let alive = true;
    call('versions.remote', 6)
      .then((list) => alive && setLatest(list))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  const launch = async () => {
    if (!selected) {
      notify('还没有可用版本，先去下载一个');
      goDownload();
      return;
    }
    setBusy(true);
    setStatus('正在启动…');
    try {
      const result = await call('launch', selected, account ? account.username : 'Player');
      setStatus(`已启动，PID ${result.pid}`);
    } catch (err) {
      setStatus('');
      notify(`启动失败：${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>主界面</h1>
        <span className="desc">{account ? `离线账号 ${account.username}` : '未登录'}</span>
      </div>

      <div className="home-grid">
        <div>
          <div className="card version-card">
            <div className="version-label">当前版本</div>
            {installed.length === 0 ? (
              <div className="version-name">未安装</div>
            ) : (
              <select
                value={selected}
                onChange={(e) => onSelect(e.target.value)}
                style={{ marginTop: 6, fontSize: 18, fontWeight: 700, border: 'none', padding: '4px 0', boxShadow: 'none', background: 'transparent' }}
              >
                {installed.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.id}
                  </option>
                ))}
              </select>
            )}
            <div className="version-meta" style={{ marginTop: 8 }}>
              <span className="tag">{current ? current.type : '—'}</span>
              <span className="tag">{installed.length} 个实例</span>
              <span className="tag">{status || '就绪'}</span>
            </div>

            <button className="launch-btn" onClick={launch} disabled={busy}>
              {busy ? '启动中…' : '启动游戏'}
            </button>

            <div className="quick">
              <button className="quick-btn" onClick={goDownload}>
                <div className="t">下载新版本</div>
                <div className="d">原版 / Fabric / Forge</div>
              </button>
              <button className="quick-btn" onClick={goAccounts}>
                <div className="t">账号管理</div>
                <div className="d">离线 / 微软</div>
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">最新正式版本</div>
          {latest.length === 0 ? (
            <div className="empty">正在获取版本清单…</div>
          ) : (
            latest.map((v) => (
              <div className="release-row" key={v.id}>
                <div className="grow">
                  <div className="n">{v.id}</div>
                  <div className="m">{v.release_time}</div>
                </div>
                <button className="btn sm" onClick={goDownload}>
                  安装
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">游戏日志</div>
        {logs.length === 0 ? (
          <div className="empty">启动游戏后，Python 会把游戏进程输出实时推送到这里</div>
        ) : (
          <div className="activity" style={{ maxHeight: 220, marginTop: 0 }}>
            {logs.join('\n')}
          </div>
        )}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function PluginsPage({ notify }) {
  const [state, setState] = useState({ host: {}, plugins: [] });
  const [logs, setLogs] = useState([]);
  const [busy, setBusy] = useState('');

  const refresh = useCallback(async () => {
    try {
      const data = await call('plugins.state');
      setState(data);
      setLogs(await call('plugins.logs', 200));
    } catch (err) {
      notify(`读取插件状态失败：${err.message}`);
    }
  }, [notify]);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const toggle = async (plugin) => {
    setBusy(plugin.name);
    try {
      await call('plugins.setEnabled', plugin.name, !plugin.enabled);
      await refresh();
    } catch (err) {
      notify(`操作失败：${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const reload = async (plugin) => {
    setBusy(plugin.name);
    try {
      await call('plugins.reload', plugin.name);
      await refresh();
      notify(`${plugin.displayName} 已重载`);
    } catch (err) {
      notify(`重载失败：${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const install = async (name) => {
    try {
      await call('plugins.installExample', name);
      await refresh();
      notify(`已安装示例：${name}`);
    } catch (err) {
      notify(`安装失败：${err.message}`);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>插件</h1>
        <span className="desc">
          宿主 {state.host.running ? `运行中 pid=${state.host.pid}` : '未启动'}
          {state.plugins.length ? ` · ${state.plugins.length} 个插件` : ''}
        </span>
      </div>

      <div className="card">
        <div className="card-title">已安装插件</div>
        {state.plugins.length === 0 ? (
          <div className="empty">
            还没有插件。可以先安装示例插件体验双向 RPC 与权限沙箱。
            <div style={{ marginTop: 12, display: 'flex', gap: 10, justifyContent: 'center' }}>
              <button className="btn sm" onClick={() => install('template')}>
                安装插件模板
              </button>
              <button className="btn primary sm" onClick={() => install('game-log')}>
                安装日志示例
              </button>
            </div>
          </div>
        ) : (
          state.plugins.map((plugin) => (
            <div className="row" key={plugin.name}>
              <div className="grow">
                <div className="name">
                  {plugin.displayName}
                  <span className="meta" style={{ marginLeft: 8 }}>v{plugin.version}</span>
                </div>
                <div className="meta">{plugin.description || plugin.name}</div>
                <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                  {(plugin.permissions || []).map((perm) => (
                    <span className="tag" key={perm}>{perm}</span>
                  ))}
                  {plugin.loaded && <span className="tag ok">已加载</span>}
                </div>
              </div>
              <button className="btn sm" onClick={() => reload(plugin)} disabled={busy === plugin.name}>
                重载
              </button>
              <button
                className={plugin.enabled ? 'btn sm' : 'btn primary sm'}
                onClick={() => toggle(plugin)}
                disabled={busy === plugin.name}
              >
                {plugin.enabled ? '禁用' : '启用'}
              </button>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <div className="card-title">宿主日志</div>
        {logs.length === 0 ? (
          <div className="empty">暂无日志</div>
        ) : (
          <div className="activity" style={{ maxHeight: 240, marginTop: 0 }}>
            {logs.join('\n')}
          </div>
        )}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function DownloadPage({ installed, onChange, notify }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [picked, setPicked] = useState(null);
  const [loader, setLoader] = useState('');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(null);
  const [activity, setActivity] = useState([]);

  const log = useCallback((text) => {
    setActivity((prev) => [...prev.slice(-199), `[${clock()}] ${text}`]);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await call('versions.remote', 120);
      setVersions(list);
      log(`版本列表已更新，共 ${list.length} 个`);
    } catch (err) {
      log(`获取失败：${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [log]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const onProgress = (event) => {
      const { taskId, downloaded, total } = event.detail;
      if (!picked || taskId !== picked.id) return;
      setProgress({ downloaded, total });
    };
    window.addEventListener('vein:progress', onProgress);
    return () => window.removeEventListener('vein:progress', onProgress);
  }, [picked]);

  const installedIds = useMemo(() => new Set(installed.map((v) => v.id)), [installed]);
  const shown = versions.filter((v) => !filter || v.id.includes(filter));
  const targetId = picked ? (loader ? `${loader}-${picked.id}` : picked.id) : '';
  const already = targetId && installedIds.has(targetId);

  const install = async () => {
    if (!picked) return;
    setBusy(true);
    setProgress({ downloaded: 0, total: 0 });
    log(`开始安装 ${targetId}`);
    try {
      const result = await call('versions.install', picked.id, loader);
      if (result.version_id) log(`加载器安装完成：${result.version_id}（loader ${result.loader_version}）`);
      else log(`安装完成：成功 ${result.ok} / 失败 ${result.failed}`);
      await onChange();
    } catch (err) {
      log(`安装失败：${err.message}`);
      notify(`安装失败：${err.message}`);
    } finally {
      setBusy(false);
      setProgress(null);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>下载</h1>
        <span className="desc">选择版本 → 选择加载器 → 安装</span>
      </div>

      <div className="download-grid">
        <div className="card">
          <div className="row" style={{ paddingTop: 0 }}>
            <div className="grow">
              <div className="name">版本列表</div>
              <div className="meta">{shown.length} 个</div>
            </div>
            <input
              className="input"
              placeholder="搜索版本号"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ width: 160 }}
            />
            <button className="btn sm" onClick={load} disabled={loading}>
              {loading ? '加载中' : '刷新'}
            </button>
          </div>

          {loading && versions.length === 0 ? (
            <div className="empty">正在获取版本清单…</div>
          ) : (
            <div className="version-list" style={{ marginTop: 8 }}>
              {shown.map((v) => (
                <div
                  key={v.id}
                  className={`version-item ${picked?.id === v.id ? 'active' : ''}`}
                  onClick={() => {
                    setPicked(v);
                    setLoader('');
                    setProgress(null);
                  }}
                >
                  <div className="grow">
                    <div className="n">{v.id}</div>
                    <div className="m">{v.release_time}</div>
                  </div>
                  {installedIds.has(v.id) && <span className="tag ok">已装</span>}
                  <span className="tag">{v.type}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">安装配置</div>
          {!picked ? (
            <div className="empty">先在左侧选择一个版本</div>
          ) : (
            <>
              <div className="kv"><div className="k">版本</div><div className="v">{picked.id}</div></div>
              <div className="kv"><div className="k">实例 ID</div><div className="v">{targetId}</div></div>

              <div className="loader-grid" style={{ marginTop: 14 }}>
                {LOADERS.map((item) => (
                  <button
                    key={item.key || 'vanilla'}
                    className={`loader-card ${loader === item.key ? 'active' : ''}`}
                    onClick={() => setLoader(item.key)}
                  >
                    <div className="t">{item.title}</div>
                    <div className="d">{item.desc}</div>
                  </button>
                ))}
              </div>

              {progress && (
                <div style={{ marginTop: 12 }}>
                  <div className="progress">
                    <i
                      style={{
                        width: `${
                          progress.total
                            ? Math.min(100, Math.round((progress.downloaded / progress.total) * 100))
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                  <div className="m" style={{ marginTop: 6, color: 'var(--text-3)', fontSize: 11 }}>
                    {progress.total ? `${progress.downloaded} / ${progress.total} 个文件` : '准备中…'}
                  </div>
                </div>
              )}

              <button
                className="btn primary"
                style={{ width: '100%', marginTop: 16, height: 44, fontSize: 15 }}
                onClick={install}
                disabled={busy}
              >
                {busy ? '安装中…' : already ? '重新安装' : '开始安装'}
              </button>

              <div className="activity">
                {activity.length === 0 ? '（安装进度会显示在这里）' : activity.join('\n')}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function VersionsPage({ installed, onChange, notify }) {
  const remove = async (id) => {
    try {
      await call('versions.delete', id);
      await onChange();
      notify(`已删除 ${id}`);
    } catch (err) {
      notify(`删除失败：${err.message}`);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>版本</h1>
        <span className="desc">{installed.length} 个已安装实例</span>
      </div>

      <div className="card">
        {installed.length === 0 ? (
          <div className="empty">还没有已安装的版本</div>
        ) : (
          <div className="installed-grid">
            {installed.map((v) => (
              <div className="installed-card" key={v.id}>
                <div className="n">{v.id}</div>
                <div className="m">{v.type || 'release'}</div>
                <div className="ops">
                  <button className="btn sm" onClick={() => remove(v.id)}>
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function ModsPage({ selected, notify }) {
  const [tab, setTab] = useState('featured');
  const [type, setType] = useState('mod');
  const [query, setQuery] = useState('');
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [installing, setInstalling] = useState('');
  const [loaded, setLoaded] = useState(false);

  const loadFeatured = useCallback(
    async (projectType) => {
      setBusy(true);
      try {
        setItems(await call('mods.featured', projectType, selected || '', 'fabric', 24));
        setLoaded(true);
      } catch (err) {
        notify(`获取推荐失败：${err.message}`);
      } finally {
        setBusy(false);
      }
    },
    [selected, notify]
  );

  useEffect(() => {
    if (tab === 'featured') loadFeatured(type);
  }, [tab, type, loadFeatured]);

  const search = async () => {
    if (!query.trim()) return;
    setBusy(true);
    try {
      setItems(await call('mods.search', query.trim(), type, selected || '', 'fabric'));
      setLoaded(true);
    } catch (err) {
      notify(`搜索失败：${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const install = async (slug) => {
    if (!selected) {
      notify('请先安装一个实例');
      return;
    }
    setInstalling(slug);
    try {
      const result = await call('mods.install', slug, selected, type, 'fabric');
      notify(`已安装：${result.installed ?? result.files ?? 1}`);
    } catch (err) {
      notify(`安装失败：${err.message}`);
    } finally {
      setInstalling('');
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>模组</h1>
        <span className="desc">目标实例：{selected || '未选择'}</span>
      </div>

      <div className="card">
        <div className="row" style={{ paddingTop: 0 }}>
          <div style={{ display: 'flex', gap: 4, background: 'var(--card-2)', padding: 4, borderRadius: 10 }}>
            <button
              className={tab === 'featured' ? 'btn primary sm' : 'btn ghost sm'}
              style={{ border: 0, boxShadow: 'none' }}
              onClick={() => setTab('featured')}
            >
              推荐
            </button>
            <button
              className={tab === 'search' ? 'btn primary sm' : 'btn ghost sm'}
              style={{ border: 0, boxShadow: 'none' }}
              onClick={() => setTab('search')}
            >
              搜索
            </button>
          </div>

          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="mod">模组</option>
            <option value="plugin">服务器插件</option>
            <option value="modpack">整合包</option>
            <option value="resourcepack">资源包</option>
            <option value="shader">光影</option>
            <option value="datapack">数据包</option>
          </select>

          {tab === 'search' && (
            <>
              <input
                className="input"
                placeholder="搜索 Modrinth"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && search()}
                style={{ flex: 1 }}
              />
              <button className="btn primary sm" onClick={search} disabled={busy}>
                {busy ? '搜索中' : '搜索'}
              </button>
            </>
          )}
          {tab === 'featured' && (
            <button className="btn sm" onClick={() => loadFeatured(type)} disabled={busy}>
              {busy ? '加载中' : '刷新推荐'}
            </button>
          )}
        </div>

        {busy && items.length === 0 ? (
          <div className="empty">正在加载…</div>
        ) : items.length === 0 ? (
          <div className="empty">
            {tab === 'featured' ? '暂无推荐内容（网络不可达或筛选过窄）' : '输入关键词搜索资源'}
          </div>
        ) : (
          <div className="mods-grid">
            {items.map((item) => (
              <div className="mod-card" key={item.slug}>
                {item.icon ? (
                  <img className="mod-icon" src={item.icon} alt={item.title} loading="lazy" />
                ) : (
                  <div className="mod-icon mod-icon-fallback">{item.title.slice(0, 1)}</div>
                )}
                <div className="mod-body">
                  <div className="mod-title" title={item.title}>{item.title}</div>
                  <div className="mod-desc" title={item.description}>{item.description}</div>
                  <div className="mod-foot">
                    <span className="mod-downloads">⬇ {Number(item.downloads || 0).toLocaleString()}</span>
                    <button
                      className="btn primary sm"
                      onClick={() => install(item.slug)}
                      disabled={installing === item.slug}
                    >
                      {installing === item.slug ? '安装中' : '安装'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function AccountsPage({ accounts, onChange, notify }) {
  const [name, setName] = useState('');

  const add = async () => {
    try {
      await call('accounts.add', name.trim());
      setName('');
      await onChange();
      notify('账号已添加');
    } catch (err) {
      notify(`添加失败：${err.message}`);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>账号</h1>
        <span className="desc">{accounts.length} 个本地账号</span>
      </div>

      <div className="card">
        <div className="card-title">离线账号</div>
        {accounts.length === 0 ? (
          <div className="empty">还没有账号，添加一个离线用户名即可启动</div>
        ) : (
          accounts.map((acc) => (
            <div className="row" key={acc.id}>
              <div className="grow">
                <div className="name">{acc.username}</div>
                <div className="meta">{acc.id}</div>
              </div>
              {acc.selected ? (
                <span className="tag ok">当前</span>
              ) : (
                <button
                  className="btn sm"
                  onClick={async () => {
                    await call('accounts.select', acc.id);
                    await onChange();
                  }}
                >
                  设为当前
                </button>
              )}
            </div>
          ))
        )}

        <div className="row" style={{ borderTop: '1px solid var(--line)', marginTop: 6, paddingTop: 12 }}>
          <input
            className="input"
            placeholder="3–16 个字符"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && add()}
            style={{ flex: 1 }}
          />
          <button className="btn primary sm" onClick={add} disabled={!name.trim()}>
            添加
          </button>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function SettingsPage({ notify }) {
  const [info, setInfo] = useState(null);
  const [runtimes, setRuntimes] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    call('app.info').then(setInfo).catch(() => {});
  }, []);

  const detect = async () => {
    setBusy(true);
    try {
      setRuntimes(await call('java.detect'));
    } catch (err) {
      notify(`探测失败：${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>设置</h1>
        <span className="desc">运行环境与程序信息</span>
      </div>

      <div className="card">
        <div className="card-title">关于</div>
        <div className="kv"><div className="k">版本</div><div className="v">{info ? info.version : '—'}</div></div>
        <div className="kv"><div className="k">数据目录</div><div className="v">{info ? info.dataDir : '—'}</div></div>
        <div className="kv"><div className="k">架构</div><div className="v">Python + PySide6 WebView + React</div></div>
        <div className="row" style={{ paddingBottom: 0 }}>
          <div className="grow">
            <div className="name">日志目录</div>
            <div className="meta">按天一个文件，保留 30 天</div>
          </div>
          <button className="btn sm" onClick={() => call('logs.openDir')}>
            打开目录
          </button>
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ paddingTop: 0 }}>
          <div className="grow">
            <div className="name">Java 运行时</div>
            <div className="meta">{runtimes.length} 个</div>
          </div>
          <button className="btn sm" onClick={detect} disabled={busy}>
            {busy ? '探测中' : '自动探测'}
          </button>
        </div>
        {runtimes.length === 0 ? (
          <div className="empty">点击「自动探测」扫描本机 Java</div>
        ) : (
          runtimes.map((rt) => (
            <div className="row" key={rt.path}>
              <div className="grow">
                <div className="name">Java {rt.major}</div>
                <div className="meta">{rt.path}</div>
              </div>
              <span className="tag">{rt.vendor}</span>
            </div>
          ))
        )}
      </div>
    </>
  );
}
