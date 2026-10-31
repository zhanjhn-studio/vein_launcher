import React, { useCallback, useEffect, useState } from 'react';
import { on, rpc } from './bridge';
import type { AccountInfo, VersionInfo } from './types';
import {
  DownloadPage,
  MlcPage,
  MultiplayerPage,
  PluginsPage,
  ToolboxPage,
} from './pages';
import { LaunchPage } from './launchPage';
import { SettingsPage } from './settingsPage';
import { DownloadBar, Toast } from './ui';
import { PluginUiHost } from './pluginUi';
import { initI18n, t, useI18n } from './i18n';
import { initTheme, Theme } from './theme';

const NAV = [
  { key: 'launch', label: '启动', icon: 'layui-icon-play' },
  { key: 'download', label: '下载', icon: 'layui-icon-download-circle' },
  { key: 'plugins', label: '插件', icon: 'layui-icon-app', star: true },
  { key: 'mlc', label: 'MLC', icon: 'layui-icon-console' },
  { key: 'multiplayer', label: '联机', icon: 'layui-icon-link' },
  { key: 'settings', label: '设置', icon: 'layui-icon-set' },
  { key: 'toolbox', label: '工具箱', icon: 'layui-icon-util' },
];

interface Announcement {
  id?: string;
  level: 'light' | 'heavy';
  title: string;
  content?: string;
  url?: string;
}

interface AnnouncementPayload {
  announcements: Announcement[];
  force_update: boolean;
  min_version: string;
  update: { version?: string; url?: string; notes?: string };
}

const KNOWN_PAGES = new Set(NAV.map((n) => n.key));

function pageFromHash(): string {
  const raw = window.location.hash.replace(/^#\/?/, '').trim();
  return KNOWN_PAGES.has(raw) ? raw : 'launch';
}

function useHashRoute(): [string, (page: string) => void] {
  const [page, setPageState] = useState(pageFromHash);
  useEffect(() => {
    const sync = () => setPageState(pageFromHash());
    window.addEventListener('hashchange', sync);
    if (!window.location.hash) window.location.hash = '#/launch';
    return () => window.removeEventListener('hashchange', sync);
  }, []);
  const navigate = useCallback((next: string) => {
    const target = KNOWN_PAGES.has(next) ? next : 'launch';
    if (pageFromHash() !== target) window.location.hash = `#/${target}`;
    setPageState(target);
  }, []);
  return [page, navigate];
}

export function App() {
  useI18n();
  const [page, setPage] = useHashRoute();
  const [toast, setToast] = useState('');
  const [installed, setInstalled] = useState<VersionInfo[]>([]);
  const [accounts, setAccounts] = useState<AccountInfo[]>([]);
  const [selected, setSelected] = useState('');
  const [news, setNews] = useState<AnnouncementPayload | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [theme, setTheme] = useState<Theme>('dark');

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
    const alpha = localStorage.getItem('vl.transparent') === 'on';
    document.documentElement.dataset.transparent = alpha ? 'on' : 'off';
    setTheme(initTheme());
    initI18n();
    refreshInstalled().catch(() => {});
    rpc<AccountInfo[]>('accounts.list').then(setAccounts).catch(() => {});
    rpc<AnnouncementPayload>('announcements.get').then(setNews).catch(() => setNews(null));
    const offNav = on<string>('vein:navigate', (p) => setPage(p));
    const offNotify = on<{ title: string; message: string }>('vein:notify', (d) =>
      notify(`${d.title}：${d.message}`)
    );
    return () => {
      offNav();
      offNotify();
    };
  }, [notify, refreshInstalled, setPage]);

  const lightNews = (news?.announcements ?? []).filter((a) => a.level !== 'heavy');
  const forced = Boolean(news?.force_update);
  const forcedItems = (news?.announcements ?? []).filter((a) => a.level === 'heavy');
  const current = NAV.find((n) => n.key === page) ?? NAV[0];

  return (
    <div className="app">
      <aside className="side">
        <div className="side-brand">
          <img src="logo.png" alt="Vein" />
          <span>VEIN</span>
        </div>
        <nav className="side-nav">
          {NAV.map((item) => (
            <button
              key={item.key}
              className={`side-btn ${page === item.key ? 'active' : ''} ${item.star ? 'star' : ''}`}
              onClick={() => setPage(item.key)}
            >
              <i className={`ico layui-icon ${item.icon}`} />
              <span className="txt">{t(item.label)}</span>
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <span className="side-ver">v0.0.3</span>
        </div>
      </aside>

      <main className="main">
        <header className="main-head">
          <h1>{t(current.label)}</h1>
          <span className="sub">Vein Launcher 0.0.3</span>
          <div className="spacer" />
          <span className="sub">{installed.length} 个实例</span>
        </header>

        {lightNews.length > 0 && !dismissed && (
          <div className="notice-bar">
            <i className="layui-icon layui-icon-notice" />
            <span>{lightNews[0].title}</span>
            {lightNews[0].content && <em>{lightNews[0].content}</em>}
            {lightNews[0].url && (
              <button className="btn sm" onClick={() => rpc('app.openUrl', [lightNews[0].url])}>
                详情
              </button>
            )}
            <button className="notice-close" onClick={() => setDismissed(true)}>
              <i className="layui-icon layui-icon-close" />
            </button>
          </div>
        )}

        <div className="main-body">
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
        </div>
      </main>

      {forced && !dismissed && (
        <div className="force-mask">
          <div className="force-modal">
            <h2>需要更新</h2>
            <p className="muted">
              当前版本被重要公告锁定，请更新后继续。
              {news?.min_version ? ` 最低版本：${news.min_version}` : ''}
            </p>
            {forcedItems.map((item, index) => (
              <div className="force-item" key={item.id ?? index}>
                <b>{item.title}</b>
                {item.content && <div className="muted">{item.content}</div>}
              </div>
            ))}
            <div className="row-actions">
              {news?.update?.url && (
                <button className="btn primary" onClick={() => rpc('app.openUrl', [news.update?.url])}>
                  下载更新
                </button>
              )}
              <button className="btn" onClick={() => setDismissed(true)}>
                暂不更新
              </button>
            </div>
          </div>
        </div>
      )}

      <DownloadBar />
      <PluginUiHost />
      <Toast text={toast} />
    </div>
  );
}
