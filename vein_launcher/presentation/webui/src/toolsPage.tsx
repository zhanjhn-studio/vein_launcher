import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import { t } from './i18n';
import { lookupCandidates, normalizeCommand, searchCandidates } from './commandTree';
import type { Candidate, IndexedCandidate } from './commandTree';

/** 把候选按 group 字段切成连续分组（没有 group 的归到空标题下） */
function groupCandidates(list: Candidate[]): [string, Candidate[]][] {
  const out: [string, Candidate[]][] = [];
  for (const item of list) {
    const key = item.group ?? '';
    const last = out[out.length - 1];
    if (last && last[0] === key) last[1].push(item);
    else out.push([key, [item]]);
  }
  return out;
}

/** 一条内置指令：slot 为全局热键槽位（Ctrl+Alt+<slot>），null 表示没有热键 */
interface Command {
  slot: number | null;
  title: string;
  desc: string;
  tag: string;
  cmd: string;
}

/** 内置指令表：均为 Java 版 1.13+ 语法，需要世界开启作弊（或拥有 OP 权限） */
const COMMANDS: Command[] = [
  {
    slot: 1,
    tag: '玩家',
    title: '切换为创造模式',
    desc: '也可换成 survival（生存）/ adventure（冒险）/ spectator（旁观）',
    cmd: '/gamemode creative',
  },
  {
    slot: 2,
    tag: '世界',
    title: '时间设为白天',
    desc: 'day / noon(正午) / night(夜晚) / midnight(午夜)，也可以直接填 tick 数字',
    cmd: '/time set day',
  },
  {
    slot: 3,
    tag: '世界',
    title: '天气设为晴天',
    desc: 'clear（晴）/ rain（下雨）/ thunder（雷雨），后面可跟持续秒数',
    cmd: '/weather clear',
  },
  {
    slot: 4,
    tag: '移动',
    title: '传送到坐标 (0, 100, 0)',
    desc: '把 @s 换成玩家名可以传送别人；坐标支持 ~ 相对坐标',
    cmd: '/tp @s 0 100 0',
  },
  {
    slot: 5,
    tag: '移动',
    title: '把当前位置设为重生点',
    desc: '不写坐标就用你当前站的位置；换床睡觉也能改重生点',
    cmd: '/spawnpoint @s',
  },
  {
    slot: 6,
    tag: '物品',
    title: '给自己 64 个钻石',
    desc: '物品 ID 必须带 minecraft: 命名空间，数量上限 64',
    cmd: '/give @s minecraft:diamond 64',
  },
  {
    slot: 7,
    tag: '状态',
    title: '10 秒 3 级生命恢复',
    desc: '语法：/effect give <目标> <效果> [秒数] [等级-1] [隐藏粒子]',
    cmd: '/effect give @s minecraft:regeneration 10 2',
  },
  {
    slot: 8,
    tag: '规则',
    title: '死亡不掉落物品',
    desc: '存到世界规则里，重启游戏依然生效；false 为关闭',
    cmd: '/gamerule keepInventory true',
  },
  {
    slot: 9,
    tag: '规则',
    title: '关闭昼夜循环',
    desc: '时间会停在当前时刻；true 恢复流动',
    cmd: '/gamerule doDaylightCycle false',
  },
  {
    slot: 0,
    tag: '物品',
    title: '清空自己的背包',
    desc: '只清 @s（自己）；写玩家名可清别人',
    cmd: '/clear @s',
  },
  {
    slot: null,
    tag: '实体',
    title: '清除 10 格内的非玩家实体',
    desc: 'type=!player 排除玩家，distance=..10 表示 10 格以内',
    cmd: '/kill @e[type=!player,distance=..10]',
  },
  {
    slot: null,
    tag: '物品',
    title: '主手物品附魔锋利 V',
    desc: '等级受物品限制（锋利上限 V）；必须手持对应物品',
    cmd: '/enchant @s minecraft:sharpness 5',
  },
];

