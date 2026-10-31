import { useEffect, useReducer } from 'react';
import { rpc } from './bridge';

export type Lang = 'en' | 'zh';

let lang: Lang = 'en';
const listeners = new Set<() => void>();
const notify = () => listeners.forEach((fn) => fn());

/** 中文源串 → 英文（默认英文；找不到则原样返回） */
const EN: Record<string, string> = {
  'Launch': 'Launch',
  'Download': 'Download',
  'Plugins': 'Plugins',
  'Multiplayer': 'Multiplayer',
  'Settings': 'Settings',
  'Toolbox': 'Toolbox',
  'Home': 'Home',
  'Game log': 'Game log',
  'Launch game': 'Launch game',
  'Current version': 'Current version',
  'Not installed': 'Not installed',
  '去Download': 'Go to downloads',
  'CurrentAccounts': 'Current account',
  'Not signed in': 'Not signed in',
  'Not signed in（Offline模式）': 'Not signed in (offline)',
  'Offline': 'Offline',
  'Ready': 'Ready',
  'Select instance': 'Select instance',
  'Versions': 'Versions',
  'Featured': 'Featured',
  'Refresh': 'Refresh',
  'Install': 'Install',
  'Installing…': 'Installing…',
  'Installed': 'Installed',
  'Install failed': 'Install failed',
  'Instance': 'Instance',
  'Loader': 'Loader',
  'Loader installed': 'Loader installed',
  'Vanilla': 'Vanilla',
  'Mods': 'Mods',
  'Modpacks': 'Modpacks',
  'Server plugins': 'Server plugins',
  'Resource packs': 'Resource packs',
  '光影': 'Shaders',
  'Datapacks': 'Datapacks',
  'Game versions': 'Game versions',
  'Enable': 'Enable',
  'Disable': 'Disable',
  'Hot reload': 'Hot reload',
  'Permissions': 'Permissions',
  'Host log': 'Host log',
  'Host stopped': 'Host stopped',
  '全部': 'All',
  'Enabled': 'Enabled',
  'Disabled': 'Disabled',
  'Select a plugin to see permissions and logs': 'Select a plugin to see permissions and logs',
  'VL-MLC Control layer': 'VL-MLC control layer',
  'Connection': 'Connection',
  'Status': 'Status',
  'Running': 'Running',
  'Idle': 'Idle',
  'Call result': 'Call result',
  'Event stream': 'Event stream',
  'World info': 'World info',
  'Coming soon': 'Coming soon',
  'About': 'About',
  'Version': 'Version',
  'Data folder': 'Data directory',
  'Architecture': 'Architecture',
  'Log folder': 'Log directory',
  'Open log folder': 'Open log folder',
  'Open data folder': 'Open data folder',
  'Auto detect': 'Auto detect',
  'Quick actions': 'Quick actions',
  'Folders': 'Folders',
  'Notes': 'Notes',
  'Test Layui layer': 'Test Layui layer',
  'Layui Component preview': 'Layui components',
  'Accounts': 'Accounts',
  'Offline account': 'Offline account',
  '添加': 'Add',
  '设为Current': 'Use this account',
  'Current': 'Current',
  'Permission request': 'Permission request',
  'Cancel': 'Cancel',
  'Allow & enable': 'Allow & enable',
  'Downloads': 'Downloads',
  'Done': 'Done',
  'Failed': 'Failed',
  'Summary': 'Description',
  'Nothing here yet': 'Nothing here yet',
  'No plugins yet': 'No plugins installed',
  'No accounts yet': 'No account yet',
  'Nothing installed yet': 'No version installed yet',
};

export async function initI18n(): Promise<void> {
  try {
    const result = await rpc<{ lang: string }>('i18n.get');
    lang = result.lang === 'zh_CN' ? 'zh' : 'en';
  } catch {
    lang = 'en';
  }
  notify();
  window.dispatchEvent(new Event('vein:lang'));
}

export function currentLang(): Lang {
  return lang;
}

export function setLang(next: Lang): void {
  lang = next;
  rpc('i18n.set', [next === 'zh' ? 'zh_CN' : 'en_US']).catch(() => {});
  notify();
  window.dispatchEvent(new Event('vein:lang'));
}

export function t(source: string): string {
  return lang === 'zh' ? source : EN[source] ?? source;
}

export function useI18n() {
  const [, force] = useReducer((x: number) => x + 1, 0);
  useEffect(() => {
    listeners.add(force);
    return () => {
      listeners.delete(force);
    };
  }, []);
  return { t, lang, setLang, currentLang };
}
