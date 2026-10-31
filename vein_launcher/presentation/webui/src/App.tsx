import React, { useCallback, useEffect, useState } from 'react';
import { on, rpc } from './bridge';
import type { AccountInfo, AppInfo, VersionInfo } from './types';
import {
  DownloadPage,
  MlcPage,
  MultiplayerPage,
  PluginsPage,
  ToolboxPage,
} from './pages';
import { LaunchPage } from './launchPage';
import { DownloadPage } from './downloadPage';
import { SettingsPage } from './settingsPage';
import { SkinsPage } from './skinsPage';
import { DownloadMonitor, Toast } from './ui';
import { PluginUiHost } from './pluginUi';
import { initI18n, t, useI18n } from './i18n';
import { initTheme, Theme } from './theme';
import { Onboarding, Splash } from './onboarding';

const NAV = [
  { key: 'launch', label: 'Launch', icon: 'layui-icon-play', iconImg: 'arrow.png' },
  { key: 'skins', label: 'Skins', icon: 'layui-icon-picture', iconImg: 'writable_book.png' },
  { key: 'download', label: 'Download', icon: 'layui-icon-download-circle', iconImg: 'hopper.png' },
  { key: 'plugins', label: 'Plugins', icon: 'layui-icon-app', iconImg: 'command_block.png', star: true },
  { key: 'mlc', label: 'MLC', icon: 'layui-icon-console', iconImg: 'chest.png' },
  { key: 'multiplayer', label: 'Multiplayer', icon: 'layui-icon-link', iconImg: 'oak_sign.png' },
  { key: 'settings', label: 'Settings', icon: 'layui-icon-set', iconImg: 'crafting_table.png' },
  { key: 'toolbox', label: 'Toolbox', icon: 'layui-icon-util', iconImg: 'bucket.png' },
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
  const [booted, setBooted] = useState(false);
  const [firstRun, setFirstRun] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

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

  const refreshAccounts = useCallback(async () => {
    const list = await rpc<AccountInfo[]>('accounts.list');
    setAccounts(list);
    return list;
  }, []);

  useEffect(() => {
    const alpha = localStorage.getItem('vl.transparent') === 'on';
    document.documentElement.dataset.transparent = alpha ? 'on' : 'off';
    setTheme(initTheme());
    initI18n();
    refreshInstalled().catch(() => {});
    rpc<AccountInfo[]>('accounts.list').then(setAccounts).catch(() => {});
    rpc<AppInfo>('app.info')
      .then((info) => {
        const fresh = Boolean(info.firstRun);
        setFirstRun(fresh);
        window.setTimeout(
          () => {
            setBooted(true);
            if (fresh) setShowOnboarding(true);
          },
          fresh ? 3200 : 900
        );
      })
      .catch(() => setBooted(true));
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

  if (!booted) {
    return <Splash firstRun={firstRun} />;
  }

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
              <img className="side-ico" src={`icons/${item.iconImg}`} alt="" />
              <span className="txt">{t(item.label)}</span>
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <DownloadMonitor />
          <span className="side-ver">v0.0.3</span>
        </div>
      </aside>

      <main className="main">
        <header className="main-head">
          <img className="head-ico" src={`icons/${current.iconImg}`} alt="" />
          <h1>{t(current.label)}</h1>
          <span className="sub">Vein Launcher 0.0.3</span>
          <div className="spacer" />
          <span className="sub">{installed.length} instances</span>
        </header>

        {lightNews.length > 0 && !dismissed && (
          <div className="notice-bar">
            <i className="layui-icon layui-icon-notice" />
            <span>{lightNews[0].title}</span>
            {lightNews[0].content && <em>{lightNews[0].content}</em>}
            {lightNews[0].url && (
              <button className="btn sm" onClick={() => rpc('app.openUrl', [lightNews[0].url])}>
                Details
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
              announcements={lightNews}
            />
          )}
          {page === 'skins' && <SkinsPage notify={notify} />}
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
            <h2>Update required</h2>
            <p className="muted">
              This build is blocked by an urgent announcement. Please update to continue.
              {news?.min_version ? ` Minimum: ${news.min_version}` : ''}
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
                  Download update
                </button>
              )}
              <button className="btn" onClick={() => setDismissed(true)}>
                Not now
              </button>
            </div>
          </div>
        </div>
      )}

      <PluginUiHost />
      {showOnboarding && (
        <Onboarding
          notify={notify}
          onDone={() => {
            setShowOnboarding(false);
            refreshAccounts().catch(() => {});
          }}
        />
      )}
      <Toast text={toast} />
    </div>
  );
}