interface BindResult {
  ok: boolean;
  bound?: number[];
  failed?: { slot: number; error: string }[];
  error?: string;
  paletteKey?: string;
}

/** 自定义常用指令 */
interface Favorite {
  id: string;
  title: string;
  cmd: string;
  slot: number | null;
}

interface ToolsConfig {
  favorites: Favorite[];
  paletteKey: string;
}

/** 小窗热键可选的键（和 Python 端 PALETTE_KEYS 保持一致） */
const PALETTE_KEYS = [
  ...'QWERTYUIOPASDFGHJKLZXCVBNM'.split(''),
  ...Array.from({ length: 12 }, (_, i) => `F${i + 1}`),
];

const SLOT_OPTIONS = Array.from({ length: 10 }, (_, i) => i);

interface HotkeyEvent {
  slot: number;
  text: string;
  title: string;
}

/** 可收起的卡片标题：点标题任意位置展开/收起 */
function CardHead({
  title,
  open,
  onToggle,
  hint,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  hint?: string;
}) {
  return (
    <div
      className="card-title card-toggle"
      role="button"
      tabIndex={0}
      aria-expanded={open}
      onClick={onToggle}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onToggle();
        }
      }}
    >
      <span className={`card-caret ${open ? 'open' : ''}`}>▸</span>
      <span>{title}</span>
      <span className="card-toggle-hint">{hint ?? (open ? '收起' : '展开')}</span>
    </div>
  );
}

