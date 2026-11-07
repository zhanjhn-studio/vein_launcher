/**
 * UI 文案翻译层
 *
 * 界面源码是英文（项目默认语言）。切到中文时不需要给每个组件套 t()：
 * 这里在 DOM 层把「文本节点 + placeholder/title/aria-label」按词典替换成中文，
 * 并记住原文；切回英文时逐字还原。动态渲染的内容由 MutationObserver 继续翻译。
 *
 * 跳过代码/日志/输入框等不该翻译的区域。
 */

import { currentLang } from './i18n';

export type Lang = 'en' | 'zh';

/** 英文 → 中文。只放界面文案，不放数据（版本号、文件名、用户名等）。 */
const ZH: Record<string, string> = {
  // ---------- 通用 ----------
  'About': '关于',
  'Accounts': '账户',
  'Add offline': '添加离线账户',
  'Announcements': '公告',
  'Appearance': '外观',
  'Auto detect': '自动检测',
  'Cancel': '取消',
  'Check for updates': '检查更新',
  'Clear': '清空',
  'Close': '关闭',
  'Collapse': '收起',
  'Coming soon': '即将推出',
  'Confirm': '确认',
  'Copy': '复制',
  'Current': '当前',
  'Delete': '删除',
  'Disabled': '已禁用',
  'Download': '下载',
  'Downloads': '下载',
  'Enabled': '已启用',
  'Expand': '展开',
  'Load more': '加载更多',
  'No': '否',
  'Off': '关',
  'On': '开',
  'Open folder': '打开文件夹',
  'Refresh': '刷新',
  'Remove': '移除',
  'Save': '保存',
  'Search': '搜索',
  'Use': '使用',
  'Use default': '使用默认',
  'Version': '版本',
  'Yes': '是',
  'instances': '个实例',
  'versions': '个版本',
  'worlds': '个世界',
  'files': '个文件',
  'mods': '个模组',
  'idle': '空闲',
  'installed': '已安装',
  'release': '正式版',
  'seconds': '秒',
  'Stack': '堆叠',
  'Count': '数量',

  // ---------- 启动页 ----------
  'Launch': '启动',
  'Launch game': '启动游戏',
  'Instance': '实例',
  'Instances': '实例',
  'Offline': '离线',
  'Offline Steve': '离线玩家 Steve',
  'Game log': '游戏日志',
  'Install a version': '安装游戏版本',
  'Manage instance': '管理实例',
  'Manage mods and files': '管理模组与文件',
  'Skin library': '皮肤库',
  'Download monitor': '下载监控',
  'No active downloads': '没有进行中的下载',
  'Download more': '下载更多',
  'Vanilla, Fabric, Forge, Quilt, NeoForge': '原版、Fabric、Forge、Quilt、NeoForge',
  'Mods, resource packs, worlds and seeds': '模组、资源包、世界与种子',
  'Import a PNG or download from LittleSkin': '导入 PNG 或从 LittleSkin 下载',
  'Vein Launcher 0.1.0 is out': 'Vein Launcher 0.1.0 已发布',
  'One-click updates, LittleSkin library and a brand-new instance manager.':
    '一键更新、LittleSkin 皮肤库与全新的实例管理器。',

  // ---------- 下载页 ----------
  'Pick a category, then choose exactly what to install': '先选分类，再决定具体安装什么',
  'Vanilla & Loaders': '原版与加载器',
  'Mods': '模组',
  'Modpacks': '整合包',
  'Resource packs': '资源包',
  'Shaders': '光影',
  'Datapacks': '数据包',
  'OptiFine': 'OptiFine',
  'Install game versions with Fabric, Forge, Quilt, NeoForge': '安装原版或 Fabric / Forge / Quilt / NeoForge 版本',
  'Mods from Modrinth, filtered by game version and loader': '来自 Modrinth 的模组，按游戏版本与加载器过滤',
  'Full modpacks (.mrpack) with automatic setup': '完整整合包（.mrpack），自动安装',
  'Textures and resource packs': '材质与资源包',
  'Shader packs for Iris / OptiFine': '适用于 Iris / OptiFine 的光影包',
  'Datapacks for worlds and servers': '用于世界与服务器的数据包',
  'Run the OptiFine installer against your game folder': '在游戏目录运行 OptiFine 安装器',
  'In-game commands': '游戏内指令',
  'Commands': '指令',
  'Builder': '构建器',
  'Common commands': '常用指令',
  'Can follow': '可以接',
  'Results': '搜索结果',
  'Hotkeys': '快捷键',
  'Command list': '指令列表',
  'No matching commands': '没有匹配的指令',
  'Palette hotkey': '速查窗热键',
  'Bound': '已绑定',
  'Delete command': '删除指令',
  'Add': '添加',
  'Save & apply': '保存并应用',
  'Saving…': '保存中…',
  'Name (e.g. Home)': '名称（例如：回城）',
  'No hotkey': '无热键',
  'No custom commands yet. Use “Add” below to create one.': '还没有自定义指令，点下面的「添加」写一条。',
  'Type a command prefix (for example kill) and the list below shows what can follow it. Click a candidate to append it.':
    '先输入一段指令（例如 kill），下面会列出它能接什么；点候选项直接追加到后面。',
  'No more candidates: the command is complete, or it needs manual arguments (names, coordinates).':
    '没有更多候选：指令已经完整，或需要手动填参数（名字、坐标）。',
  'This command is complete — copy it and paste it in game.': '这条指令已经完整，复制后回游戏粘贴即可。',
  'Command complete — copy it': '指令已完整，可直接复制',
  'With the launcher in the background and the game focused, press Ctrl + Alt + number to copy that command; switch to the game, press T and paste with Ctrl+V.':
    '启动器在后台、游戏在前台时，按 Ctrl + Alt + 数字 可复制对应指令；切回游戏按 T 打开聊天框、Ctrl+V 粘贴。',
  'These commands need cheats enabled or OP. On a server, follow the server\'s rules.':
    '这些指令需要世界开启作弊或拥有 OP 权限；在服务器里请遵守服务器规则。',
  'Search commands or items: sword / kill / diamond': '搜索指令或物品：sword / kill / diamond',
  'No commands or items match': '没有匹配的指令或物品',

  // ---------- 皮肤页 ----------
  'Skins': '皮肤',
  'LittleSkin': 'LittleSkin',
  'LittleSkin library': 'LittleSkin 皮肤库',
  'LittleSkin email': 'LittleSkin 邮箱',
  'Password': '密码',
  'Sign in': '登录',
  'Sign in with Microsoft': '使用微软账号登录',
  'Skin library': '皮肤库',
  'Import PNG': '导入 PNG',
  'Import…': '导入…',
  'Classic': '经典',
  'Slim': '纤细',
  'Slim arms': '纤细手臂',
  'Classic (4px arms)': '经典（4px 手臂）',
  'Search skins…': '搜索皮肤…',
  'No skin preview yet': '暂无皮肤预览',
  'no skin': '未设置皮肤',
  'skin set': '已设置皮肤',
  'Browse public skins and download them straight into an account.': '浏览公开皮肤并直接下载到账号。',
  'Download a public skin straight into the selected account': '把公开皮肤直接下载到选中的账号',
  'Import a PNG or read the skin from LittleSkin': '导入 PNG，或从 LittleSkin 读取皮肤',
  'Offline username (3-16)': '离线用户名（3-16 字符）',
  'littleskin.cn skins and its online servers. The launcher stores only the access token, never your password.':
    'littleskin.cn 的皮肤与在线服务器。启动器只保存令牌，不保存你的密码。',

  // ---------- 设置页 ----------
  'Settings': '设置',
  'Language': '语言',
  'Theme': '主题',
  'Dark': '深色',
  'Light': '浅色',
  'System': '跟随系统',
  'English': 'English',
  'Chinese (Simplified)': '简体中文',
  'Compact mode': '简洁模式',
  'Hides the sidebar; a translucent handle on the left edge slides it back in. Clicking a page closes it again.':
    '隐藏侧栏；左边缘的半透明把手可以把它滑回来，点任意页面后再次收起。',
  'Fade out after idle': '空闲后淡出',
  'Wallpaper': '壁纸',
  'Java runtime': 'Java 运行时',
  'Game folder': '游戏目录',
  'Data folder': '数据目录',
  'Logs': '日志',
  'Choose .minecraft': '选择 .minecraft 目录',
  'Install Java 8': '安装 Java 8',
  'Install Java 17': '安装 Java 17',
  'Install Java 21': '安装 Java 21',
  'No scan yet. Click Auto detect.': '还没有扫描结果，点「自动检测」。',
  'Azure client id': 'Azure 客户端 ID',
  'authority (common / tenant id)': 'authority（common / 租户 ID）',
  'Written daily to VeinLauncher/log, split into launcher / plugin / mlc / download.':
    '按天写入 VeinLauncher/log，按 launcher / plugin / mlc / download 分开存放。',
  'Python + PySide6 WebView + React + TS': 'Python + PySide6 WebView + React + TS',
  'Grouped sections': '分组折叠',
  'Open log folder': '打开日志目录',

  // ---------- 实例页 ----------
  'Console': '控制台',
  'Worlds': '世界',
  'Delete instance': '删除实例',
  'Delete instance?': '删除实例？',

  // ---------- MLC ----------
  'MLC': 'MLC',
  'MLC master switch': 'MLC 总开关',
  'When off, MLC data calls (saves, player data, mod install) are rejected.':
    '关闭后，MLC 的数据调用（存档、玩家数据、安装模组）会被拒绝。',
  'VL-MLC Control layer': 'VL-MLC 控制层',
  'Connection': '连接',
  'Call result': '调用结果',
  'Status': '状态',
  'Running': '运行中',
  'Idle': '空闲',
  'Connected': '已连接',
  'Disconnected': '未连接',
  'World info': '世界信息',
  'Scan saves': '扫描存档',
  'No saves found. Create a world in-game, then scan again.': '没有找到存档。先在游戏里建一个世界，再重新扫描。',
  'Results appear here': '结果会显示在这里',

  // ---------- 插件 / 联机 / 引导 ----------
  'Plugins': '插件',
  'Multiplayer': '联机',
  'Tools': '工具箱',
  'Toolbox': '工具箱',
  'Capabilities': '能力',
  'Permissions': '权限',
  'Reload': '重新加载',
  'Enable': '启用',
  'Disable': '禁用',
  'Install example': '安装示例插件',
  'Loading…': '加载中…',
  'Back': '返回',
  'Next': '下一步',
  'Skip': '跳过',
  'Finish': '完成',
  'Welcome': '欢迎',
  // ---------- 工具页 / 动态片段 ----------
  'Type a command prefix (for example': '先输入一段指令（例如',
  ') and the list below shows what can follow it. Click a candidate to append it.':
    '），下面会列出它能接什么；点候选项直接追加到后面。',
  'Current: Ctrl+Alt+': '当前：Ctrl+Alt+',
  'Current:': '当前：',
  'Common commands': '常用指令',
  'Command list': '指令列表',
  'Builder': '构建器',
  'Hotkeys': '快捷键',
  'Bound': '已绑定',
  'Save & apply': '保存并应用',
  'Copy': '复制',
  'Back': '返回',
  'Results': '搜索结果',
  'Can follow': '可以接',
  'No hotkey': '无热键',
  'Add': '添加',
  // ---------- 工具页内置指令预设 ----------
  'Switch to Creative': '切换为创造模式',
  'Also accepts survival / adventure / spectator': '也可换成 survival（生存）/ adventure（冒险）/ spectator（旁观）',
  'Set time to day': '时间设为白天',
  'day / noon / night / midnight, or a raw tick number': 'day / noon（正午）/ night（夜晚）/ midnight（午夜），也可以直接填 tick 数字',
  'Set weather to clear': '天气设为晴天',
  'clear / rain / thunder, optionally followed by seconds': 'clear（晴）/ rain（下雨）/ thunder（雷雨），后面可跟持续秒数',
  'Teleport to (0, 100, 0)': '传送到坐标 (0, 100, 0)',
  'Replace @s with a player name to move someone else; coordinates accept ~':
    '把 @s 换成玩家名可以传送别人；坐标支持 ~ 相对坐标',
  'Set spawn to your position': '把当前位置设为重生点',
  'Without coordinates it uses where you stand; sleeping in a bed also moves spawn':
    '不写坐标就用你当前站的位置；换床睡觉也能改重生点',
  'Give yourself 64 diamonds': '给自己 64 个钻石',
  'Item IDs need the minecraft: namespace; max stack is 64': '物品 ID 必须带 minecraft: 命名空间，数量上限 64',
  'Regeneration III for 10s': '10 秒 3 级生命恢复',
  'Syntax: /effect give <target> <effect> [seconds] [amplifier] [hideParticles]':
    '语法：/effect give <目标> <效果> [秒数] [等级-1] [隐藏粒子]',
  'Keep inventory on death': '死亡不掉落物品',
  'Stored in world rules and persists across restarts; false turns it off':
    '存到世界规则里，重启游戏依然生效；false 为关闭',
  'Freeze the day cycle': '关闭昼夜循环',
  'Time stops where it is; true resumes the cycle': '时间会停在当前时刻；true 恢复流动',
  'Clear your inventory': '清空自己的背包',
  'Clears @s only; pass a player name to clear someone else': '只清 @s（自己）；写玩家名可清别人',
  'Kill non-player entities within 10 blocks': '清除 10 格内的非玩家实体',
  'type=!player excludes players; distance=..10 means within 10 blocks':
    'type=!player 排除玩家，distance=..10 表示 10 格以内',
  'Enchant held item with Sharpness V': '主手物品附魔锋利 V',
  'Level is capped by the item (Sharpness V max); you must hold it':
    '等级受物品限制（锋利上限 V）；必须手持对应物品',
  'Player': '玩家',
  'World': '世界',
  'Movement': '移动',
  'Items': '物品',
  'Status': '状态',
  'Rules': '规则',
  'Entities': '实体',
  'Favorites (custom)': '常用指令（自定义）',
  'Ctrl + Alt + number': 'Ctrl + Alt + 数字',
  'Palette hotkey Ctrl + Alt +': '速查窗唤出键 Ctrl + Alt +',
  'With the launcher in the background and the game focused, press':
    '启动器在后台、游戏在前台时，按',
  'to copy that command; switch to the game, press T and paste with Ctrl+V.':
    '可复制对应指令；切回游戏按 T 打开聊天框、Ctrl+V 粘贴。',
  'Running games': '运行中的游戏',
  'End': '结束',
  'external': '外部启动',
  'Game log will stream here after launch.': '启动游戏后，游戏日志会在这里滚动显示。',
  'LittleSkin library is live': 'LittleSkin 皮肤库已上线',
  '(Results appear here)': '（结果会显示在这里）',
  'MC2 · World data': 'MC2 · 世界数据',
  'Event stream': '事件流',
  'MLC events appear here after launch': '启动后 MLC 事件会显示在这里',
  'mlc.launch': '启动游戏',
};

