/* 运行时英文化：把 DOM 文本与占位符翻译成英文（默认英文，切换中文时还原）
 * 采用原文快照（WeakMap），语言切换可逆；不侵入组件代码。
 */

import { currentLang } from './i18n';

type Rule = [RegExp, string];

const EXACT: Record<string, string> = {
  '下载': 'Download',
  '世界信息': 'World info',
  '事件流': 'Event stream',
  '允许并启用': 'Allow & enable',
  '光影': 'Shaders',
  '全部': 'All',
  '关于': 'About',
  '刷新': 'Refresh',
  '加载中': 'Loading',
  '加载失败': 'Load failed',
  '原版': 'Vanilla',
  '取消': 'Cancel',
  '启动': 'Launch',
  '启动中…': 'Launching…',
  '启动游戏': 'Launch game',
  '启用': 'Enable',
  '失败': 'Failed',
  '安装中…': 'Installing…',
  '安装失败': 'Install failed',
  '完成': 'Done',
  '实例': 'Instance',
  '实例 ID': 'Instance ID',
  '宿主日志': 'Host log',
  '宿主未启动': 'Host stopped',
  '就绪': 'Ready',
  '工具箱': 'Toolbox',
  '已加载': 'Loaded',
  '已启用': 'Enabled',
  '已安装': 'Installed',
  '已就绪': 'Ready',
  '已热重载': 'Reloaded',
  '已禁用': 'Disabled',
  '开始安装': 'Install',
  '当前版本': 'Current version',
  '待加载': 'Pending',
  '快捷操作': 'Quick actions',
  '打开数据目录': 'Open data folder',
  '打开日志目录': 'Open log folder',
  '授权确认': 'Permission request',
  '控制层': 'Control layer',
  '推荐': 'Featured',
  '插件': 'Plugins',
  '敬请期待': 'Coming soon',
  '数据包': 'Datapacks',
  '数据目录': 'Data folder',
  '整合包': 'Modpacks',
  '日志': 'Logs',
  '暂无内容': 'Nothing here yet',
  '暂无日志': 'No logs',
  '服务器插件': 'Server plugins',
  '未声明权限': 'No permission declared',
  '未安装': 'Not installed',
  '未登录': 'Not signed in',
  '未连接': 'Disconnected',
  '权限': 'Permissions',
  '架构': 'Architecture',
  '桥接失败': 'Bridge failed',
  '模组': 'Mods',
  '正在启动…': 'Starting…',
  '没有可用实例': 'No instance available',
  '测试 Layui 弹层': 'Test Layui layer',
  '游戏日志': 'Game log',
  '游戏本体': 'Game versions',
  '热重载': 'Hot reload',
  '版本': 'Version',
  '版本列表': 'Versions',
  '状态': 'Status',
  '目录': 'Folders',
  '禁用': 'Disable',
  '空闲': 'Idle',
  '简体中文': '简体中文',
  '联机': 'Multiplayer',
  '自动探测': 'Auto detect',
  '设置': 'Settings',
  '该插件未声明任何权限': 'This plugin declares no permissions',
  '语言 / Language': 'Language',
  '说明': 'Notes',
  '请先安装一个实例': 'Install an instance first',
  '调用返回': 'Call result',
  '资源包': 'Resource packs',
  '运行中': 'Running',
  '主界面': 'Home',
  '离线账号': 'Offline account',
  '当前账号': 'Current account',
  '设为当前': 'Use this account',
  '当前': 'Current',
  '添加': 'Add',
  '账号': 'Accounts',
  '加载器': 'Loader',
  '开始安装到': 'Install to',
  '选择实例': 'Select instance',
  '选择插件查看权限与日志': 'Select a plugin to see permissions and logs',
  '启动后这里会实时显示游戏输出': 'Game output appears here after launch',
  '游戏启动后这里会显示 MLC 事件': 'MLC events appear here after the game starts',
  '点击探测扫描本机 Java': 'Click detect to scan local Java runtimes',
  '下载缓存位于 assets/objects，下载中断会保留 .part 便于续传':
    'Downloads live in assets/objects; interrupted files keep .part for resume.',
  '请求以下能力。未声明的能力会被宿主拒绝':
    'This plugin requests the following capabilities. Undeclared calls are rejected.',
  '按天写入 %APPDATA%\\VeinLauncher\\logs\\YYYY-MM-DD.log':
    'Written daily to VeinLauncher/log/YYYY-MM-DD.log',
  '个实例': ' instances',
  '个文件': ' files',
  '已连接': 'Connected',
};

