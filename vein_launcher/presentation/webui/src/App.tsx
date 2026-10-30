import React, { useCallback, useEffect, useState } from 'react';
import { on, rpc } from './bridge';
import type { AccountInfo, VersionInfo } from './types';
import {
  DownloadPage,
  LaunchPage,
  MlcPage,
  MultiplayerPage,
  PluginsPage,
  SettingsPage,
  ToolboxPage,
} from './pages';
import { DownloadBar, Toast } from './ui';

const NAV = [
  { key: 'launch', label: '启动', icon: 'layui-icon-play' },
  { key: 'download', label: '下载', icon: 'layui-icon-download-circle' },
  { key: 'plugins', label: '插件', icon: 'layui-icon-app', star: true },
  { key: 'mlc', label: 'MLC', icon: 'layui-icon-console' },
  { key: 'multiplayer', label: '联机', icon: 'layui-icon-link' },
  { key: 'settings', label: '设置', icon: 'layui-icon-set' },
  { key: 'toolbox', label: '工具箱', icon: 'layui-icon-util' },
];

export function App() {
  const [page, setPage] = useState('launch');
  const [toast, setToast] = useState('');
  const [installed, setInstalled] = useState<VersionInfo[]>([]);
  const [accounts, setAccounts] = useState<AccountInfo[]>([]);
  const [selected, setSelected] = useState('');

  const notify = useCallback((text: string) => {
    setToast(text);
    window.clearTimeout((notify as any)._timer);
    (notify as any)._timer = window.setTimeout(() => setToast(''), 3600);
  }, []);

  const refreshInstalled = useCallback(async () => {
    const list = await rpc<VersionInfo[]>('versions.info');
    setInstalled(list);
    setSelected((prev) => (prev && list.some((v) => v.id === prev) ? prev : list[0]?.id ?? ''));
  }, []);

  useEffect(() => {
    refreshInstalled().catch(() => {});
    rpc<AccountInfo[]>('accounts.list').then(setAccounts).catch(() => {});
    const offNav = on<string>('vein:navigate', (p) => setPage(p));
    const offNotify = on<{ title: string; message: string }>('vein:notify', (d) =>
      notify(`${d.title}：${d.message}`)
    );
    return () => {
      offNav();
      offNotify();
    };
  }, [notify, refreshInstalled]);

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src="logo.png" alt="Vein" />
          <span className="brand-text">VEIN</span>
        </div>
        <nav className="nav">
          {NAV.map((item) => (
            <button
              key={item.key}
              className={`nav-btn ${page === item.key ? 'active' : ''} ${item.star ? 'star' : ''}`}
              onClick={() => setPage(item.key)}
            >
              <i className={`ico layui-icon ${item.icon}`} />
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="content">
        {page === 'launch' && (
          <LaunchPage
            installed={installed}
            accounts={accounts}
            selected={selected}
            onSelect={setSelected}
            notify={notify}
          />
        )}
        {page === 'download' && (
          <DownloadPage installed={installed} onInstalled={refreshInstalled} notify={notify} />
        )}
        {page === 'plugins' && <PluginsPage notify={notify} />}
        {page === 'mlc' && <MlcPage installed={installed} selected={selected} notify={notify} />}
        {page === 'multiplayer' && <MultiplayerPage />}
        {page === 'settings' && <SettingsPage notify={notify} />}
        {page === 'toolbox' && <ToolboxPage notify={notify} />}
      </main>

      <DownloadBar />
      <Toast text={toast} />
    </div>
  );
}
