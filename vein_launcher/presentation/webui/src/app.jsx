import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { call } from './bridge.js';

const PAGES = [
  ['home', '启动', '▷'],
  ['versions', '版本', '▤'],
  ['download', '下载', '↓'],
  ['mods', '模组', '▦'],
  ['accounts', '账号', '◉'],
  ['settings', '设置', '⚙'],
];

const LOADERS = [
  { key: '', title: '原版', desc: 'Vanilla' },
  { key: 'fabric', title: 'Fabric', desc: '轻量模组' },
  { key: 'quilt', title: 'Quilt', desc: 'Fabric 分支' },
  { key: 'forge', title: 'Forge', desc: '经典模组' },
  { key: 'neoforge', title: 'NeoForge', desc: '1.20.2+' },
];

function clock() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false });
}

export function App() {
  const [page, setPage] = useState('home');
  const [toast, setToast] = useState('');
  const [info, setInfo] = useState(null);
  const [installed, setInstalled] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selected, setSelected] = useState('');

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
        const meta = await call('app.info');
        if (!alive) return;
        setInfo(meta);
        await Promise.all([refreshInstalled(), refreshAccounts()]);
      } catch (err) {
        notify(`初始化失败：${err.message}`);
      }
    })();

    const onNavigate = (event) => setPage(event.detail);
    const onNotify = (event) => notify(`${event.detail.title}：${event.detail.message}`);
    window.addEventListener('vein:navigate', onNavigate);
    window.addEventListener('vein:notify', onNotify);
    return () => {
      alive = false;
      window.removeEventListener('vein:navigate', onNavigate);
      window.removeEventListener('vein:notify', onNotify);
    };
  }, [notify, refreshInstalled, refreshAccounts]);

  const current = PAGES.find((p) => p[0] === page) || PAGES[0];
  const account = accounts.find((a) => a.selected) || null;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">V</div>
          <div>
            <div className="brand-name">VEIN</div>
            <div className="brand-ver">{info ? info.version : '—'}</div>
          </div>
        </div>

        <nav className="nav">
          {PAGES.map(([key, label, icon]) => (
            <button
              key={key}
              className={`nav-item ${page === key ? 'active' : ''}`}
              onClick={() => setPage(key)}
            >
              <span className="ico">{icon}</span>
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <span>账号 {account ? account.username : '未登录'}</span>
          <span>实例 {installed.length}</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <h1>{current[1]}</h1>
          <span className="sub">
            {page === 'home' && (selected || '未选择实例')}
            {page === 'mods' && 'MODRINTH'}
            {page === 'download' && '选择版本 → 选择加载器 → 安装'}
            {page === 'accounts' && `${accounts.length} 个本地账号`}
          </span>
          <div className="spacer" />
          <span className={`status-dot ${installed.length ? 'on' : ''}`} />
          <span className="status-text">
            {installed.length ? `已安装 ${installed.length} 个版本` : '尚无可用实例'}
          </span>
        </header>

        <div className="content">
          {page === 'home' && (
            <HomePage
              installed={installed}
              accounts={accounts}
              selected={selected}
              onSelect={setSelected}
              notify={notify}
              onGoDownload={() => setPage('download')}
            />
          )}
          {page === 'versions' && (
            <VersionsPage installed={installed} onChange={refreshInstalled} notify={notify} />
          )}
          {page === 'download' && (
            <DownloadPage installed={installed} onChange={refreshInstalled} notify={notify} />
          )}
          {page === 'mods' && <ModsPage installed={installed} selected={selected} notify={notify} />}
          {page === 'accounts' && (
            <AccountsPage accounts={accounts} onChange={refreshAccounts} notify={notify} />
          )}
          {page === 'settings' && <SettingsPage info={info} notify={notify} />}
        </div>
      </main>

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function Empty({ children }) {
  return <div className="empty">{children}</div>;
}

function HomePage({ installed, accounts, selected, onSelect, notify, onGoDownload }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const account = accounts.find((a) => a.selected) || null;

  const launch = async () => {
    if (!selected) {
      notify('请先安装一个版本');
      onGoDownload();
      return;
    }
    setBusy(true);
    setStatus('正在构建启动参数…');
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
      <div className="panel">
        <div className="panel-head">
          <h2>启动游戏</h2>
          <span className="count">{installed.length} 个实例</span>
          <div className="spacer" />
          <span className="count">{account ? `离线 · ${account.username}` : '未登录（离线模式）'}</span>
        </div>

        {installed.length === 0 ? (
          <Empty>
            还没有安装任何版本。
            <button className="btn primary sm" style={{ marginLeft: 10 }} onClick={onGoDownload}>
              去下载
            </button>
          </Empty>
        ) : (
          <>
            <div className="row">
              <div className="grow">
                <div className="name">选择实例</div>
                <div className="meta">instances 目录</div>
              </div>
              <select value={selected} onChange={(e) => onSelect(e.target.value)}>
                {installed.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.id}
                  </option>
                ))}
              </select>
            </div>

            <div className="row">
              <div className="grow">
                <div className="name">启动游戏</div>
                <div className="meta">{status || '构建命令并拉起 Java 进程'}</div>
              </div>
              <button className="btn primary" onClick={launch} disabled={busy}>
                {busy ? '启动中…' : '启动'}
              </button>
            </div>
          </>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>当前账号</h2>
        </div>
        {account ? (
          <div className="kv">
            <div className="k">用户名</div>
            <div className="v">{account.username}</div>
          </div>
        ) : (
          <Empty>未登录。到「账号」页添加一个离线账号。</Empty>
        )}
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
    <div className="panel">
      <div className="panel-head">
        <h2>已安装版本</h2>
        <span className="count">{installed.length}</span>
      </div>
      {installed.length === 0 ? (
        <Empty>还没有已安装的版本</Empty>
      ) : (
        installed.map((v) => (
          <div className="row" key={v.id}>
            <div className="grow">
              <div className="name">{v.id}</div>
              <div className="meta">{v.type || 'release'}</div>
            </div>
            <button className="btn sm" onClick={() => remove(v.id)}>
              删除
            </button>
          </div>
        ))
      )}
    </div>
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
      log(`版本列表已更新，共 ${list.length} 个版本`);
    } catch (err) {
      log(`获取版本列表失败：${err.message}`);
      notify(`获取版本列表失败：${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [log, notify]);

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
    log(`开始安装 ${targetId}（${loader || '原版'}）`);
    try {
      const result = await call('versions.install', picked.id, loader);
      if (result.version_id) {
        log(`加载器安装完成：${result.version_id}（loader ${result.loader_version}）`);
      } else {
        log(`安装完成：成功 ${result.ok} 个 / 失败 ${result.failed} 个文件`);
      }
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
    <div className="download-layout">
      <div className="panel">
        <div className="panel-head">
          <h2>选择版本</h2>
          <span className="count">{shown.length}</span>
          <div className="spacer" />
          <input
            className="input"
            placeholder="搜索版本号"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <button className="btn ghost sm" onClick={load} disabled={loading}>
            {loading ? '加载中' : '刷新'}
          </button>
        </div>

        {loading && versions.length === 0 ? (
          <Empty>正在获取版本清单…</Empty>
        ) : shown.length === 0 ? (
          <Empty>没有匹配的版本</Empty>
        ) : (
          <div className="version-list">
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
                  <div className="name">{v.id}</div>
                  <div className="meta">{v.release_time}</div>
                </div>
                {installedIds.has(v.id) && <span className="tag ok">已装</span>}
                <span className="tag">{v.type}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>安装配置</h2>
        </div>

        {!picked ? (
          <Empty>先在左侧选择一个版本</Empty>
        ) : (
          <>
            <div className="kv">
              <div className="k">目标版本</div>
              <div className="v">{picked.id}</div>
            </div>
            <div className="kv">
              <div className="k">实例 ID</div>
              <div className="v">{targetId}</div>
            </div>

            <div style={{ marginTop: 14, marginBottom: 6, fontSize: 12, color: 'var(--text-2)' }}>
              加载器
            </div>
            <div className="loader-grid">
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
              <>
                <div className="progress" style={{ marginBottom: 6 }}>
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
                <div className="meta">
                  {progress.total
                    ? `${progress.downloaded} / ${progress.total} 个文件`
                    : '准备中…'}
                </div>
              </>
            )}

            <div className="row" style={{ marginTop: 12, borderTop: '1px solid var(--line)', paddingTop: 14 }}>
              <div className="grow">
                <div className="name">{already ? '这个实例已存在' : '开始安装'}</div>
                <div className="meta">文件会下载到实例目录</div>
              </div>
              <button className="btn primary" onClick={install} disabled={busy}>
                {busy ? '安装中…' : already ? '重新安装' : '安装'}
              </button>
            </div>

            <div className="activity">
              {activity.length === 0 ? '（下载进度会显示在这里）' : activity.join('\n')}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
function ModsPage({ selected, notify }) {
  const [query, setQuery] = useState('');
  const [type, setType] = useState('mod');
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState(false);
  const [installing, setInstalling] = useState('');

  const search = async () => {
    if (!query.trim()) return;
    setBusy(true);
    try {
      const list = await call('mods.search', query.trim(), type, selected || '', 'fabric');
      setResults(list);
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
      notify(`已安装：${result.installed ?? result.files ?? 1} 个文件`);
    } catch (err) {
      notify(`安装失败：${err.message}`);
    } finally {
      setInstalling('');
    }
  };

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Modrinth</h2>
        <span className="count">{results.length}</span>
        <div className="spacer" />
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="mod">模组</option>
          <option value="plugin">服务器插件</option>
          <option value="modpack">整合包</option>
          <option value="resourcepack">资源包</option>
          <option value="shader">光影</option>
          <option value="datapack">数据包</option>
        </select>
        <input
          className="input"
          placeholder="搜索关键词"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
        />
        <button className="btn sm" onClick={search} disabled={busy}>
          {busy ? '搜索中' : '搜索'}
        </button>
      </div>

      <div className="meta" style={{ marginBottom: 10 }}>
        目标实例：{selected || '未选择'}
      </div>

      {results.length === 0 ? (
        <Empty>输入关键词搜索 Modrinth 资源</Empty>
      ) : (
        results.map((item) => (
          <div className="row" key={item.slug}>
            <div className="grow">
              <div className="name">{item.title}</div>
              <div className="meta">
                {item.author} · ⬇ {item.downloads.toLocaleString()}
              </div>
              <div className="meta" style={{ marginTop: 3 }}>
                {item.description}
              </div>
            </div>
            <button
              className="btn sm"
              onClick={() => install(item.slug)}
              disabled={installing === item.slug}
            >
              {installing === item.slug ? '安装中…' : '安装'}
            </button>
          </div>
        ))
      )}
    </div>
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

  const select = async (id) => {
    await call('accounts.select', id);
    await onChange();
  };

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>离线账号</h2>
        <span className="count">{accounts.length}</span>
      </div>

      {accounts.length === 0 ? (
        <Empty>还没有账号。添加一个离线用户名即可启动游戏。</Empty>
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
              <button className="btn sm" onClick={() => select(acc.id)}>
                设为当前
              </button>
            )}
          </div>
        ))
      )}

      <div
        className="row"
        style={{ marginTop: 12, borderTop: '1px solid var(--line)', paddingTop: 12 }}
      >
        <input
          className="input"
          placeholder="3–16 个字符"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
        />
        <button className="btn primary sm" onClick={add} disabled={!name.trim()}>
          添加
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
function SettingsPage({ info, notify }) {
  const [runtimes, setRuntimes] = useState([]);
  const [busy, setBusy] = useState(false);

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
      <div className="panel">
        <div className="panel-head">
          <h2>关于</h2>
        </div>
        <div className="kv"><div className="k">版本</div><div className="v">{info ? info.version : '—'}</div></div>
        <div className="kv"><div className="k">数据目录</div><div className="v">{info ? info.dataDir : '—'}</div></div>
        <div className="kv"><div className="k">架构</div><div className="v">Python + PySide6 WebView + React</div></div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Java 运行时</h2>
          <span className="count">{runtimes.length}</span>
          <div className="spacer" />
          <button className="btn sm" onClick={detect} disabled={busy}>
            {busy ? '探测中' : '自动探测'}
          </button>
        </div>
        {runtimes.length === 0 ? (
          <Empty>点击「自动探测」扫描本机 Java（注册表 / JAVA_HOME / PATH）</Empty>
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
