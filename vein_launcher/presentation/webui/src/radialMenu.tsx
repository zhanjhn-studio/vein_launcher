import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface WheelItem {
  key: string;
  label: string;
  iconImg: string;
}

const SECTOR = 45; // 8 等分
const RADIUS = 148;
const BALL = 56;
const DRAG_THRESHOLD = 4;
const HOLD_MS = 200;
const DEAD_ZONE = 30;

/**
 * 指南针悬浮球 + 3D 轮盘
 *
 * 手势（右键）：
 *   1. 在球上按住右键 → 200ms 后轮盘以球心为中心弹出（3D 倾斜透视展开）
 *   2. 按住右键拖到某个扇形 → 该扇形高亮
 *   3. 松开右键 → 执行该扇区
 *   移动球：按住右键后先移动超过 4px 即判定为拖动（不会呼出轮盘）
 *
 * 左键短按：打开「常驻」轮盘（点扇区选、点空白/Esc 收起）
 */
export function RadialMenu({
  items,
  page,
  onPick,
  open,
  onOpenChange,
}: {
  items: WheelItem[];
  page: string;
  onPick: (key: string) => void;
  open: boolean;
  onOpenChange: (next: boolean) => void;
}) {
  const [hovered, setHovered] = useState<string | null>(null);
  const [holding, setHolding] = useState(false);
  const [ball, setBall] = useState<{ x: number; y: number }>(() => {
    try {
      const raw = localStorage.getItem('vl.ball');
      if (raw) {
        const parsed = JSON.parse(raw) as { x?: number; y?: number };
        if (typeof parsed.x === 'number' && typeof parsed.y === 'number') {
          return { x: parsed.x, y: parsed.y };
        }
      }
    } catch {
      /* 忽略 */
    }
    return { x: 96, y: Math.max(120, (window.innerHeight || 720) - 120) };
  });
  const [dragging, setDragging] = useState(false);
  const [viewport, setViewport] = useState({
    w: typeof window !== 'undefined' ? window.innerWidth : 1200,
    h: typeof window !== 'undefined' ? window.innerHeight : 800,
  });

  const drag = useRef<{ dx: number; dy: number; moved: boolean; id: number } | null>(null);
  const latest = useRef(ball);
  const timer = useRef<number | null>(null);
  const holdingRef = useRef(false);

  // 视口窄时轮盘要缩小，否则 296px 的圆放不下
  const radius = useMemo(() => {
    const min = Math.min(viewport.w, viewport.h);
    return Math.max(92, Math.min(RADIUS, Math.round(min * 0.42)));
  }, [viewport.w, viewport.h]);

  const size = radius * 2;

  // 轮盘必须完整落在窗口里。若球贴边，直接以球心为圆会被裁掉一块，
  // 所以「展开时把球挪到能完整放下的最近位置」——球与轮盘永远同心，不会错位。
  const safeCenter = useCallback(() => {
    const pad = radius + 8;
    return {
      x: Math.min(Math.max(ball.x, pad), Math.max(pad, viewport.w - pad)),
      y: Math.min(Math.max(ball.y, pad), Math.max(pad, viewport.h - pad)),
    };
  }, [ball.x, ball.y, radius, viewport.w, viewport.h]);

  const clearTimer = useCallback(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  }, []);

  useEffect(() => {
    const clamp = () => {
      setBall((prev) => {
        const next = {
          x: Math.min(Math.max(prev.x, BALL / 2), Math.max(BALL / 2, window.innerWidth - BALL / 2)),
          y: Math.min(Math.max(prev.y, BALL / 2), Math.max(BALL / 2, window.innerHeight - BALL / 2)),
        };
        if (next.x !== prev.x || next.y !== prev.y) {
          latest.current = next;
          try {
            localStorage.setItem('vl.ball', JSON.stringify(next));
          } catch {
            /* 忽略 */
          }
        }
        return next;
      });
    };
    clamp();
    const onResize = () => {
      clamp();
      setViewport({ w: window.innerWidth, h: window.innerHeight });
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onOpenChange(false);
        setHolding(false);
        holdingRef.current = false;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onOpenChange]);

  const sectors = useMemo(() => {
    const cx = radius;
    const cy = radius;
    // 按项目数量等分 360°，而不是固定 45°（否则项目不足 8 个时会留缺口、宽窄不一）
    const step = 360 / Math.max(1, items.length);
    return items.slice(0, 12).map((item, index) => {
      const start = -90 + step * index;
      const end = start + step;
      const mid = start + step / 2;
      const toXY = (deg: number) => {
        const rad = (deg * Math.PI) / 180;
        return { x: cx + Math.cos(rad) * radius, y: cy + Math.sin(rad) * radius };
      };
      const a = toXY(start);
      const b = toXY(end);
      const labelPos = {
        x: cx + Math.cos((mid * Math.PI) / 180) * radius * 0.64,
        y: cy + Math.sin((mid * Math.PI) / 180) * radius * 0.64,
      };
      return {
        item,
        index,
        mid,
        path: `M ${cx} ${cy} L ${a.x} ${a.y} A ${radius} ${radius} 0 0 1 ${b.x} ${b.y} Z`,
        labelPos,
        active: item.key === page,
      };
    });
  }, [items, page, radius]);

  const current = useMemo(
    () => items.find((item) => item.key === page) || items[0],
    [items, page]
  );

  // 指南针针尖：指向当前页（或悬停页）所在扇区
  const needleDeg = useMemo(() => {
    const key = hovered || current?.key;
    const hit = sectors.find((s) => s.item.key === key);
    if (!hit) return 0;
    return hit.mid + 90;
  }, [hovered, current, sectors]);

  const sectorAt = useCallback(
    (clientX: number, clientY: number): string | null => {
      const dx = clientX - latest.current.x;
      const dy = clientY - latest.current.y;
      if (Math.hypot(dx, dy) < DEAD_ZONE) return null;
      const deg = (Math.atan2(dy, dx) * 180) / Math.PI;
      const step = 360 / Math.max(1, items.length);
      const index = Math.floor(((deg + 90 + 360) % 360) / step) % items.length;
      return items[index]?.key ?? null;
    },
    [items]
  );

  useEffect(() => {
    if (!holding) return;
    const onMove = (event: PointerEvent) => setHovered(sectorAt(event.clientX, event.clientY));
    const onUp = (event: PointerEvent) => {
      const key = sectorAt(event.clientX, event.clientY);
      holdingRef.current = false;
      setHolding(false);
      setHovered(null);
      onOpenChange(false);
      if (key) onPick(key);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    };
  }, [holding, sectorAt, onPick, onOpenChange]);

  // 右键按下即挂 window 监听（不等 React 重渲染），拖出球体也不断线
  const beginRightDrag = useCallback(
    (event: React.PointerEvent<HTMLButtonElement>) => {
      const state = drag.current;
      if (!state) return;
      setDragging(true);

      const onMove = (ev: PointerEvent) => {
        const nx = ev.clientX - state.dx;
        const ny = ev.clientY - state.dy;
        if (!state.moved) {
          if (Math.hypot(nx - ball.x, ny - ball.y) < DRAG_THRESHOLD) return;
          state.moved = true;
        }
        const x = Math.min(Math.max(nx, BALL / 2), window.innerWidth - BALL / 2);
        const y = Math.min(Math.max(ny, BALL / 2), window.innerHeight - BALL / 2);
        latest.current = { x, y };
        setBall({ x, y });
      };

      const preventMenu = (ev: MouseEvent) => ev.preventDefault();

      const finish = () => {
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', finish);
        window.removeEventListener('pointercancel', finish);
        window.removeEventListener('contextmenu', preventMenu);
        drag.current = null;
        setDragging(false);
        if (state.moved) {
          try {
            localStorage.setItem('vl.ball', JSON.stringify(latest.current));
          } catch {
            /* 忽略 */
          }
        }
      };

      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', finish);
      window.addEventListener('pointercancel', finish);
      window.addEventListener('contextmenu', preventMenu);
      event.preventDefault();
    },
    [ball.x, ball.y]
  );

  const onPointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
    // 右键：拖动悬浮球；左键：长按呼出轮盘并按住选择
    if (event.button !== 0 && event.button !== 2) return;
    drag.current = {
      dx: event.clientX - ball.x,
      dy: event.clientY - ball.y,
      moved: false,
      id: event.pointerId,
    };

    if (event.button === 2) {
      beginRightDrag(event);
      return;
    }

    if (open) return;
    setDragging(false);

    clearTimer();
    timer.current = window.setTimeout(() => {
      timer.current = null;
      const center = safeCenter();
      if (center.x !== ball.x || center.y !== ball.y) {
        latest.current = center;
        setBall(center);
        try {
          localStorage.setItem('vl.ball', JSON.stringify(center));
        } catch {
          /* 忽略 */
        }
      }
      holdingRef.current = true;
      setHolding(true);
      onOpenChange(true);
      setHovered(sectorAt(center.x, center.y));
    }, HOLD_MS);
  };
  return (
    <>
      {open && (
        <>
          {!holding && <div className="wheel-dismiss" onClick={() => onOpenChange(false)} />}
          <div
            className={`pie ${holding ? 'holding' : ''}`}
            style={{
              left: ball.x,
              top: ball.y,
              width: size,
              height: size,
              marginLeft: -radius,
              marginTop: -radius,
            }}
          >
            <svg viewBox={`0 0 ${size} ${size}`} className="pie-svg" role="menu">
              {sectors.map(({ item, path, labelPos, active }) => {
                const isHover = hovered === item.key;
                return (
                  <g
                    key={item.key}
                    className={`pie-sector ${active ? 'is-active' : ''} ${isHover ? 'is-hover' : ''}`}
                    style={{
                      transformOrigin: `${radius}px ${radius}px`,
                      transform: isHover ? 'scale(1.14)' : 'scale(1)',
                    }}
                    onMouseEnter={() => {
                      if (!holding) setHovered(item.key);
                    }}
                    onMouseLeave={() => {
                      if (!holding) setHovered(null);
                    }}
                    onClick={() => {
                      if (holding) return;
                      onPick(item.key);
                      onOpenChange(false);
                    }}
                    role="menuitem"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        onPick(item.key);
                        onOpenChange(false);
                      }
                    }}
                  >
                    <path d={path} className="pie-slice" />
                    <image
                      href={`icons/${item.iconImg}`}
                      x={labelPos.x - 12}
                      y={labelPos.y - 20}
                      width={24}
                      height={24}
                      className="pie-icon"
                      style={{ pointerEvents: 'none' }}
                    />
                    <text
                      x={labelPos.x}
                      y={labelPos.y + 22}
                      className="pie-label"
                      textAnchor="middle"
                      style={{ pointerEvents: 'none' }}
                    >
                      {item.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </>
      )}

      <button
        type="button"
        className={`wheel-ball ${dragging ? 'dragging' : ''} ${open ? 'open' : ''} ${
          holding ? 'holding' : ''
        }`}
        style={{ left: ball.x, top: ball.y }}
        aria-expanded={open}
        aria-label={open ? '收起导航轮盘' : '右键长按呼出轮盘 · 右键拖动移动'}
        title={open ? '松开收起' : '右键长按呼出轮盘 · 右键拖动移动'}
        onContextMenu={(event) => event.preventDefault()}
        onPointerDown={onPointerDown}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onOpenChange(!open);
          }
        }}
      >
        <svg className="compass" viewBox="0 0 56 56" aria-hidden="true">
          <circle cx="28" cy="28" r="23" className="compass-face" />
          <circle cx="28" cy="28" r="17" className="compass-dial" />
          {[0, 90, 180, 270].map((deg) => (
            <line
              key={deg}
              x1="28"
              y1="7"
              x2="28"
              y2="11"
              className="compass-tick"
              transform={`rotate(${deg} 28 28)`}
            />
          ))}
          <g
            className="compass-needle"
            style={{ transform: `rotate(${needleDeg}deg)`, transformOrigin: '28px 28px' }}
          >
            <polygon points="28,11 32.5,28 28,33 23.5,28" className="needle-north" />
            <polygon points="28,45 23.5,28 28,23 32.5,28" className="needle-south" />
          </g>
          <circle cx="28" cy="28" r="2.6" className="compass-pin" />
        </svg>
      </button>
    </>
  );
}
