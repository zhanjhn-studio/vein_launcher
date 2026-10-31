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
}: {
  installed: VersionInfo[];
  accounts: AccountInfo[];
  selected: string;
  onSelect: (id: string) => void;
  notify: (text: string) => void;
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
      notify('请先安装一个版本');
      return;
    }
    setBusy(true);
    try {
      const result = await rpc<{ pid: number }>('launch', [selected, account?.username ?? 'Player']);
      notify(`已启动，PID ${result.pid}`);
    } catch (err) {
      notify(`启动失败：${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="launch-grid">
        <div>
          <div className="page-head">
            <h1>启动</h1>
            <span className="muted">{installed.length} 个版本</span>
            <span className="muted">·</span>
            <span className="muted">{account ? `离线 ${account.username}` : '未登录'}</span>
          </div>

          {installed.length === 0 ? (
            <div className="card">
              <div className="empty">还没有安装任何版本，去「下载」页安装</div>
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
                  {selected === version.id && <span className="status">已选择</span>}
                </button>
              ))}
            </div>
          )}

          <div className="card" style={{ marginTop: 14 }}>
            <div className="launch-panel">
              <div className="kv">
                <span>实例</span>
                <b>{selected || '—'}</b>
              </div>
              <div className="kv">
                <span>账号</span>
                <b>{account ? account.username : '未登录（离线）'}</b>
              </div>
              <div className="launch-actions">
                <button className="launch-btn" onClick={launch} disabled={busy || !selected}>
                  {busy ? '启动中…' : '启动游戏'}
                </button>
              </div>
            </div>
          </div>
        </div>

        <LogPanel lines={logs} height={520} />
      </div>
    </div>
  );
}