const RULES: Rule[] = [
  [/^宿主 (\d+)$/, 'Host $1'],
  [/^失败 (\d+)$/, 'Failed $1'],
  [/^安装 (\d+)$/, 'Install $1'],
  [/^推荐 (\d+)$/, 'Featured $1'],
  [/^版本列表 (\d+)$/, 'Versions ($1)'],
  [/^开始安装 (.+)$/, 'Installing $1'],
  [/^加载器安装完成：(.+)$/, 'Loader installed: $1'],
  [/^安装完成：成功 (\d+) \/ 失败 (\d+)$/, 'Installed: $1 ok / $2 failed'],
  [/^加载失败：(.+)$/, 'Load failed: $1'],
  [/^启动失败：(.+)$/, 'Launch failed: $1'],
  [/^安装失败：(.+)$/, 'Install failed: $1'],
  [/^操作失败：(.+)$/, 'Operation failed: $1'],
  [/^探测失败：(.+)$/, 'Detect failed: $1'],
  [/^读取插件失败：(.+)$/, 'Failed to read plugins: $1'],
  [/^已启动，PID (\d+)$/, 'Launched, PID $1'],
  [/^已连接 · pid (\d+)$/, 'Connected · pid $1'],
  [/^离线 · (.+)$/, 'Offline · $1'],
  [/^安装到 (.+)$/, 'Install to $1'],
  [/^未登录（离线模式）$/, 'Not signed in (offline)'],
];

const originals = new WeakMap<Node, string>();
const attrOriginals = new WeakMap<Element, Map<string, string>>();
const ATTRS = ['placeholder', 'title', 'aria-label'];

function translateText(source: string): string {
  if (currentLang() === 'zh') return source;
  const text = source.trim();
  if (!text) return source;
  if (EXACT[text]) return source.replace(text, EXACT[text]);
  for (const [pattern, replacement] of RULES) {
    if (pattern.test(text)) return source.replace(text, text.replace(pattern, replacement));
  }
  return source;
}

function applyText(node: Node): void {
  const source = originals.get(node) ?? node.nodeValue ?? '';
  if (!originals.has(node)) originals.set(node, source);
  const next = translateText(source);
  if (node.nodeValue !== next) node.nodeValue = next;
}

function applyAttrs(el: Element): void {
  let store = attrOriginals.get(el);
  if (!store) {
    store = new Map();
    attrOriginals.set(el, store);
  }
  for (const attr of ATTRS) {
    const value = el.getAttribute(attr);
    if (value === null) continue;
    if (!store.has(attr)) store.set(attr, value);
    const next = translateText(store.get(attr)!);
    if (value !== next) el.setAttribute(attr, next);
  }
}

function walk(root: Node): void {
  if (root.nodeType === Node.TEXT_NODE) {
    applyText(root);
    return;
  }
  if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_FRAGMENT_NODE) return;
  const el = root as Element;
  if (el.tagName) applyAttrs(el);
  el.childNodes?.forEach(walk);
}

let observer: MutationObserver | null = null;

export function startLocalization(): void {
  const root = document.getElementById('root');
  if (!root || observer) return;
  walk(root);
  observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'characterData') applyText(mutation.target);
      else mutation.addedNodes.forEach(walk);
    }
  });
  observer.observe(root, { childList: true, subtree: true, characterData: true });
  window.addEventListener('vein:lang', () => {
    if (root) walk(root);
  });
}
