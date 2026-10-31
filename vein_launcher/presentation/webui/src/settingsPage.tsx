import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { AppInfo, JavaRuntime } from './types';
import { applyTheme, currentTheme, Theme } from './theme';

export function SettingsPage({ notify }: { notify: (text: string) => void }) {
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [runtimes, setRuntimes] = useState<JavaRuntime[]>([]);
  const [javaBusy, setJavaBusy] = useState(0);
  const [javaMsg, setJavaMsg] = useState('');
  const [mcDir, setMcDir] = useState('');
  const [theme, setTheme] = useState<Theme>(currentTheme());

  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
    rpc<{ path: string }>('minecraft.getDir')
      .then((r) => setMcDir(r.path))
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
      setJavaMsg(`Java ${major}：${r.path}（${r.downloaded ? 'downloaded' : 'existing'}）`);
    } catch (err) {
      setJavaMsg(`Java ${major} Failed：${(err as Error).message}`);
    } finally {
      setJavaBusy(0);
    }
  };

  const chooseDir = async () => {
    const picked = await rpc<{ path: string }>('app.pickDirectory', ['Select .minecraft folder']);
    if (!picked.path) return;
    const applied = await rpc<{ path: string }>('minecraft.setDir', [picked.path]);
    setMcDir(applied.path);
    notify(`Game folder: ${applied.path}`);
  };

  return (
    <div className="page">
      <div className="page-head">
        <h1>Settings</h1>
        <span className="muted">Grouped sections keep the page readable.</span>
      </div>

      <div className="accordion">
        <details className="acc-item" open>
          <summary>Appearance & language</summary>
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
          <summary>Java Runtime</summary>
          <div className="acc-body">
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button className="btn sm" onClick={detect}>Auto detect</button>
              {[8, 17, 21].map((major) => (
                <button key={major} className="btn sm" disabled={javaBusy === major} onClick={() => installJava(major)}>
                  {javaBusy === major ? '…' : `Install Java ${major}`}
                </button>
              ))}
            </div>
            {javaMsg && <p className="muted">{javaMsg}</p>}
            {runtimes.length === 0 ? (
              <p className="muted">Not scanned yet. Click Auto detect to find local Java.</p>
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
              <button className="btn sm" onClick={chooseDir}>Choose .minecraft</button>
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
            <p className="muted">Written daily to VeinLauncher/log, split by launcher / plugin / mlc / download.。</p>
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
            <div className="kv"><span>Architecture</span><b>Python + PySide6 WebView + React + TS</b></div>
          </div>
        </details>
      </div>
    </div>
  );
}
