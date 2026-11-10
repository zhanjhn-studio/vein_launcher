import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';

interface DownloadTask {
  id: string;
  name: string;
  done: number;
  total: number;
  active: boolean;
  error?: string | null;
}

export function DownloadsPage() {
  const [tasks, setTasks] = useState<DownloadTask[]>([]);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const list = await rpc<DownloadTask[]>('downloads.list', []);
        if (alive) setTasks(list);
      } catch {
        /* 忽略单次失败 */
      }
    };
    tick();
    const timer = window.setInterval(tick, 800);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  const active = tasks.filter((t) => t.active);
  const done = tasks.filter((t) => !t.active);

  return (
    <div className="page">
      <div className="page-head">
        <h1>下载</h1>
        <span className="muted">{active.length} 进行中 · {done.length} 已完成</span>
      </div>

      <div className="dl-list">
        {tasks.length === 0 && <div className="empty">还没有下载任务</div>}
        {tasks.map((task) => {
          const pct = task.total > 0 ? Math.min(100, Math.round((task.done / task.total) * 100)) : 0;
          return (
            <div className={`dl-row ${task.active ? 'active' : ''}`} key={task.id}>
              <div className="dl-name" title={task.id}>
                <b>{task.name || task.id}</b>
                <span className="muted">
                  {task.error ? `失败：${task.error}` : task.active ? '下载中' : '已完成'}
                </span>
              </div>
              <div className="dl-bar">
                <i style={{ width: `${Math.max(pct, task.active ? 2 : 0)}%` }} />
              </div>
              <span className="dl-pct">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
