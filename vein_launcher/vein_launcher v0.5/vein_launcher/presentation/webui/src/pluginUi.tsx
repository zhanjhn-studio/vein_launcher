import React, { useEffect, useRef, useState } from 'react';
import { rpc } from './bridge';

interface UiNode {
  type: string;
  props?: Record<string, any>;
  children?: UiNode[];
}

const SHADOW_STYLE = `
  :host { all: initial; }
  .vp-panel {
    font: 13px/1.6 "HarmonyOS Sans SC", system-ui, sans-serif;
    background: #20252f; color: #e6e9f0;
    border: 1px solid #2b313d; border-radius: 12px;
    box-shadow: 0 16px 40px rgba(0,0,0,.45);
    padding: 16px; width: 360px; position: relative;
  }
  .vp-title { font-weight: 700; font-size: 14px; margin-bottom: 10px; padding-right: 22px; }
  .vp-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 6px 0; }
  .vp-text { font-size: 12.5px; color: #a4aec0; }
  .vp-button {
    border: 1px solid #6f97f0; background: #6f97f0; color: #101725;
    border-radius: 9px; padding: 5px 12px; cursor: pointer; font-size: 12.5px; font-weight: 600;
  }
  .vp-button:hover { filter: brightness(1.08); }
  .vp-input { border: 1px solid #363e4d; border-radius: 8px; padding: 5px 10px; font-size: 12.5px; background: #262c37; color: #e6e9f0; }
  .vp-badge {
    font: 11px ui-monospace, monospace; color: #6f97f0;
    background: rgba(111,151,240,.12); border: 1px solid rgba(111,151,240,.3);
    border-radius: 6px; padding: 2px 8px;
  }
  .vp-divider { border: 0; border-top: 1px solid #2b313d; margin: 10px 0; }
  .vp-table { width: 100%; border-collapse: collapse; font-size: 12px; color: #e6e9f0; }
  .vp-table th, .vp-table td { border-bottom: 1px solid #2b313d; padding: 5px 6px; text-align: left; }
  .vp-table th { color: #a4aec0; font-weight: 600; }
  .vp-image { max-width: 100%; border-radius: 8px; }
  .vp-close {
    position: absolute; top: 8px; right: 8px; z-index: 3;
    width: 22px; height: 22px; line-height: 20px; text-align: center;
    border: 1px solid #363e4d; background: #262c37; color: #a4aec0;
    border-radius: 7px; cursor: pointer; font-size: 13px; padding: 0;
  }
  .vp-close:hover { background: #c0504d; border-color: #c0504d; color: #fff; }
`;

export function PluginUiHost() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const shadowRef = useRef<ShadowRoot | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [current, setCurrent] = useState<{ pluginId: string; tree: UiNode } | null>(null);

  // 只创建一次 shadow root，避免重复 attachShadow 抛错
  useEffect(() => {
    const host = hostRef.current;
    if (!host || shadowRef.current) return;
    const shadow = host.attachShadow({ mode: 'closed' });
    const style = document.createElement('style');
    style.textContent = SHADOW_STYLE;
    shadow.appendChild(style);
    const shell = document.createElement('div');
    shell.style.cssText = 'position:fixed;right:24px;bottom:64px;z-index:150;';
    shadow.appendChild(shell);
    const container = document.createElement('div');
    shell.appendChild(container);
    shadowRef.current = shadow;
    containerRef.current = container;
  }, []);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { pluginId?: string; tree?: UiNode };
      if (detail?.tree && detail.tree.type) {
        setCurrent({ pluginId: String(detail.pluginId || 'plugin'), tree: detail.tree });
      }
    };
    const clear = () => setCurrent(null);
    (window as any).__veinUi = (payload: any) =>
      window.dispatchEvent(new CustomEvent('vein:ui', { detail: payload }));
    (window as any).__veinUiClear = clear;
    window.addEventListener('vein:ui', handler);
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') clear();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('vein:ui', handler);
      window.removeEventListener('keydown', onKey);
    };
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    container.innerHTML = '';
    if (!current) return;

    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';

    const close = document.createElement('button');
    close.className = 'vp-close';
    close.type = 'button';
    close.textContent = '×';
    close.title = 'Close';
    close.addEventListener('click', (event) => {
      event.stopPropagation();
      setCurrent(null);
    });
    wrapper.appendChild(close);

    const panel = renderNode(current.tree, current.pluginId);
    if (panel) wrapper.appendChild(panel);
    container.appendChild(wrapper);
  }, [current]);

  return <div ref={hostRef} />;
}

function renderNode(node: UiNode, pluginId: string): HTMLElement | null {
  const props = node.props || {};
  const children = (node.children || [])
    .map((child) => renderNode(child, pluginId))
    .filter(Boolean) as HTMLElement[];

  const text = (value: unknown) => String(value ?? '');

  switch (node.type) {
    case 'panel': {
      const el = document.createElement('div');
      el.className = 'vp-panel';
      if (props.title) {
        const title = document.createElement('div');
        title.className = 'vp-title';
        title.textContent = text(props.title);
        el.appendChild(title);
      }
      children.forEach((child) => el.appendChild(child));
      return el;
    }
    case 'row': {
      const el = document.createElement('div');
      el.className = 'vp-row';
      children.forEach((child) => el.appendChild(child));
      return el;
    }
    case 'text': {
      const el = document.createElement('div');
      el.className = 'vp-text';
      el.textContent = text(props.value);
      return el;
    }
    case 'button': {
      const el = document.createElement('button');
      el.className = 'vp-button';
      el.textContent = text(props.label || 'Run');
      el.addEventListener('click', () => {
        rpc('plugins.uiAction', [pluginId, text(props.action || 'click'), {}]).catch(() => {});
      });
      return el;
    }
    case 'input': {
      const el = document.createElement('input');
      el.className = 'vp-input';
      el.placeholder = text(props.placeholder);
      el.addEventListener('change', () => {
        rpc('plugins.uiAction', [pluginId, text(props.action || 'input'), { value: el.value }]).catch(() => {});
      });
      return el;
    }
    case 'badge': {
      const el = document.createElement('span');
      el.className = 'vp-badge';
      el.textContent = text(props.value);
      return el;
    }
    case 'divider': {
      const hr = document.createElement('hr');
      hr.className = 'vp-divider';
      return hr;
    }
    case 'image': {
      const src = text(props.src);
      if (!/^https?:\/\//i.test(src)) return null;
      const img = document.createElement('img');
      img.className = 'vp-image';
      img.src = src;
      return img;
    }
    case 'table': {
      const table = document.createElement('table');
      table.className = 'vp-table';
      const columns: string[] = Array.isArray(props.columns) ? props.columns.map(String) : [];
      const rows: any[] = Array.isArray(props.rows) ? props.rows : [];
      if (columns.length) {
        const head = document.createElement('thead');
        const tr = document.createElement('tr');
        columns.forEach((col) => {
          const th = document.createElement('th');
          th.textContent = col;
          tr.appendChild(th);
        });
        head.appendChild(tr);
        table.appendChild(head);
      }
      const body = document.createElement('tbody');
      rows.forEach((row) => {
        const tr = document.createElement('tr');
        const cells = Array.isArray(row) ? row : Object.values(row || {});
        cells.forEach((cell: any) => {
          const td = document.createElement('td');
          td.textContent = String(cell);
          tr.appendChild(td);
        });
        body.appendChild(tr);
      });
      table.appendChild(body);
      return table;
    }
    default:
      return null;
  }
}