/** 动态文案：数字 + 名词，用正则处理 */
const PATTERNS: [RegExp, (match: RegExpMatchArray) => string][] = [
  [/^(\d+) items$/, (m) => `${m[1]} 项`],
  [/^Common commands \((\d+)\)$/, (m) => `常用指令（${m[1]}）`],
  [/^Results \((\d+)\)$/, (m) => `搜索结果（${m[1]}）`],
  [/^(\d+) instances$/, (m) => `${m[1]} 个实例`],
  [/^(\d+) versions$/, (m) => `${m[1]} 个版本`],
  [/^(\d+) worlds$/, (m) => `${m[1]} 个世界`],
  [/^(\d+) files$/, (m) => `${m[1]} 个文件`],
  [/^(\d+) mods$/, (m) => `${m[1]} 个模组`],
  [/^(\d+) saves$/, (m) => `${m[1]} 个存档`],
  [/^(.*) · external$/, (m) => `${m[1]} · 外部启动`],
];

function dynamicZh(text: string): string | undefined {
  for (const [pattern, render] of PATTERNS) {
    const match = text.match(pattern);
    if (match) return render(match);
  }
  return undefined;
}

const TRANSLATED_ATTRS = ['placeholder', 'title', 'aria-label'] as const;
const SKIP = '.mono, pre, code, .activity, [data-no-i18n]';

