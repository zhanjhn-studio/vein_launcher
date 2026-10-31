import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { DownloadTask, PluginInfo } from './types';

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function StatusDot({ on, label, tone = 'ok' }: { on: boolean; label: string; tone?: 'ok' | 'warn' | 'idle' }) {
  const cls = on ? tone : 'idle';
  return (
    <span className="status">
      <i className={`dot ${cls}`} />
      {label}
    </span>
  );
}

export function ThreePane({
  left,
  middle,
  right,
}: {
  left: React.ReactNode;
  middle: React.ReactNode;
  right: React.ReactNode;
}) {
  return (
    <div className="three-pane">
      <aside className="pane pane-left">{left}</aside>
      <section className="pane pane-middle">{middle}</section>
      <section className="pane pane-right">{right}</section>
    </div>
  );
}

export function CategoryList({
  items,
  active,
  onPick,
}: {
  items: { key: string; label: string; hint?: string }[];
  active: string;
  onPick: (key: string) => void;
}) {
  return (
    <div className="category-list">
      {items.map((item) => (
        <button
          key={item.key}
          className={`category ${active === item.key ? 'active' : ''}`}
          onClick={() => onPick(item.key)}
        >
          <span>{item.label}</span>
          {item.hint && <em>{item.hint}</em>}
        </button>
      ))}
    </div>
  );
}

export function PermissionDialog({
  plugin,
  onCancel,
  onConfirm,
}: {
  plugin: PluginInfo;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="modal-mask" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>授权确认</h3>
        <p className="muted">
          {plugin.displayName} 请求以下能力。未声明的能力会被宿主拒绝。
        </p>
        <ul className="perm-list">
          {plugin.permissions.length === 0 ? (
            <li className="muted">该插件未声明任何权限</li>
          ) : (
            plugin.permissions.map((perm) => (
              <li key={perm}>
                <code>{perm}</code>
              </li>
            ))
          )}
        </ul>
        <div className="modal-actions">
          <button className="btn" onClick={onCancel}>
            取消
          </button>
          <button className="btn primary" onClick={onConfirm}>
            允许并启用
          </button>
        </div>
      </div>
    </div>
  );
}

export function DownloadBar() {
  const [tasks, setTasks] = useState<DownloadTask[]>([]);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const list = await rpc<DownloadTask[]>('downloads.list');
        if (alive) setTasks(list);
      } catch {
        /* 宿主不可用时静默 */
      }
    };
    tick();
    const timer = window.setInterval(tick, 1500);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  if (tasks.length === 0) return null;

  return (
    <div className="download-bar">
      {tasks.map((task) => {
        const percent = task.total ? Math.min(100, Math.round((task.done / task.total) * 100)) : 0;
        return (
          <div className={`download-item ${task.error ? 'error' : ''}`} key={task.id}>
            <span className="name">{task.name}</span>
            <div className="mini-progress">
              <i style={{ width: `${percent}%` }} />
            </div>
            <span className="percent">
              {task.error ? '失败' : task.active ? `${percent}%` : '完成'}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function Toast({ text }: { text: string }) {
  if (!text) return null;
  return <div className="toast">{text}</div>;
}


export function LogPanel({
  lines,
  title = 'Game log',
  height = 320,
}: {
  lines: string[];
  title?: string;
  height?: number;
}) {
  const [open, setOpen] = useState(true);
  const levelOf = (line: string): string => {
    if (/\b(ERROR|FATAL|Exception|Traceback)\b/i.test(line)) return 'error';
    if (/\b(WARN|WARNING)\b/i.test(line)) return 'warn';
    if (/\b(INFO|DEBUG)\b/i.test(line)) return 'info';
    return '';
  };
  return (
    <section className="log-panel">
      <div className="log-head">
        <span className="title">{title}</span>
        <span className="spacer" />
        <span className="muted">{lines.length}</span>
        <button className="btn sm ghost" onClick={() => setOpen((v) => !v)}>
          {open ? '收起' : '展开'}
        </button>
      </div>
      {open && (
        <div className="log-body" style={{ height }}>
          {lines.length === 0 ? (
            <div className="log-empty">启动游戏后日志会在这里实时滚动</div>
          ) : (
            lines.map((line, index) => (
              <div className={`log-line ${levelOf(line)}`} key={index}>
                {line}
              </div>
            ))
          )}
        </div>
      )}
    </section>
  );
}

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div>
      {Array.from({ length: rows }).map((_, i) => (
        <div className="skeleton skeleton-row" key={i} />
      ))}
    </div>
  );
}

export function Spinner() {
  return <span className="spinner" />;
}
