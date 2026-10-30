import { useEffect, useReducer } from 'react';
import { rpc } from './bridge';

export type Lang = 'en' | 'zh';

let lang: Lang = 'en';
const listeners = new Set<() => void>();
const notify = () => listeners.forEach((fn) => fn());

/** 中文源串 → 英文（默认英文；找不到则原样返回） */
const EN: Record<string, string> = {
  '启动': 'Launch',
  '下载': 'Download',
  '插件': 'Plugins',
  '联机': 'Multiplayer',
  '设置': 'Settings',
  '工具箱': 'Toolbox',
  '主界面': 'Home',
  '游戏日志': 'Game log',
  '启动游戏': 'Launch game',
  '当前版本': 'Current version',
  '未安装': 'Not installed',
  '去下载': 'Go to downloads',
  '当前账号': 'Current account',
  '未登录': 'Not signed in',
  '未登录（离线模式）': 'Not signed in (offline)',
  '离线': 'Offline',
  '就绪': 'Ready',
  '选择实例': 'Select instance',
  '版本列表': 'Versions',
  '推荐': 'Featured',
  '刷新': 'Refresh',
  '安装': 'Install',
  '安装中…': 'Installing…',
  '开始安装': 'Install',
  '安装完成': 'Install finished',
  '安装失败': 'Install failed',
  '实例': 'Instance',
  '加载器': 'Loader',
  '加载器安装完成': 'Loader installed',
  '原版': 'Vanilla',
  '模组': 'Mods',
  '整合包': 'Modpacks',
  '服务器插件': 'Server plugins',
  '资源包': 'Resource packs',
  '光影': 'Shaders',
  '数据包': 'Datapacks',
  '游戏本体': 'Game versions',
  '已安装': 'Installed',
  '启用': 'Enable',
  '禁用': 'Disable',
  '热重载': 'Hot reload',
  '权限': 'Permissions',
  '宿主日志': 'Host log',
  '宿主未启动': 'Host stopped',
  '全部': 'All',
  '已启用': 'Enabled',
  '已禁用': 'Disabled',
  '选择插件查看权限与日志': 'Select a plugin to see permissions and logs',
  'VL-MLC 控制层': 'VL-MLC control layer',
  '连接': 'Connection',
  '状态': 'Status',
  '运行中': 'Running',
  '空闲': 'Idle',
  '调用返回': 'Call result',
  '事件流': 'Event stream',
  '世界信息': 'World info',
  '敬请期待': 'Coming soon',
  '关于': 'About',
  '版本': 'Version',
  '数据目录': 'Data directory',
  '架构': 'Architecture',
  '日志目录': 'Log directory',
  '打开日志目录': 'Open log folder',
  '打开数据目录': 'Open data folder',
  '自动探测': 'Auto detect',
  '快捷操作': 'Quick actions',
  '目录': 'Folders',
  '说明': 'Notes',
  '测试 Layui 弹层': 'Test Layui layer',
  'Layui 组件预览': 'Layui components',
  '账号': 'Accounts',
  '离线账号': 'Offline account',
  '添加': 'Add',
  '设为当前': 'Use this account',
  '当前': 'Current',
  '授权确认': 'Permission request',
  '取消': 'Cancel',
  '允许并启用': 'Allow & enable',
  '下载任务': 'Downloads',
  '完成': 'Done',
  '失败': 'Failed',
  '简介': 'Description',
  '暂无内容': 'Nothing here yet',
  '还没有插件': 'No plugins installed',
  '还没有账号': 'No account yet',
  '还没有安装任何版本': 'No version installed yet',
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