/** 原文记录：文本节点 → 英文原串；元素 → 属性原文 */
const textOriginal = new Map<Text, string>();
const attrOriginal = new Map<Element, Record<string, string>>();

let lang: Lang = 'en';
let observer: MutationObserver | null = null;
let scheduled = false;

function shouldSkip(node: Node): boolean {
  const parent = node.parentElement;
  if (!parent) return true;
  const tag = parent.tagName.toLowerCase();
  if (tag === 'script' || tag === 'style') return true;
  return Boolean(parent.closest(SKIP));
}

function translateTextNode(node: Text): void {
  if (shouldSkip(node)) return;
  const raw = node.textContent ?? '';
  const trimmed = raw.trim();
  if (!trimmed) return;

  if (lang === 'zh') {
    const stored = textOriginal.get(node);
    const source = stored ?? trimmed;
    const hit = ZH[source] ?? ZH[source.replace(/\s+/g, ' ')] ?? dynamicZh(source);
    if (!hit) return;
    if (!stored) textOriginal.set(node, raw);
    if (trimmed !== hit) {
      node.textContent = raw.replace(trimmed, hit);
    }
    return;
  }

  const stored = textOriginal.get(node);
  if (stored !== undefined) {
    if (node.textContent !== stored) node.textContent = stored;
    textOriginal.delete(node);
  }
}

