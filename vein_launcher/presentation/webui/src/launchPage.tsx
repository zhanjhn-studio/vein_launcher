import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { AccountInfo, VersionInfo } from './types';
import { LogPanel } from './ui';

export function LaunchPage({
  installed,
  accounts,
  selected,
  onSelect,
  notify,
  announcements = [],
}: {
  installed: VersionInfo[];
  accounts: AccountInfo[];
  selected: string;
  onSelect: (id: string) => void;
  notify: (text: string) => void;
  announcements?: { id?: string; title: string; content?: string }[];
}) {
  const [busy, setBusy] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const account = accounts.find((a) => a.selected) || null;

  useEffect(() => {
    const handler = (event: Event) =>
      setLogs((prev) => [...prev.slice(-599), String((event as CustomEvent).detail)]);
    window.addEventListener('vein:log', handler);
    return () => window.removeEventListener('vein:log', handler);
  }, []);

  const launch = async () => {
    if (!selected) {
      notify('Install a version first');
      return;
    }
    setBusy(true);
    try {
      const result = await rpc<{ pid: number }>('launch', [selected, account?.username ?? 'Player']);
      notify(`Launched, PID ${result.pid}`);
    } catch (err) {
      notify(`Launch failed：${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="launch-grid">
        <div>
          <div className="page-head">
            <h1>Launch</h1>
            <span className="muted">{installed.length} versions</span>
            <span className="muted">·</span>
            <span className="muted">{account ? `Offline ${account.username}` : 'Not signed in'}</span>
          </div>

          {installed.length === 0 ? (
            <div className="card">
              <div className="empty">Nothing installed yet. Install one from Download.</div>
            </div>
          ) : (
            <div className="version-cards">
              {installed.map((version) => (
                <button
                  key={version.id}
                  className={`version-card ${selected === version.id ? 'active' : ''}`}
                  onClick={() => onSelect(version.id)}
                >
                  <span className="mark">{version.id.split('.')[0]}</span>
                  <span className="meta">
                    <span className="name">{version.id}</span>
                    <span className="tag">{version.type || 'release'}</span>
                  </span>
                  {selected === version.id && <span className="status">Selected</span>}
                </button>
              ))}
            </div>
          )}

          <div className="card" style={{ marginTop: 14 }}>
            <div className="launch-panel">
              <div className="kv">
                <span>Instance</span>
                <b>{selected || '—'}</b>
              </div>
              <div className="kv">
                <span>Accounts</span>
                <b>{account ? account.username : 'Not signed in (offline)'}</b>
              </div>
              <div className="launch-actions">
                <button className="launch-btn" onClick={launch} disabled={busy || !selected}>
                  {busy ? 'Launching…' : 'Launch game'}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="card announce-board">
            <div className="card-title">Announcements</div>
            {announcements.length === 0 ? (
              <div className="empty">No announcements</div>
            ) : (
              announcements.map((item, index) => (
                <div className="announce-item" key={item.id ?? index}>
                  <b>{item.title}</b>
                  {item.content && <p className="muted">{item.content}</p>}
                </div>
              ))
            )}
          </div>
          <LogPanel lines={logs} height={360} />
        </div>
      </div>
    </div>
  );
}
