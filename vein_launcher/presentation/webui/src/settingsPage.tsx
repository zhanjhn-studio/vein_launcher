import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { AppInfo, JavaRuntime } from './types';
import { applyTheme, currentTheme, Theme } from './theme';

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
        <h1>Settings</h1>
        <span className="muted">Grouped sections</span>
      </div>

      <div className="accordion">
        <details className="acc-item" open>
          <summary>Appearance</summary>
          <div className="acc-body">
            <div className="kv">
              <span>Theme</span>
              <b>
                <select
                  value={theme}
                  onChange={(e) => {
                    const next = e.target.value as Theme;
                    setTheme(next);
                    applyTheme(next);
                  }}
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="clear">Clear</option>
                  <option value="system">System</option>
                </select>
              </b>
            </div>
          </div>
        </details>

        <details className="acc-item">
          <summary>Accounts</summary>
          <div className="acc-body">
            {accounts.length === 0 && <p className="muted">No accounts yet</p>}
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
                placeholder="Offline username (3-16)"
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

            <div className="card-title" style={{ marginTop: 14 }}>Microsoft</div>
            <div className="row-actions">
              <input
                className="input"
                style={{ width: 300 }}
                placeholder="Azure client id"
                value={msId}
                onChange={(e) => setMsId(e.target.value)}
              />
              <input
                className="input"
                style={{ width: 260 }}
                placeholder="authority (common / tenant id)"
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

            <div className="card-title" style={{ marginTop: 14 }}>LittleSkin</div>
            <div className="row-actions">
              <input
                className="input"
                style={{ width: 260 }}
                placeholder="LittleSkin email"
                value={lsEmail}
                onChange={(e) => setLsEmail(e.target.value)}
              />
              <input
                className="input"
                style={{ width: 220 }}
                type="password"
                placeholder="Password"
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
          <summary>Java runtime</summary>
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
              <p className="muted">No scan yet. Click Auto detect.</p>
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
          <summary>Game folder</summary>
          <div className="acc-body">
            <div className="kv">
              <span>Current</span>
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
          <summary>Logs</summary>
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
          <summary>About</summary>
          <div className="acc-body">
            <div className="kv"><span>Version</span><b>{info?.version ?? '—'}</b></div>
            <div className="kv"><span>Data folder</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
            <div className="kv"><span>Stack</span><b>Python + PySide6 WebView + React + TS</b></div>
          </div>
        </details>
      </div>
    </div>
  );
}
