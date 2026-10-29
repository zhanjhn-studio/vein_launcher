import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { initBridge } from './bridge';

async function boot() {
  const root = createRoot(document.getElementById('root')!);
  try {
    await initBridge();
    root.render(<App />);
  } catch (err) {
    root.render(
      <div style={{ padding: 24, fontFamily: 'monospace', color: '#d64545' }}>
        桥接失败：{String(err)}
      </div>
    );
  }
}

boot();