function translateAttrs(el: Element): void {
  if (el.closest(SKIP)) return;
  for (const attr of TRANSLATED_ATTRS) {
    const value = el.getAttribute(attr);
    if (!value) continue;
    if (lang === 'zh') {
      const hit = ZH[value.trim()];
      if (!hit || value === hit) continue;
      let store = attrOriginal.get(el);
      if (!store) {
        store = {};
        attrOriginal.set(el, store);
      }
      if (!(attr in store)) store[attr] = value;
      el.setAttribute(attr, hit);
    } else {
      const store = attrOriginal.get(el);
      if (store && attr in store) {
        el.setAttribute(attr, store[attr]);
        delete store[attr];
      }
    }
  }
}

function walk(root: Node): void {
  if (root.nodeType === Node.TEXT_NODE) {
    translateTextNode(root as Text);
    return;
  }
  if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_FRAGMENT_NODE) return;

  const element = root as Element;
  if (element.nodeType === Node.ELEMENT_NODE) translateAttrs(element);

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  let node = walker.nextNode();
  while (node) {
    if (node.nodeType === Node.TEXT_NODE) translateTextNode(node as Text);
    else translateAttrs(node as Element);
    node = walker.nextNode();
  }
}

function scheduleReapply(_node: Node): void {
  if (scheduled) return;
  scheduled = true;
  window.requestAnimationFrame(() => {
    scheduled = false;
    // 全量重扫：React 可能整块替换文本，盯住新增节点会漏
    if (sweepRoot) walk(sweepRoot);
  });
}

