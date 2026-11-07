import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import { currentLang, t } from './i18n';
import {
  displayHint,
  groupLabel,
  lookupCandidates,
  normalizeCommand,
  searchCandidates,
} from './commandTree';
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
    tag: 'Player',
    title: 'Switch to Creative',
    desc: 'Also accepts survival / adventure / spectator',
    cmd: '/gamemode creative',
  },
  {
    slot: 2,
    tag: 'World',
    title: 'Set time to day',
    desc: 'day / noon / night / midnight, or a raw tick number',
    cmd: '/time set day',
  },
  {
    slot: 3,
    tag: 'World',
    title: 'Set weather to clear',
    desc: 'clear / rain / thunder, optionally followed by seconds',
    cmd: '/weather clear',
  },
  {
    slot: 4,
    tag: 'Movement',
    title: 'Teleport to (0, 100, 0)',
    desc: 'Replace @s with a player name to move someone else; coordinates accept ~',
    cmd: '/tp @s 0 100 0',
  },
  {
    slot: 5,
    tag: 'Movement',
    title: 'Set spawn to your position',
    desc: 'Without coordinates it uses where you stand; sleeping in a bed also moves spawn',
    cmd: '/spawnpoint @s',
  },
  {
    slot: 6,
    tag: 'Items',
    title: 'Give yourself 64 diamonds',
    desc: 'Item IDs need the minecraft: namespace; max stack is 64',
    cmd: '/give @s minecraft:diamond 64',
  },
  {
    slot: 7,
    tag: 'Status',
    title: 'Regeneration III for 10s',
    desc: 'Syntax: /effect give <target> <effect> [seconds] [amplifier] [hideParticles]',
    cmd: '/effect give @s minecraft:regeneration 10 2',
  },
  {
    slot: 8,
    tag: 'Rules',
    title: 'Keep inventory on death',
    desc: 'Stored in world rules and persists across restarts; false turns it off',
    cmd: '/gamerule keepInventory true',
  },
  {
    slot: 9,
    tag: 'Rules',
    title: 'Freeze the day cycle',
    desc: 'Time stops where it is; true resumes the cycle',
    cmd: '/gamerule doDaylightCycle false',
  },
  {
    slot: 0,
    tag: 'Items',
    title: 'Clear your inventory',
    desc: 'Clears @s only; pass a player name to clear someone else',
    cmd: '/clear @s',
  },
  {
    slot: null,
    tag: 'Entities',
    title: 'Kill non-player entities within 10 blocks',
    desc: 'type=!player excludes players; distance=..10 means within 10 blocks',
    cmd: '/kill @e[type=!player,distance=..10]',
  },
  {
    slot: null,
    tag: 'Items',
    title: 'Enchant held item with Sharpness V',
    desc: 'Level is capped by the item (Sharpness V max); you must hold it',
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
      <span className="card-toggle-hint">{hint ?? (open ? 'Collapse' : 'Expand')}</span>
    </div>
  );
}

