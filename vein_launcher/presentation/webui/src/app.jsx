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

export function App() {
  const [page, setPage] = useState('home');
  const [toast, setToast] = useState('');
  const [info, setInfo] = useState(null);
  const [installed, setInstalled] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selected, setSelected] = useState('');
  const [tasks, setTasks] = useState({});
  const [logs, setLogs] = useState([]);

  const notify = useCallback((message) => {
    setToast(String(message));
    window.clearTimeout(notify._timer);
    notify._timer = window.setTimeout(() => setToast(''), 4000);
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
        const [meta] = await Promise.all([call('app.info')]);
        if (!alive) return;
        setInfo(meta);
        await Promise.all([refreshInstalled(), refreshAccounts()]);
      } catch (err) {
        notify(`初始化失败：${err.message}`);
      }
    })();

    const onProgress = (event) => {
      const { taskId, downloaded, total } = event.detail;
      setTasks((prev) => ({ ...prev, [taskId]: { downloaded, total } }));
    };
    const onLog = (event) => {
      setLogs((prev) => [...prev.slice(-199), event.detail]);
    };
    const onNotify = (event) => {
      notify(`${event.detail.title}：${event.detail.message}`);
    };
    window.addEventListener('vein:progress', onProgress);
    window.addEventListener('vein:log', onLog);
    window.addEventListener('vein:notify', onNotify);
    return () => {
      alive = false;
      window.removeEventListener('vein:progress', onProgress);
      window.removeEventListener('vein:log', onLog);
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
              logs={logs}
            />
          )}
          {page === 'versions' && (
            <VersionsPage installed={installed} onChange={refreshInstalled} notify={notify} />
          )}
          {page === 'download' && <DownloadPage tasks={tasks} />}
          {page === 'mods' && (
            <ModsPage installed={installed} selected={selected} notify={notify} />
          )}
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

function HomePage({ installed, accounts, selected, onSelect, notify, logs }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const account = accounts.find((a) => a.selected) || null;

  const launch = async () => {
    if (!selected) {
      notify('请先安装一个版本');
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
          <h2>启动</h2>
          <span className="count">{installed.length} 个实例</span>
          <div className="spacer" />
          <span className="count">{account ? `离线 · ${account.username}` : '未登录（离线模式）'}</span>
        </div>

        {installed.length === 0 ? (
          <Empty>还没有安装任何版本。到「版本」页选择一个 Minecraft 版本安装。</Empty>
        ) : (
          <>
            <div className="row">
              <div className="grow">
                <div className="name">选择实例</div>
                <div className="meta">本地 instances 目录</div>
              </div>
              <select value={selected} onChange={(e) => onSelect(e.target.value)}>
                {installed.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.id} · {v.type}
                  </option>
                ))}
              </select>
            </div>

            <div className="row">
              <div className="grow">
                <div className="name">启动游戏</div>
                <div className="meta">{status || '将调用 Python 端构建命令并拉起 Java 进程'}</div>
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

      <div className="panel">
        <div className="panel-head">
          <h2>游戏日志</h2>
          <span className="count">{logs.length}</span>
        </div>
        {logs.length === 0 ? (
          <Empty>启动游戏后，Python 会把进程输出实时推送到这里</Empty>
        ) : (
          <pre className="log-view">{logs.slice(-120).join('\n')}</pre>
        )}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
function VersionsPage({ installed, onChange, notify }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [installing, setInstalling] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await call('versions.remote', 80);
      setVersions(list);
    } catch (err) {
      notify(`获取版本列表失败：${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    load();
  }, [load]);

  const installedIds = useMemo(() => new Set(installed.map((v) => v.id)), [installed]);
  const shown = versions.filter((v) => !filter || v.id.includes(filter));

  const install = async (id) => {
    setInstalling(id);
    try {
      const result = await call('versions.install', id);
      notify(`安装完成：${result.ok}/${result.files} 个文件`);
      await onChange();
    } catch (err) {
      notify(`安装失败：${err.message}`);
    } finally {
      setInstalling('');
    }
  };

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>版本列表</h2>
        <span className="count">{shown.length}</span>
        <div className="spacer" />
        <input
          className="input"
          placeholder="筛选版本号"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <button className="btn ghost sm" onClick={load} disabled={loading}>
          {loading ? '加载中' : '刷新'}
        </button>
      </div>

      {loading && versions.length === 0 ? (
        <Empty>正在从 Mojang 获取版本清单…</Empty>
      ) : shown.length === 0 ? (
        <Empty>没有匹配的版本</Empty>
      ) : (
        shown.map((v) => {
          const isInstalled = installedIds.has(v.id);
          return (
            <div className="row" key={v.id}>
              <div className="grow">
                <div className="name">{v.id}</div>
                <div className="meta">
                  {v.type} · {v.release_time}
                </div>
              </div>
              {isInstalled ? (
                <span className="tag ok">已安装</span>
              ) : (
                <button
                  className="btn sm"
                  onClick={() => install(v.id)}
                  disabled={installing === v.id}
                >
                  {installing === v.id ? '安装中…' : '安装'}
                </button>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function DownloadPage({ tasks }) {
  const entries = Object.entries(tasks);
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>下载任务</h2>
        <span className="count">{entries.length}</span>
      </div>
      {entries.length === 0 ? (
        <Empty>当前没有下载任务。在「版本」或「模组」页开始安装后，这里会显示进度。</Empty>
      ) : (
        entries.map(([id, task]) => {
          const percent = task.total ? Math.min(100, Math.round((task.downloaded / task.total) * 100)) : 0;
          return (
            <div className="row" key={id}>
              <div className="grow">
                <div className="name">{id}</div>
                <div className="meta">
                  {formatBytes(task.downloaded)} / {formatBytes(task.total)}
                </div>
                <div className="progress">
                  <i style={{ width: `${percent}%` }} />
                </div>
              </div>
              <span className="tag">{percent}%</span>
            </div>
          );
        })
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function ModsPage({ installed, selected, notify }) {
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
      notify('请先在「版本」页安装一个实例');
      return;
    }
    setInstalling(slug);
    try {
      const result = await call('mods.install', slug, selected, type, 'fabric');
      notify(`已安装：${result.installed} 个文件`);
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

      <div className="row" style={{ marginTop: 12, borderTop: '1px solid var(--line)', paddingTop: 12 }}>
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
        <div className="kv"><div className="k">架构</div><div className="v">Python 后端 + React (WebView)</div></div>
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

/* ------------------------------------------------------------------ */
function formatBytes(value) {
  if (!value) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let index = 0;
  let size = value;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}