let sweepRoot: HTMLElement | null = null;
let sweepTimer = 0;
let sweepTicks = 0;

function startSweep(root: HTMLElement): void {
  sweepRoot = root;
  sweepTicks = 0;
  if (sweepTimer) return;
  sweepTimer = window.setInterval(() => {
    if (!sweepRoot) return;
    walk(sweepRoot);
    sweepTicks += 1;
    // 只在切换语言后的几秒内高频补扫，之后交给 MutationObserver
    if (sweepTicks > 20) {
      window.clearInterval(sweepTimer);
      sweepTimer = 0;
    }
  }, 400);
}

function stopSweep(): void {
  if (sweepTimer) window.clearInterval(sweepTimer);
  sweepTimer = 0;
  sweepTicks = 0;
}

export function applyLangOverlay(root: HTMLElement | null, next?: Lang): void {
  if (!root) return;
  if (next) lang = next;
  walk(root);

  if (lang === 'zh') {
    sweepRoot = root;
    startSweep(root);
  } else {
    stopSweep();
    sweepRoot = root;
  }

  if (lang === 'zh' && !observer) {
    observer = new MutationObserver((records) => {
      for (const record of records) {
        if (record.type === 'childList') {
          record.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.TEXT_NODE) {
              scheduleReapply(node);
            }
          });
        } else if (record.type === 'characterData' && record.target.nodeType === Node.TEXT_NODE) {
          scheduleReapply(record.target);
        }
      }
    });
    observer.observe(root, { childList: true, subtree: true, characterData: true });
  }

  if (lang === 'en' && observer) {
    observer.disconnect();
    observer = null;
  }
}

/** 供预览/自检脚本调用 */
declare global {
  interface Window {
    __veinApplyLang?: (next: Lang) => void;
  }
}

export function installLangBridge(root: HTMLElement | null): void {
  if (!root) return;
  lang = currentLang() === 'zh' ? 'zh' : 'en';
  applyLangOverlay(root);
  window.__veinApplyLang = (next: Lang) => applyLangOverlay(root, next);
}

export { ZH as ZH_UI };
