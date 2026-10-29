import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app.jsx';

/**
 * 浏览器预览入口：不连 Python，用内存数据驱动界面。
 * 只用于看排版，不代表真实数据。
 */
const VERSIONS = [
  { id: '1.21.4', type: 'release', release_time: '2024-12-03' },
  { id: '1.21', type: 'release', release_time: '2024-06-13' },
  { id: '1.20.4', type: 'release', release_time: '2023-12-07' },
  { id: '1.20.1', type: 'release', release_time: '2023-06-12' },
  { id: '1.19.4', type: 'release', release_time: '2023-03-14' },
];

const RESPONSES = {
  'app.info': { version: 'preview', dataDir: '（预览模式，无后端）' },
  'versions.info': [],
  'versions.remote': VERSIONS,
  'accounts.list': [],
  'java.detect': [],
  'mods.search': [],
};

window.__bridge = {
  call(id, payload) {
    let method = '';
    try {
      method = JSON.parse(payload).method;
    } catch {
      method = '';
    }
    const data = RESPONSES[method];
    window.setTimeout(() => {
      if (data === undefined) {
        window.__veinResult(id, false, '预览模式不支持该操作');
      } else {
        window.__veinResult(id, true, data);
      }
    }, 100);
  },
};

const style = document.createElement('style');
style.textContent = `
  .preview-note {
    position: fixed; right: 16px; bottom: 14px; z-index: 99;
    font: 11px var(--mono); color: #64717e;
    background: #141a22; border: 1px solid #27313d;
    border-radius: 6px; padding: 6px 12px;
  }
`;
document.head.appendChild(style);

const root = createRoot(document.getElementById('root'));
root.render(
  <>
    <App />
    <div className="preview-note">预览模式 · 未连接 Python 后端</div>
  </>
);