export function ToolsPage({ notify }: { notify: (text: string) => void }) {
  // 整个「指令」区块默认收起，点标题展开
  const lang = currentLang();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const [binding, setBinding] = useState<BindResult | null>(null);
  const [error, setError] = useState('');

  // 自定义常用指令 + 小窗热键
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [paletteKey, setPaletteKey] = useState('Q');
  const [saving, setSaving] = useState(false);
  const [agent, setAgent] = useState<{ ok?: boolean; inGame?: boolean } | null>(null);
  const [running, setRunning] = useState(false);
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
        notify(`Copied Ctrl+Alt+${d.slot}: ${d.title || d.text}`);
      }),
    [notify],
  );

  const copy = async (item: Command) => {
    try {
      await rpc('tools.copy', [item.cmd]);
      notify(`Copied: ${item.cmd}`);
    } catch (e) {
      notify((e as Error).message);
    }
  };

  // MLC：把指令直接发进游戏
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const state = await rpc<{ ok?: boolean; inGame?: boolean }>('mlc.agentState', [0]);
        if (alive) setAgent(state);
      } catch {
        if (alive) setAgent({ ok: false });
      }
    };
    tick();
    const timer = window.setInterval(tick, 5000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  const runCommand = async (raw: string) => {
    const cmd = raw.trim();
    if (!cmd) return;
    setRunning(true);
    try {
      const payload = cmd.startsWith('/') ? cmd : `/${cmd}`;
      await rpc('mlc.agentChat', [payload, 0]);
      notify(`Sent to game: ${payload}`);
    } catch (err) {
      notify(`MLC not available: ${(err as Error).message}`);
    } finally {
      setRunning(false);
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
      notify('Favorites saved');
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------- 指令Builder
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
      notify(`Copied: ${fullCommand}`);
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
          title="Commands"
          open={open}
          onToggle={() => setOpen((v) => !v)}
          hint={open ? 'Collapse' : 'Expand'}
        />
        {open && (
          <>
        <div className="tool-section">
        <div className="tool-section-title">Builder</div>
        <p className="muted">
          Type a command prefix (for example <code className="mono">kill</code>) and the list below shows what can follow it. Click a candidate to append it.
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
          <button
            className="btn sm primary"
            onClick={() => runCommand(fullCommand)}
            disabled={!normalizeCommand(draft) || running || agent?.ok === false}
            title={agent?.ok === false ? 'MLC agent offline — launch a vanilla instance first' : 'Send this command to the running game'}
          >
            Send to game
          </button>
          <button className="btn sm ghost" onClick={undo} disabled={!history.length}>
            Back
          </button>
          <button
            className="btn sm ghost"
            onClick={() => {
              setHistory([]);
              setDraft('');
            }}
            disabled={!draft && !history.length}
          >
            Clear
          </button>
        </div>

        <div className="cmd-current">
          <code className="mono">{normalizeCommand(draft) ? fullCommand : '/…'}</code>
          {normalizeCommand(draft) && candidates === null && (
            <span className="cmd-badge">Command complete — copy it</span>
          )}
          <span className="cmd-badge">
            {t(`MLC ${agent?.ok === false ? 'offline' : agent?.inGame ? 'in game' : 'connected'}`)}
          </span>
        </div>

        <div className="cmd-search">
          <input
            className="input"
            value={query}
            spellCheck={false}
            placeholder="Search commands or items: sword / kill / diamond"
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button className="btn sm ghost" onClick={() => setQuery('')}>
              Clear
            </button>
          )}
        </div>

        {query.trim() ? (
          searchResults.length === 0 ? (
            <p className="muted">No commands or items match “{query}”.</p>
          ) : (
            <>
              <div className="cmd-hint">Results ({searchResults.length})</div>
              <div className="cmd-options">
                {searchResults.map((r) => (
                  <button
                    key={`${r.parent}|${r.token}|${displayHint(r, lang)}`}
                    className="cmd-option search"
                    onClick={() => applyResult(r)}
                  >
                    <code className="mono">
                      {r.parent ? <em>{r.parent} </em> : null}
                      {r.token}
                    </code>
                    <span>{displayHint(r, lang)}</span>
                  </button>
                ))}
              </div>
            </>
          )
        ) : candidates === null ? (
          <p className="muted">No more candidates: the command is complete, or it needs manual arguments (names, coordinates).</p>
        ) : candidates.length === 0 ? (
          <p className="muted">This command is complete — copy it and paste it in game.</p>
        ) : (
          <>
            <div className="cmd-hint">
              {normalizeCommand(draft) ? 'Can follow' : 'Common commands'}（{candidates.length}）
            </div>
            <div className="cmd-options">
              {groupCandidates(candidates).map(([group, items], gi) => (
                <React.Fragment key={`${group}-${gi}`}>
                  {group && <div className="cmd-group">{groupLabel(group, lang)}</div>}
                  {items.map((c) => (
                    <button
                      key={`${c.token}-${displayHint(c, lang)}`}
                      className="cmd-option"
                      onClick={() => append(c.token)}
                    >
                      <code className="mono">{c.token}</code>
                      <span>{displayHint(c, lang)}</span>
                    </button>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </>
        )}
        </div>

        <div className="tool-section">
        <div className="tool-section-title">Hotkeys</div>
        <p className="muted">
          With the launcher in the background and the game focused, press <b>Ctrl + Alt + number</b>{' '}
          to copy that command; switch to the game, press T and paste with Ctrl+V.
        </p>
        <p className="muted" style={{ marginTop: 8 }}>
          Bound <b>{bound.size} / {hotkeyItems.length}</b>
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
          These commands need cheats enabled or OP. On a server, follow the server's rules.
        </p>

        <div className="cmd-input-row" style={{ marginTop: 12 }}>
          <span className="muted">Palette hotkey Ctrl + Alt +</span>
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
            Current: Ctrl+Alt+{binding?.paletteKey || paletteKey}
            {binding?.paletteKey ? ' ✓ registered' : ''}
          </span>
        </div>

        <div style={{ marginTop: 18 }}>
          <CardHead
            title="Favorites (custom)"
            open={openFav}
            onToggle={() => setOpenFav((v) => !v)}
            hint={openFav ? 'Collapse' : `${favorites.length} items`}
          />
        </div>
        {openFav && (
          <>
        {favorites.length === 0 && (
          <p className="muted">No custom commands yet. Use “Add” below to create one.</p>
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
              <option value="">No hotkey</option>
              {SLOT_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  Ctrl+Alt+{s}
                </option>
              ))}
            </select>
            <input
              className="input fav-title"
              value={f.title}
              placeholder="Name (e.g. Home)"
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
              Delete
            </button>
          </div>
        ))}
        <div className="row-actions" style={{ marginTop: 10 }}>
          <button className="btn sm" onClick={addFavorite}>
            + Add
          </button>
          <button className="btn sm primary" onClick={saveConfig} disabled={saving}>
            {saving ? 'Saving…' : 'Save & apply'}
          </button>
          {!loaded && <span className="muted">Loading config…</span>}
        </div>
          </>
        )}
        </div>

        <div className="tool-section">
        <div className="tool-section-title">Command list</div>
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
          {visible.length === 0 && <div className="empty">No matching commands</div>}
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
                className="btn sm primary"
                disabled={agent?.ok === false || running}
                onClick={(e) => {
                  e.stopPropagation();
                  runCommand(item.cmd);
                }}
              >
                Run
              </button>
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
