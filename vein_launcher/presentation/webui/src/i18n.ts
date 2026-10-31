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

/** 英文界面 → 简体中文（界面源码是英文，切到中文时走这张表） */
const ZH: Record<string, string> = {
  Launch: '启动',
  Skins: '皮肤',
  Download: '下载',
  Plugins: '插件',
  MLC: 'MLC',
  Multiplayer: '联机',
  Settings: '设置',
  Toolbox: '工具箱',
  Instances: '实例',
  Appearance: '外观',
  Accounts: '账号',
  'Java runtime': 'Java 环境',
  'Game folder': '游戏目录',
  Logs: '日志',
  About: '关于',
  Theme: '主题',
  Language: '语言',
  Dark: '深色',
  Light: '浅色',
  Clear: '透明',
  System: '跟随系统',
  English: 'English',
  'Check for updates': '检查更新',
  'Download update': '下载更新',
  'Install update': '安装更新',
  'You are on the latest version.': '已是最新版本。',
  'Update available': '发现新版本',
  Version: '版本',
  'Data folder': '数据目录',
  'Open folder': '打开目录',
  'Delete instance': '删除实例',
  'Resource packs': '资源包',
  Shaders: '光影',
  Datapacks: '数据包',
  Modpacks: '整合包',
  Worlds: '世界',
  Console: '控制台',
  Mods: '模组',
  Enabled: '已启用',
  Disabled: '已禁用',
  Delete: '删除',
  Cancel: '取消',
  Refresh: '刷新',
  'Download more': '下载更多',
  Installing: '安装中',
  'No accounts yet': '还没有账号',
  'Add offline': '添加离线账号',
  'Sign in': '登录',
  Ready: '就绪',
  'Current version': '当前版本',
  'Not installed': '未安装',
  'Launch game': '启动游戏',
  'Game log': '游戏日志',
  'Select instance': '选择实例',
  'No worlds in this instance yet.': '这个实例还没有世界。',
  'No installed versions yet.': '还没有安装任何版本。',
  'Search skins…': '搜索皮肤…',
  'LittleSkin library': 'LittleSkin 皮肤库',
  Search: '搜索',
  'Load more': '加载更多',
  'Slim arms': '细手臂',
  'Import PNG': '导入 PNG',
  'Load from LittleSkin': '从 LittleSkin 读取',
  Remove: '移除',
  Back: '上一步',
  Continue: '继续',
  'Enter launcher': '进入启动器',
  'Skip setup': '跳过设置',
  'Get started': '开始',
  'Welcome to Vein Launcher': '欢迎使用 Vein Launcher',
  'What you can do': '能做什么',
  'Your account': '你的账号',
  Privacy: '隐私',
  Offline: '离线',
  Microsoft: '微软',
  LittleSkin: 'LittleSkin',
  'Classic': '经典',
  'Slim': '纤细',
  'Downloading': '下载中',
  'You are ready to play': '可以开始玩了',
  'Your data stays on your PC': '数据保存在你自己的电脑上',
  'Choose your account': '选择账号',
  'Everything in one window': '所有功能集中在一个窗口',
};

export function t(source: string): string {
  if (lang === 'zh') return ZH[source] ?? source;
  return EN[source] ?? source;
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