export function ToolsPage({ notify }: { notify: (text: string) => void }) {
  // 整个「指令」区块默认收起，点标题展开
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const [binding, setBinding] = useState<BindResult | null>(null);
  const [error, setError] = useState('');

  // 自定义常用指令 + 小窗热键
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [paletteKey, setPaletteKey] = useState('Q');
  const [saving, setSaving] = useState(false);
  const [openFav, setOpenFav] = useState(false);
  const [loaded, setLoaded] = useState(false);

  /** 自定义指令占用的槽位优先，内置指令让位 */
  const hotkeyItems = useMemo(() => {
    const taken = new Set(favorites.map((f) => f.slot).filter((s) => s !== null));
    return [
      ...favorites
        .filter((f) => f.slot !== null)
        .map((f) => ({ slot: f.slot as number, text: f.cmd, title: f.title })),
      ...COMMANDS.filter((c) => c.slot !== null && !taken.has(c.slot)).map((c) => ({
        slot: c.slot as number,
        text: c.cmd,
        title: c.title,
      })),
    ];
  }, [favorites]);

  const bindHotkeys = useCallback(
    async (entries: typeof hotkeyItems, key: string) => {
      try {
        const result = await rpc<BindResult>('tools.bindHotkeys', [entries, key]);
        setBinding(result);
        setError('');
      } catch (e) {
        setError((e as Error).message);
      }
    },
    [],
  );

  // 启动时读配置 → 注册热键
  useEffect(() => {
    rpc<ToolsConfig>('tools.config')
      .then((cfg) => {
        const favs = Array.isArray(cfg?.favorites) ? cfg.favorites : [];
        const key = cfg?.paletteKey || 'Q';
        setFavorites(favs);
        setPaletteKey(key);
        setLoaded(true);
        const taken = new Set(favs.map((f) => f.slot).filter((s) => s !== null));
        const entries = [
          ...favs
            .filter((f) => f.slot !== null)
            .map((f) => ({ slot: f.slot as number, text: f.cmd, title: f.title })),
          ...COMMANDS.filter((c) => c.slot !== null && !taken.has(c.slot)).map((c) => ({
            slot: c.slot as number,
            text: c.cmd,
            title: c.title,
          })),
        ];
        bindHotkeys(entries, key).catch(() => {});
      })
      .catch((e: Error) => {
        setError(e.message);
        setLoaded(true);
      });
  }, [bindHotkeys]);

  // 热键在游戏里按下时，Python 会推过来一条事件
  useEffect(
    () =>
      on<HotkeyEvent>('vein:hotkey', (d) => {
        notify(`已复制 Ctrl+Alt+${d.slot}：${d.title || d.text}`);
      }),
    [notify],
  );

  const copy = async (item: Command) => {
    try {
      await rpc('tools.copy', [item.cmd]);
      notify(`已复制：${item.cmd}`);
    } catch (e) {
      notify((e as Error).message);
    }
  };

  // ---------------------------------------------------------------- 常用指令编辑
  const addFavorite = () => {
    setFavorites((list) => [
      ...list,
      { id: `fav-${Date.now()}`, title: '', cmd: '', slot: null },
    ]);
  };

  const updateFavorite = (id: string, patch: Partial<Favorite>) => {
    setFavorites((list) => list.map((f) => (f.id === id ? { ...f, ...patch } : f)));
  };

  const removeFavorite = (id: string) => {
    setFavorites((list) => list.filter((f) => f.id !== id));
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const rows = favorites
        .map((f) => ({ ...f, cmd: f.cmd.trim(), title: f.title.trim() }))
        .filter((f) => f.cmd);
      const result = await rpc<{ ok: boolean; config: ToolsConfig }>('tools.saveConfig', [
        rows,
        paletteKey,
      ]);
      const saved = result?.config ?? { favorites: rows, paletteKey };
      setFavorites(saved.favorites ?? []);
      setPaletteKey(saved.paletteKey ?? paletteKey);
      await bindHotkeys(
        [
          ...(saved.favorites ?? [])
            .filter((f) => f.slot !== null)
            .map((f) => ({ slot: f.slot as number, text: f.cmd, title: f.title })),
          ...COMMANDS.filter(
            (c) =>
              c.slot !== null &&
              !(saved.favorites ?? []).some((f) => f.slot === c.slot),
          ).map((c) => ({ slot: c.slot as number, text: c.cmd, title: c.title })),
        ],
        saved.paletteKey ?? paletteKey,
      );
      notify('常用指令已保存');
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------- 指令构建器
  const [draft, setDraft] = useState('');
  const [query, setQuery] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const candidates = lookupCandidates(draft);
  const searchResults = useMemo(() => searchCandidates(query), [query]);
  const fullCommand = `/${normalizeCommand(draft)}`;

  const append = (token: string) => {
    const base = normalizeCommand(draft);
    const next = [base, token].filter(Boolean).join(' ');
    setHistory((h) => [...h, draft]);
    setDraft(next);
  };

  /** 中文检索结果：把父级路径 + token 拼成完整指令 */
  const applyResult = (r: IndexedCandidate) => {
    setHistory((h) => [...h, draft]);
    setDraft([r.parent, r.token].filter(Boolean).join(' '));
    setQuery('');
  };

  const undo = () => {
    setHistory((h) => {
      if (!h.length) return h;
      setDraft(h[h.length - 1]);
      return h.slice(0, -1);
    });
  };

  const copyDraft = async () => {
    try {
      await rpc('tools.copy', [fullCommand]);
      notify(`已复制：${fullCommand}`);
    } catch (e) {
      notify((e as Error).message);
    }
  };

  const keyword = filter.trim().toLowerCase();
  const visible = keyword
    ? COMMANDS.filter(
        (c) =>
          c.title.toLowerCase().includes(keyword) ||
          c.desc.toLowerCase().includes(keyword) ||
          c.cmd.toLowerCase().includes(keyword) ||
          c.tag.toLowerCase().includes(keyword),
      )
    : COMMANDS;

  const bound = new Set(binding?.bound ?? []);
  const failed = binding?.failed ?? [];

  return (
    <div className="page">
      <div className="page-head">
        <h1>{t('Tools')}</h1>
        <span className="muted">{t('In-game commands')}</span>
      </div>

      <div className="card">
        <CardHead
          title="指令"
          open={open}
          onToggle={() => setOpen((v) => !v)}
          hint={open ? '收起' : '展开'}
        />
        {open && (
          <>
        <div className="tool-section">
        <div className="tool-section-title">构建器</div>
        <p className="muted">
          先输入一段指令（比如 <code className="mono">kill</code>），下面会列出它能接什么；点候选项直接追加到后面。
        </p>

        <div className="cmd-input-row">
          <span className="cmd-slash">/</span>
          <input
            className="input cmd-input"
            value={draft}
            spellCheck={false}
            placeholder="kill / gamemode / give …"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') copyDraft();
            }}
          />
          <button className="btn sm" onClick={copyDraft} disabled={!normalizeCommand(draft)}>
            {t('Copy')}
          </button>
          <button className="btn sm ghost" onClick={undo} disabled={!history.length}>
            回退
          </button>
          <button
            className="btn sm ghost"
            onClick={() => {
              setHistory([]);
              setDraft('');
            }}
            disabled={!draft && !history.length}
          >
            清空
          </button>
        </div>

        <div className="cmd-current">
          <code className="mono">{normalizeCommand(draft) ? fullCommand : '/…'}</code>
          {normalizeCommand(draft) && candidates === null && (
            <span className="cmd-badge">指令已完整，可直接复制</span>
          )}
        </div>

        <div className="cmd-search">
          <input
            className="input"
            value={query}
            spellCheck={false}
            placeholder="搜索指令或物品：中文（钻石 / 苹果 / 杀）或英文（sword / kill）"
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button className="btn sm ghost" onClick={() => setQuery('')}>
              清除
            </button>
          )}
        </div>

        {query.trim() ? (
          searchResults.length === 0 ? (
            <p className="muted">没有匹配「{query}」的指令或物品。</p>
          ) : (
            <>
              <div className="cmd-hint">搜索结果（{searchResults.length}）</div>
              <div className="cmd-options">
                {searchResults.map((r) => (
                  <button
                    key={`${r.parent}|${r.token}|${r.hint}`}
                    className="cmd-option search"
                    onClick={() => applyResult(r)}
                  >
                    <code className="mono">
                      {r.parent ? <em>{r.parent} </em> : null}
                      {r.token}
                    </code>
                    <span>{r.hint}</span>
                  </button>
                ))}
              </div>
            </>
          )
        ) : candidates === null ? (
          <p className="muted">没有更多候选：这条指令已经完整，或者需要手动填参数（名字、坐标等）。</p>
        ) : candidates.length === 0 ? (
          <p className="muted">这条指令已经完整，复制后回游戏粘贴即可。</p>
        ) : (
          <>
            <div className="cmd-hint">
              {normalizeCommand(draft) ? '后面可以接' : '常用指令'}（{candidates.length}）
            </div>
            <div className="cmd-options">
              {groupCandidates(candidates).map(([group, items], gi) => (
                <React.Fragment key={`${group}-${gi}`}>
                  {group && <div className="cmd-group">{group}</div>}
                  {items.map((c) => (
                    <button
                      key={`${c.token}-${c.hint}`}
                      className="cmd-option"
                      onClick={() => append(c.token)}
                    >
                      <code className="mono">{c.token}</code>
                      <span>{c.hint}</span>
                    </button>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </>
        )}
        </div>

        <div className="tool-section">
        <div className="tool-section-title">快捷键</div>
        <p className="muted">
          启动器缩到后台、游戏窗口在前台时，按 <b>Ctrl + Alt + 数字</b>{' '}
          会把对应指令复制到剪贴板，切回游戏按 T 打开聊天框、Ctrl+V 粘贴即可。
        </p>
        <p className="muted" style={{ marginTop: 8 }}>
          已绑定 <b>{bound.size} / {hotkeyItems.length}</b>
          {bound.size > 0
            ? ` · Ctrl+Alt+${[...bound].sort((a, b) => a - b).join(' / ')}`
            : ''}
        </p>
        {failed.length > 0 && (
          <p className="tool-warn">
            {failed.map((f) => `Ctrl+Alt+${f.slot} ${f.error}`).join('；')}
          </p>
        )}
        {error && <p className="tool-warn">{error}</p>}
        <p className="muted">
          这些指令需要世界开启「允许作弊」或拥有 OP 权限；在服务器里请按服务器的规则使用。
        </p>

        <div className="cmd-input-row" style={{ marginTop: 12 }}>
          <span className="muted">小窗唤出键 Ctrl + Alt +</span>
          <select
            className="input"
            value={paletteKey}
            style={{ width: 96 }}
            onChange={(e) => setPaletteKey(e.target.value)}
          >
            {PALETTE_KEYS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
          <span className="muted">
            当前：Ctrl+Alt+{binding?.paletteKey || paletteKey}
            {binding?.paletteKey ? ' ✓ 已注册' : ''}
          </span>
        </div>

        <div style={{ marginTop: 18 }}>
          <CardHead
            title="常用指令（自定义）"
            open={openFav}
            onToggle={() => setOpenFav((v) => !v)}
            hint={openFav ? '收起' : `${favorites.length} 条`}
          />
        </div>
        {openFav && (
          <>
        {favorites.length === 0 && (
          <p className="muted">还没有自定义指令。点下面「添加」写一条自己的指令。</p>
        )}
        {favorites.map((f) => (
          <div className="fav-row" key={f.id}>
            <select
              className="input fav-slot"
              value={f.slot === null ? '' : String(f.slot)}
              onChange={(e) =>
                updateFavorite(f.id, {
                  slot: e.target.value === '' ? null : Number(e.target.value),
                })
              }
            >
              <option value="">无热键</option>
              {SLOT_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  Ctrl+Alt+{s}
                </option>
              ))}
            </select>
            <input
              className="input fav-title"
              value={f.title}
              placeholder="名称（例如：回城）"
              onChange={(e) => updateFavorite(f.id, { title: e.target.value })}
            />
            <input
              className="input fav-cmd mono"
              value={f.cmd}
              placeholder="/tp 0 100 0"
              spellCheck={false}
              onChange={(e) => updateFavorite(f.id, { cmd: e.target.value })}
            />
            <button className="btn sm ghost" onClick={() => removeFavorite(f.id)}>
              删除
            </button>
          </div>
        ))}
        <div className="row-actions" style={{ marginTop: 10 }}>
          <button className="btn sm" onClick={addFavorite}>
            + 添加
          </button>
          <button className="btn sm primary" onClick={saveConfig} disabled={saving}>
            {saving ? '保存中…' : '保存并应用'}
          </button>
          {!loaded && <span className="muted">读取配置中…</span>}
        </div>
          </>
        )}
        </div>

        <div className="tool-section">
        <div className="tool-section-title">指令列表</div>
        <div className="dl-search" style={{ marginTop: 8 }}>
          <input
            className="input"
            value={filter}
            placeholder={t('Search by name / command')}
            onChange={(e) => setFilter(e.target.value)}
          />
          <span className="muted" style={{ alignSelf: 'center' }}>
            {visible.length} / {COMMANDS.length}
          </span>
        </div>

        <div style={{ marginTop: 10 }}>
          {visible.length === 0 && <div className="empty">没有匹配的指令</div>}
          {visible.map((item, index) => (
            <div
              key={`${item.cmd}-${index}`}
              className="tool-row"
              role="button"
              tabIndex={0}
              onClick={() => copy(item)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  copy(item);
                }
              }}
            >
              <span className={`tool-hk ${item.slot !== null && bound.has(item.slot) ? 'on' : ''}`}>
                {item.slot === null ? '—' : `Ctrl+Alt+${item.slot}`}
              </span>
              <div className="tool-main">
                <div className="tool-title">
                  {item.title}
                  <span className="tool-tag">{item.tag}</span>
                </div>
                <div className="tool-desc">{item.desc}</div>
                <code className="tool-cmd">{item.cmd}</code>
              </div>
              <button
                className="btn sm"
                onClick={(e) => {
                  e.stopPropagation();
                  copy(item);
                }}
              >
                {t('Copy')}
              </button>
            </div>
          ))}
        </div>
        </div>
          </>
        )}
      </div>
    </div>
  );
}
