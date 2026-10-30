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
    font: 13px/1.6 "Microsoft YaHei UI", system-ui, sans-serif;
    background: #ffffff; color: #1b2330;
    border: 1px solid #e8ecf3; border-radius: 14px;
    box-shadow: 0 12px 32px rgba(20,30,50,.18);
    padding: 16px; width: 360px;
  }
  .vp-title { font-weight: 700; font-size: 14px; margin-bottom: 10px; }
  .vp-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 6px 0; }
  .vp-text { font-size: 12.5px; color: #5a6679; }
  .vp-button {
    border: 1px solid #2f6cf0; background: #2f6cf0; color: #fff;
    border-radius: 8px; padding: 5px 12px; cursor: pointer; font-size: 12.5px;
  }
  .vp-button:hover { filter: brightness(1.05); }
  .vp-input { border: 1px solid #dbe2ec; border-radius: 8px; padding: 5px 10px; font-size: 12.5px; }
  .vp-badge {
    font: 11px ui-monospace, monospace; color: #2f6cf0;
    background: #eef4ff; border: 1px solid #dbe7ff; border-radius: 6px; padding: 2px 8px;
  }
  .vp-divider { border: 0; border-top: 1px solid #e8ecf3; margin: 10px 0; }
  .vp-table { width: 100%; border-collapse: collapse; font-size: 12px; }
  .vp-table th, .vp-table td { border-bottom: 1px solid #eef2f8; padding: 5px 6px; text-align: left; }
  .vp-image { max-width: 100%; border-radius: 8px; }
  .vp-close {
    position: absolute; top: 8px; right: 10px; border: 0; background: transparent;
    color: #8c97a8; cursor: pointer; font-size: 14px;
  }
`;

export function PluginUiHost() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [current, setCurrent] = useState<{ pluginId: string; tree: UiNode } | null>(null);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { pluginId?: string; tree?: UiNode };
      if (detail?.tree && detail.tree.type) {
        setCurrent({ pluginId: String(detail.pluginId || 'plugin'), tree: detail.tree });
      }
    };
    (window as any).__veinUi = (payload: any) =>
      window.dispatchEvent(new CustomEvent('vein:ui', { detail: payload }));
    window.addEventListener('vein:ui', handler);
    return () => window.removeEventListener('vein:ui', handler);
  }, []);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.innerHTML = '';
    if (!current) return;

    const shadow = host.attachShadow({ mode: 'closed' });
    const style = document.createElement('style');
    style.textContent = SHADOW_STYLE;
    shadow.appendChild(style);

    const shell = document.createElement('div');
    shell.style.position = 'fixed';
    shell.style.right = '24px';
    shell.style.bottom = '64px';
    shell.style.zIndex = '150';
    shadow.appendChild(shell);

    const panel = renderNode(current.tree, shadow, current.pluginId);
    if (panel) {
      const close = document.createElement('button');
      close.className = 'vp-close';
      close.textContent = '×';
      close.addEventListener('click', () => setCurrent(null));
      const wrapper = document.createElement('div');
      wrapper.style.position = 'relative';
      wrapper.appendChild(close);
      wrapper.appendChild(panel);
      shell.appendChild(wrapper);
    }
  }, [current]);

  return <div ref={hostRef} />;
}

function renderNode(node: UiNode, root: ShadowRoot, pluginId: string): HTMLElement | null {
  const props = node.props || {};
  const children = (node.children || []).map((child) => renderNode(child, root, pluginId)).filter(Boolean) as HTMLElement[];

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
      const el = document.createElement('hr');
      el.className = 'vp-divider';
      return el;
    }
    case 'image': {
      const src = text(props.src);
      if (!/^https?:\/\//i.test(src)) return null;
      const el = document.createElement('img');
      el.className = 'vp-image';
      el.src = src;
      return el;
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
