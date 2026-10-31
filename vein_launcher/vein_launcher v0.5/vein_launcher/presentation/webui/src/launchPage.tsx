import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { AccountInfo, VersionInfo } from './types';
import { LogPanel } from './ui';
import { usePrefs } from './prefs';

export function LaunchPage({
  installed,
  accounts,
  selected,
  onSelect,
  onManage,
  notify,
  announcements = [],
}: {
  installed: VersionInfo[];
  accounts: AccountInfo[];
  selected: string;
  onSelect: (id: string) => void;
  onManage?: (id: string) => void;
  notify: (text: string) => void;
  announcements?: { id?: string; title: string; content?: string }[];
}) {
  const [busy, setBusy] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const account = accounts.find((a) => a.selected) || null;
  const prefs = usePrefs();

  // 空闲淡出：启动页在设定秒数内无任何输入（鼠标/键盘/滚轮/触摸）后，UI 变透明只留壁纸。
  // 注意：淡出会给 .main/.side 加 pointer-events:none，这会让浏览器合成一次 mousemove，
  // 若直接把它当成用户操作就会「淡出→立刻恢复→再淡出」无限闪烁。所以：
  //   · 坐标没真正变化的 mousemove 忽略；
  //   · 刚进入透明态的头 600ms 内的任何事件都不算恢复操作。
  useEffect(() => {
    const root = document.documentElement;
    const seconds = Number(prefs.idleSeconds) || 0;
    if (seconds <= 0) {
      delete root.dataset.idle;
      return;
    }
    let timer = 0;
    let armedAt = 0;
    let lastX = Number.NaN;
    let lastY = Number.NaN;

    const arm = () => {
      armedAt = Date.now();
      root.dataset.idle = 'on';
    };

    const reset = (event: Event) => {
      const now = Date.now();
      if (armedAt && now - armedAt < 600) return;
      if (event.type === 'mousemove') {
        const { clientX, clientY } = event as MouseEvent;
        if (clientX === lastX && clientY === lastY) return;
        lastX = clientX;
        lastY = clientY;
      }
      armedAt = 0;
      if (root.dataset.idle) delete root.dataset.idle;
      window.clearTimeout(timer);
      timer = window.setTimeout(arm, seconds * 1000);
    };

    const events: (keyof WindowEventMap)[] = [
      'mousemove',
      'mousedown',
      'wheel',
      'keydown',
      'touchstart',
      'pointerdown',
    ];
    events.forEach((name) => window.addEventListener(name, reset, { passive: true }));
    timer = window.setTimeout(arm, seconds * 1000);
    return () => {
      events.forEach((name) => window.removeEventListener(name, reset));
      window.clearTimeout(timer);
      delete root.dataset.idle;
    };
  }, [prefs.idleSeconds]);

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
    <>
      <div className="page no-anim">
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
                <div
                  key={version.id}
                  className={`version-card ${selected === version.id ? 'active' : ''}`}
                  onClick={() => onSelect(version.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') onSelect(version.id);
                  }}
                >
                  <span className="mark">{version.id.split('.')[0]}</span>
                  <span className="meta">
                    <span className="name">{version.id}</span>
                    <span className="tag">{version.type || 'release'}</span>
                  </span>
                  {selected === version.id && <span className="status">Selected</span>}
                  {onManage && (
                    <button
                      className="btn sm ghost card-manage"
                      onClick={(e) => {
                        e.stopPropagation();
                        onManage(version.id);
                      }}
                    >
                      Manage
                    </button>
                  )}
                </div>
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
    </>
  );
}
