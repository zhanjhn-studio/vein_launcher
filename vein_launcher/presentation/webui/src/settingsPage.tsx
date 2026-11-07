import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { AppInfo, JavaRuntime } from './types';
import { applyTheme, currentTheme, Theme } from './theme';
import { currentLang, setLang as applyLang, type Lang } from './i18n';
import { LayuiProgress } from './ui';
import { clearWallpaper, importWallpaper, savePrefs, usePrefs } from './prefs';
import { ACCENT_PRESETS, currentAccent } from './accent';

interface AccountRow {
  id: string;
  username: string;
  selected?: boolean;
  type?: string;
  uuid?: string;
  online?: boolean;
}

export function SettingsPage({ notify }: { notify: (text: string) => void }) {
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [runtimes, setRuntimes] = useState<JavaRuntime[]>([]);
  const [javaBusy, setJavaBusy] = useState(0);
  const [javaMsg, setJavaMsg] = useState('');
  const [mcDir, setMcDir] = useState('');
  const [theme, setTheme] = useState<Theme>(currentTheme());
  const [accounts, setAccounts] = useState<AccountRow[]>([]);
  const [newName, setNewName] = useState('');
  const [msId, setMsId] = useState('');
  const [msAuthority, setMsAuthority] = useState('common');
  const [msCode, setMsCode] = useState('');
  const [msBusy, setMsBusy] = useState(false);
  const [lsEmail, setLsEmail] = useState('');
  const [lsPassword, setLsPassword] = useState('');
  const [lsBusy, setLsBusy] = useState(false);
  const [lsMsg, setLsMsg] = useState('');
  const [lang, setLangState] = useState<Lang>(currentLang());
  const [update, setUpdate] = useState<{
    available: boolean;
    current?: string;
    version?: string;
    notes?: string;
    html_url?: string;
    error?: string;
    assets?: { name: string; size: number; url: string }[];
  } | null>(null);
  const [updateBusy, setUpdateBusy] = useState('');
  const [updateMsg, setUpdateMsg] = useState('');
  const [updatePct, setUpdatePct] = useState(0);
  const [downloaded, setDownloaded] = useState('');
  const prefs = usePrefs();
  const [idleDraft, setIdleDraft] = useState(String(prefs.idleSeconds));
  const [wallBusy, setWallBusy] = useState(false);

  useEffect(() => {
    setIdleDraft(String(prefs.idleSeconds));
  }, [prefs.idleSeconds]);

  const toggleCompact = async () => {
    try {
      const next = await savePrefs({ compactMode: !prefs.compactMode });
      notify(next.compactMode ? '已开启简洁模式' : '已关闭简洁模式');
    } catch (err) {
      notify(`Failed: ${(err as Error).message}`);
    }
  };

  /** 切主色：立即写配置并重绘 CSS 变量 */
  const changeAccent = async (hex: string) => {
    try {
      const next = await savePrefs({ accent: hex });
      notify(hex ? `主色已切换：${next.accent || hex}` : '已恢复默认主色');
    } catch (err) {
      notify(`Failed: ${(err as Error).message}`);
    }
  };

  const commitIdle = async () => {
    const parsed = Number.parseInt(idleDraft, 10);
    const seconds = Number.isFinite(parsed) ? Math.max(0, Math.min(3600, parsed)) : 60;
    setIdleDraft(String(seconds));
    try {
      await savePrefs({ idleSeconds: seconds });
    } catch (err) {
      notify(`Failed: ${(err as Error).message}`);
    }
  };

  const pickWallpaper = async () => {
    setWallBusy(true);
    try {
      const next = await importWallpaper();
      if (next) notify('Wallpaper updated');
    } catch (err) {
      notify(`Import failed: ${(err as Error).message}`);
    } finally {
      setWallBusy(false);
    }
  };

  const dropWallpaper = async () => {
    try {
      await clearWallpaper();
      notify('Wallpaper removed');
    } catch (err) {
      notify(`Failed: ${(err as Error).message}`);
    }
  };

  const reloadAccounts = () =>
    rpc<AccountRow[]>('accounts.list').then(setAccounts).catch(() => {});

  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
    rpc<{ path: string }>('minecraft.getDir')
      .then((r) => setMcDir(r.path))
      .catch(() => {});
    reloadAccounts();
    rpc<{ client_id: string }>('accounts.msClientId')
      .then((r) => setMsId(r.client_id))
      .catch(() => {});
    rpc<{ authority: string }>('accounts.msAuthority')
      .then((r) => setMsAuthority(r.authority || 'common'))
      .catch(() => {});
  }, []);

  const detect = async () => {
    try {
      setRuntimes(await rpc<JavaRuntime[]>('java.detect'));
    } catch (err) {
      notify(`Detect failed: ${(err as Error).message}`);
    }
  };

  const installJava = async (major: number) => {
    setJavaBusy(major);
    setJavaMsg(`Installing Java ${major}…`);
    try {
      const r = await rpc<{ path: string; downloaded: boolean }>('java.ensure', [major]);
      setJavaMsg(`Java ${major}: ${r.path} (${r.downloaded ? 'downloaded' : 'existing'})`);
    } catch (err) {
      setJavaMsg(`Java ${major} failed: ${(err as Error).message}`);
    } finally {
      setJavaBusy(0);
    }
  };

  const startMicrosoft = async () => {
    setMsBusy(true);
    setMsCode('Requesting device code…');
    try {
      await rpc('accounts.msClientId', [msId]);
      await rpc('accounts.msAuthority', [msAuthority]);
      const info = await rpc<{ device_code: string; user_code: string; verification_uri: string }>(
        'accounts.msStart'
      );
      setMsCode(`Open ${info.verification_uri} and enter code ${info.user_code}`);
      const account = await rpc<{ username: string }>('accounts.msLogin', [info.device_code]);
      setMsCode(`Signed in as ${account.username}`);
      await reloadAccounts();
    } catch (err) {
      setMsCode(`Microsoft login failed: ${(err as Error).message}`);
    } finally {
      setMsBusy(false);
    }
  };

  const checkUpdates = async () => {
    setUpdateBusy('check');
    setUpdateMsg('');
    try {
      const info = await rpc<typeof update>('update.latest');
      setUpdate(info as never);
    } catch (err) {
      setUpdateMsg((err as Error).message);
    } finally {
      setUpdateBusy('');
    }
  };

  const downloadUpdate = async () => {
    const asset =
      update?.assets?.find((a) => /\.(zip|exe|msi)$/i.test(a.name)) || update?.assets?.[0];
    if (!asset) {
      setUpdateMsg('This release has no downloadable file');
      return;
    }
    setUpdateBusy('download');
    setUpdatePct(0);
    setUpdateMsg(`Downloading ${asset.name}…`);
    const timer = window.setInterval(async () => {
      try {
        const list = await rpc<Array<{ id: string; done: number; total: number }>>('downloads.list');
        const task = list.find((t) => t.id === 'update');
        if (task && task.total) setUpdatePct(Math.round((task.done / task.total) * 100));
      } catch {
        /* ignore */
      }
    }, 700);
    try {
      const result = await rpc<{ path: string }>('update.download', [asset.url, asset.name]);
      setDownloaded(result.path);
      setUpdatePct(100);
      setUpdateMsg(`Downloaded to ${result.path}`);
    } catch (err) {
      setUpdateMsg((err as Error).message);
    } finally {
      window.clearInterval(timer);
      setUpdateBusy('');
    }
  };

  const installUpdate = async () => {
    if (!downloaded) return;
    setUpdateBusy('install');
    try {
      const result = await rpc<{ started: boolean; kind: string; path: string }>('update.install', [
        downloaded,
      ]);
      setUpdateMsg(
        result.started
          ? 'Update unpacked — follow the installer / open the extracted folder.'
          : `Cannot apply automatically, file at ${result.path}`
      );
    } catch (err) {
      setUpdateMsg((err as Error).message);
    } finally {
      setUpdateBusy('');
    }
  };

  const startLittleSkin = async () => {
    setLsBusy(true);
    setLsMsg('Signing in to LittleSkin…');
    try {
      const account = await rpc<{ username: string }>('accounts.littleSkin', [
        '',
        lsEmail.trim(),
        lsPassword,
      ]);
      setLsPassword('');
      setLsMsg(`Signed in as ${account.username}`);
      await reloadAccounts();
    } catch (err) {
      setLsMsg(`LittleSkin login failed: ${(err as Error).message}`);
    } finally {
      setLsBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h1>设置</h1>
        <span className="muted">分组设置</span>
      </div>

      <div className="accordion">
        <details className="acc-item" open>
          <summary>外观</summary>
          <div className="acc-body">
            <div className="kv">
              <span>主题</span>
              <b>
                <select
                  value={theme}
                  onChange={(e) => {
                    const next = e.target.value as Theme;
                    setTheme(next);
                    applyTheme(next);
                  }}
                >
                  <option value="dark">深色</option>
                  <option value="light">浅色</option>
                  <option value="clear">透明</option>
                  <option value="system">跟随系统</option>
                </select>
              </b>
            </div>
            <div className="setting-block">
              <div className="setting-label">主题色</div>
              <div className="accent-row">
                {ACCENT_PRESETS.map((color) => (
                  <button
                    key={color}
                    className={`accent-dot ${prefs.accent.toLowerCase() === color ? 'active' : ''}`}
                    style={{ background: color, color }}
                    title={color}
                    onClick={() => changeAccent(color)}
                  />
                ))}
                <input
                  type="color"
                  className="accent-picker"
                  value={prefs.accent || currentAccent()}
                  onChange={(e) => changeAccent(e.target.value)}
                />
                <button className="btn sm ghost" onClick={() => changeAccent('')}>
                  默认
                </button>
              </div>
              <p className="muted" style={{ margin: '8px 0 0' }}>
                主色会套用到按钮、选中态、进度条与强调文字；点色块即时生效，「默认」恢复内置配色。
              </p>
            </div>
            <div className="kv">
              <span>语言</span>
              <b>
                <select
                  value={lang}
                  onChange={(e) => {
                    const next = e.target.value as Lang;
                    setLangState(next);
                    applyLang(next);
                  }}
                >
                  <option value="en">English</option>
                  <option value="zh">Chinese (Simplified)</option>
                </select>
              </b>
            </div>
            <div className="kv">
              <span>简洁模式</span>
              <b>
                <button
                  className={`btn sm ${prefs.compactMode ? 'primary' : ''}`}
                  onClick={toggleCompact}
                >
                  {prefs.compactMode ? '开' : '关'}
                </button>
              </b>
            </div>
            <p className="muted" style={{ margin: '-4px 0 8px' }}>
              隐藏侧边栏：屏幕左边缘会留一个半透明手柄，点它把侧栏滑出来；选完页面会自动收起。
            </p>
            <div className="kv">
              <span>空闲后淡出</span>
              <b>
                <input
                  className="input"
                  style={{ width: 92 }}
                  type="number"
                  min={0}
                  max={3600}
                  value={idleDraft}
                  onChange={(e) => setIdleDraft(e.target.value)}
                  onBlur={commitIdle}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
                  }}
                />
                <span className="muted" style={{ marginLeft: 8 }}>秒</span>
              </b>
            </div>
            <p className="muted" style={{ margin: '-4px 0 8px' }}>
              在启动页，超过这么多秒没有鼠标、键盘、滚轮或触摸操作后，界面会淡成透明；任何操作都会让它
              重新出现。填 0 关闭（默认 60 秒）。
            </p>
            <div className="kv">
              <span>壁纸</span>
              <b>
                <button className="btn sm" onClick={pickWallpaper} disabled={wallBusy}>
                  {wallBusy ? '导入中…' : prefs.wallpaper ? '更换…' : '导入…'}
                </button>
                {prefs.wallpaper && (
                  <button className="btn sm ghost" style={{ marginLeft: 6 }} onClick={dropWallpaper}>
                    移除
                  </button>
                )}
              </b>
            </div>
            <p className="muted" style={{ margin: '-4px 0 8px' }}>
              支持 PNG / JPG / WEBP / GIF / BMP / MP4 / WEBM。文件会被复制进启动器数据目录，
              之后移动原文件也没关系。
            </p>
            {prefs.wallpaper && (
              <div className="wall-preview-wrap">
                {prefs.wallpaper.kind === 'video' ? (
                  <video
                    className="wall-preview"
                    src={prefs.wallpaper.url}
                    muted
                    loop
                    autoPlay
                    playsInline
                  />
                ) : (
                  <img className="wall-preview" src={prefs.wallpaper.url} alt="" />
                )}
                <span className="mono muted">{prefs.wallpaper.name}</span>
              </div>
            )}
          </div>
        </details>

        <details className="acc-item">
          <summary>账号</summary>
          <div className="acc-body">
            {accounts.length === 0 && <p className="muted">还没有账号</p>}
            {accounts.map((acc) => (
              <div className="kv" key={acc.id}>
                <span>
                  {acc.username}
                  <span className={acc.type === 'microsoft' ? 'badge accent' : 'badge'}>
                    {acc.type === 'microsoft'
                      ? acc.online
                        ? 'Microsoft'
                        : 'Microsoft · signed out'
                      : acc.type === 'littleskin'
                        ? 'LittleSkin'
                        : 'Offline'}
                  </span>
                  {acc.selected ? ' · current' : ''}
                </span>
                <b>
                  <button
                    className="btn sm"
                    onClick={async () => {
                      await rpc('accounts.select', [acc.id]);
                      await reloadAccounts();
                    }}
                  >
                    Use
                  </button>
                  <button
                    className="btn sm"
                    style={{ marginLeft: 6 }}
                    onClick={async () => {
                      await rpc('accounts.remove', [acc.id]);
                      await reloadAccounts();
                    }}
                  >
                    Remove
                  </button>
                </b>
              </div>
            ))}

            <div className="row-actions">
              <input
                className="input"
                placeholder="离线用户名（3-16 位）"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <button
                className="btn primary sm"
                onClick={async () => {
                  try {
                    await rpc('accounts.add', [newName]);
                    setNewName('');
                    await reloadAccounts();
                  } catch (err) {
                    notify(`Add failed: ${(err as Error).message}`);
                  }
                }}
              >
                Add offline
              </button>
            </div>

            <div className="card-title" style={{ marginTop: 14 }}>微软账号</div>
            <div className="row-actions">
              <input
                className="input"
                style={{ width: 300 }}
                placeholder="Azure 客户端 ID"
                value={msId}
                onChange={(e) => setMsId(e.target.value)}
              />
              <input
                className="input"
                style={{ width: 260 }}
                placeholder="授权域（common / 租户 ID）"
                value={msAuthority}
                onChange={(e) => setMsAuthority(e.target.value)}
              />
              <button
                className="btn sm"
                onClick={async () => {
                  await rpc('accounts.msClientId', [msId]);
                  await rpc('accounts.msAuthority', [msAuthority]);
                  notify('Microsoft settings saved');
                }}
              >
                Save
              </button>
            </div>
            <div className="row-actions">
              <button className="btn primary" onClick={startMicrosoft} disabled={msBusy}>
                {msBusy ? 'Waiting for approval…' : 'Sign in with Microsoft'}
              </button>
            </div>
            {msCode && <p className="muted">{msCode}</p>}

            <div className="card-title" style={{ marginTop: 14 }}>LittleSkin 账号</div>
            <div className="row-actions">
              <input
                className="input"
                style={{ width: 260 }}
                placeholder="LittleSkin 邮箱"
                value={lsEmail}
                onChange={(e) => setLsEmail(e.target.value)}
              />
              <input
                className="input"
                style={{ width: 220 }}
                type="password"
                placeholder="密码"
                value={lsPassword}
                onChange={(e) => setLsPassword(e.target.value)}
              />
              <button
                className="btn primary sm"
                disabled={lsBusy || !lsEmail.trim() || !lsPassword}
                onClick={startLittleSkin}
              >
                {lsBusy ? 'Signing in…' : 'Sign in'}
              </button>
            </div>
            <p className="muted">
              littleskin.cn skins and its online servers. The launcher stores only the access
              token, never your password.
            </p>
            {lsMsg && <p className="muted">{lsMsg}</p>}
          </div>
        </details>

        <details className="acc-item">
          <summary>Java 环境</summary>
          <div className="acc-body">
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button className="btn sm" onClick={detect}>
                Auto detect
              </button>
              {[8, 17, 21].map((major) => (
                <button
                  key={major}
                  className="btn sm"
                  disabled={javaBusy === major}
                  onClick={() => installJava(major)}
                >
                  {javaBusy === major ? '…' : `Install Java ${major}`}
                </button>
              ))}
            </div>
            {javaMsg && <p className="muted">{javaMsg}</p>}
            {runtimes.length === 0 ? (
              <p className="muted">还没扫描过，点「自动检测」。</p>
            ) : (
              runtimes.map((rt) => (
                <div className="kv" key={rt.path}>
                  <span>Java {rt.major}</span>
                  <b className="mono">{rt.path}</b>
                </div>
              ))
            )}
          </div>
        </details>

        <details className="acc-item">
          <summary>游戏目录</summary>
          <div className="acc-body">
            <div className="kv">
              <span>当前</span>
              <b className="mono">{mcDir || '—'}</b>
            </div>
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button
                className="btn sm"
                onClick={async () => {
                  const picked = await rpc<{ path: string }>('app.pickDirectory', [
                    'Select .minecraft folder',
                  ]);
                  if (!picked.path) return;
                  const applied = await rpc<{ path: string }>('minecraft.setDir', [picked.path]);
                  setMcDir(applied.path);
                }}
              >
                Choose .minecraft
              </button>
              <button
                className="btn sm"
                onClick={async () => {
                  const applied = await rpc<{ path: string }>('minecraft.setDir', ['']);
                  setMcDir(applied.path);
                }}
              >
                Use default
              </button>
            </div>
          </div>
        </details>

        <details className="acc-item">
          <summary>日志</summary>
          <div className="acc-body">
            <p className="muted">
              Written daily to VeinLauncher/log, split into launcher / plugin / mlc / download.
            </p>
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button className="btn sm" onClick={() => rpc('logs.openDir').catch(() => {})}>
                Open log folder
              </button>
            </div>
          </div>
        </details>

        <details className="acc-item">
          <summary>关于</summary>
          <div className="acc-body">
            <div className="kv"><span>版本</span><b>{info?.version ?? '—'}</b></div>
            <div className="kv"><span>数据目录</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
            <div className="kv"><span>技术栈</span><b>Python + PySide6 WebView + React + TS</b></div>

            <div className="row-actions" style={{ marginTop: 10 }}>
              <button className="btn sm" onClick={checkUpdates} disabled={updateBusy === 'check'}>
                <i className="layui-icon layui-icon-refresh" />{' '}
                {updateBusy === 'check' ? 'Checking…' : 'Check for updates'}
              </button>
              {update?.html_url && (
                <button
                  className="btn sm ghost"
                  onClick={() => rpc('app.openUrl', [update.html_url])}
                >
                  Release page
                </button>
              )}
            </div>

            {update?.available && (
              <div className="update-card">
                <b>Update available: v{update.version}</b>
                {update.notes && <pre className="update-notes">{update.notes.slice(0, 1400)}</pre>}
                {updateBusy === 'download' && <LayuiProgress percent={updatePct} />}
                <div className="row-actions">
                  <button
                    className="btn primary sm"
                    onClick={downloadUpdate}
                    disabled={updateBusy !== ''}
                  >
                    {updateBusy === 'download' ? `Downloading ${updatePct}%` : 'Download update'}
                  </button>
                  {downloaded && (
                    <button className="btn sm" onClick={installUpdate} disabled={updateBusy !== ''}>
                      {updateBusy === 'install' ? 'Starting…' : 'Install update'}
                    </button>
                  )}
                </div>
              </div>
            )}

            {update && !update.available && !update.error && (
              <p className="muted">已是最新版本。</p>
            )}
            {update?.error && <p className="muted">{update.error}</p>}
            {updateMsg && <p className="muted">{updateMsg}</p>}
          </div>
        </details>
      </div>
    </div>
  );
}
