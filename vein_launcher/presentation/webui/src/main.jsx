import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app.jsx';
import { initBridge } from './bridge.js';

async function boot() {
  const root = createRoot(document.getElementById('root'));
  try {
    await initBridge();
    root.render(<App />);
  } catch (err) {
    root.render(
      <div style={{ padding: 24, color: '#f85149', fontFamily: 'monospace' }}>
        桥接失败：{String(err)}
      </div>
    );
  }
}

boot();
