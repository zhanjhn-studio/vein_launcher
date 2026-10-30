import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { initBridge } from './bridge';
import { startLocalization } from './localize';

async function boot() {
  const root = createRoot(document.getElementById('root')!);
  try {
    await initBridge();
    root.render(<App />);
    // 渲染后启动 DOM 英文化（默认英文）
    window.setTimeout(startLocalization, 0);
    window.setTimeout(startLocalization, 300);
  } catch (err) {
    root.render(
      <div style={{ padding: 24, fontFamily: 'monospace', color: '#d64545' }}>
        Bridge failed: {String(err)}
      </div>
    );
  }
}

boot();
