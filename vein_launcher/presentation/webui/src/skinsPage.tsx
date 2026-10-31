import React, { useEffect, useMemo, useState } from 'react';
import { rpc } from './bridge';
import { Empty, LayuiCheckbox, LayuiProgress } from './ui';
import type { AccountInfo } from './types';

interface SkinState {
  has: boolean;
  model?: string;
  source?: string;
  data_url?: string;
  size?: [number, number];
  updated_at?: number;
}

interface SkinRow extends AccountInfo {
  skin: SkinState;
}

export function SkinsPage({ notify }: { notify: (text: string) => void }) {
  const [rows, setRows] = useState<SkinRow[]>([]);
  const [activeId, setActiveId] = useState('');
  const [model, setModel] = useState<'classic' | 'slim'>('classic');
  const [reloadKey, setReloadKey] = useState(0);
  const [busy, setBusy] = useState('');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [remote, setRemote] = useState<{ url: string; data_url: string; model: string } | null>(null);

  const load = () =>
    rpc<SkinRow[]>('skins.list')
      .then((list) => {
        setRows(list);
        setActiveId((prev) => (prev && list.some((r) => r.id === prev) ? prev : list[0]?.id ?? ''));
      })
      .catch(() => setRows([]));

  useEffect(() => {
    load();
  }, [reloadKey]);

  const active = useMemo(() => rows.find((r) => r.id === activeId) ?? null, [rows, activeId]);

  useEffect(() => {
    if (!active) return;
    setModel(active.skin.model === 'slim' ? 'slim' : 'classic');
    setRemote(null);
    setMessage('');
  }, [activeId, active?.skin.model, active?.skin.has]);

  const preview = remote?.data_url || active?.skin.data_url || '';

  const importSkin = async () => {
    if (!active) return;
    setBusy('import');
    setProgress(15);
    setMessage('');
    try {
      const picked = await rpc<{ path: string }>('app.pickFile', [
        'Select a skin',
        'PNG image (*.png)',
      ]);
      setProgress(45);
      if (!picked.path) {
        setProgress(0);
        return;
      }
      await rpc('skins.import', [active.id, picked.path, model]);
      setProgress(100);
      setMessage('Skin saved locally.');
      setRemote(null);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setMessage((err as Error).message);
      notify('Skin import failed');
    } finally {
      setBusy('');
      window.setTimeout(() => setProgress(0), 900);
    }
  };

  const clearSkin = async () => {
    if (!active) return;
    setBusy('clear');
    setMessage('');
    try {
      await rpc('skins.clear', [active.id]);
      setRemote(null);
      setMessage('Skin removed.');
      setReloadKey((k) => k + 1);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy('');
    }
  };

  const fetchRemote = async () => {
    if (!active) return;
    setBusy('remote');
    setProgress(20);
    setMessage('');
    try {
      const result = await rpc<{ ok: boolean; error?: string; url?: string; data_url?: string; model?: string }>(
        'skins.remote',
        [active.id]
      );
      setProgress(90);
      if (!result.ok) {
        setMessage(result.error || 'No skin found on LittleSkin');
        return;
      }
      setRemote({
        url: result.url || '',
        data_url: result.data_url || '',
        model: result.model || 'classic',
      });
      setModel(result.model === 'slim' ? 'slim' : 'classic');
      setMessage('Loaded the skin currently set on LittleSkin.');
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy('');
      setProgress(100);
      window.setTimeout(() => setProgress(0), 700);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h1>Skins</h1>
        <span className="muted">Import a PNG or read the skin from LittleSkin</span>
      </div>

      {rows.length === 0 ? (
        <Empty>
          No accounts yet. Add one in Settings → Accounts, then come back to pick a skin.
        </Empty>
      ) : (
        <div className="skin-layout">
          <aside className="skin-accounts">
            {rows.map((row) => (
              <button
                key={row.id}
                className={`skin-account ${row.id === activeId ? 'active' : ''}`}
                onClick={() => setActiveId(row.id)}
              >
                <span className={`badge ${row.type === 'microsoft' ? 'accent' : ''}`}>
                  {row.type === 'microsoft' ? 'MS' : row.type === 'littleskin' ? 'LS' : 'OFF'}
                </span>
                <b>{row.username}</b>
                <em>{row.skin.has ? 'skin set' : 'no skin'}</em>
              </button>
            ))}
          </aside>

          <section className="skin-main">
            <div className="skin-preview">
              {preview ? (
                <>
                  <div className="skin-head">
                    <div className="skin-head-layer base" style={headStyle(preview, 8)} />
                    <div className="skin-head-layer hat" style={headStyle(preview, 40)} />
                  </div>
                  <img className="skin-texture" src={preview} alt="skin texture" />
                  <div className="skin-meta">
                    <b>{active?.username}</b>
                    <span>
                      {remote
                        ? 'LittleSkin skin (read only)'
                        : active?.skin.has
                          ? `Local · ${active.skin.size ? `${active.skin.size[0]}×${active.skin.size[1]}` : 'PNG'} · ${
                              active.skin.model === 'slim' ? 'Slim' : 'Classic'
                            }`
                          : 'Default skin'}
                    </span>
                  </div>
                </>
              ) : (
                <div className="skin-empty">
                  <i className="layui-icon layui-icon-picture" />
                  <span>No skin preview yet</span>
                </div>
              )}
            </div>

            <div className="skin-controls">
              <div className="skin-row">
                <span>Slim arms</span>
                <LayuiCheckbox
                  checked={model === 'slim'}
                  onChange={(next) => setModel(next ? 'slim' : 'classic')}
                  label={model === 'slim' ? 'Slim (3px arms)' : 'Classic (4px arms)'}
                />
              </div>

              {progress > 0 && <LayuiProgress percent={progress} />}

              <div className="row-actions">
                <button className="btn primary" disabled={Boolean(busy)} onClick={importSkin}>
                  <i className="layui-icon layui-icon-upload-drag" /> Import PNG
                </button>
                {active?.type === 'littleskin' && (
                  <button className="btn" disabled={Boolean(busy)} onClick={fetchRemote}>
                    <i className="layui-icon layui-icon-refresh" /> Load from LittleSkin
                  </button>
                )}
                {active?.skin.has && (
                  <button className="btn" disabled={Boolean(busy)} onClick={clearSkin}>
                    Remove
                  </button>
                )}
              </div>

              {message && <p className="muted">{message}</p>}

              <p className="muted skin-note">
                Offline and Microsoft accounts: the launcher stores the skin and shows the preview.
                Minecraft only renders custom skins through a skin mod (CustomSkinLoader) or a
                LittleSkin account launched with authlib-injector.
                {active?.type === 'littleskin' && (
                  <>
                    {' '}
                    To change the LittleSkin skin itself, use{' '}
                    <button
                      className="link-btn"
                      onClick={() => rpc('app.openUrl', ['https://littleskin.cn/user/closet'])}
                    >
                      littleskin.cn closet
                    </button>
                    .
                  </>
                )}
              </p>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function headStyle(dataUrl: string, x: number): React.CSSProperties {
  // 64×64 皮肤里头部在 (8,8)，帽子层在 (40,8)；用 800% 放大把 8×8 铺满 96px 方块
  const offsetX = -(x * 100) / 8;
  return {
    backgroundImage: `url(${dataUrl})`,
    backgroundSize: '800% 800%',
    backgroundPosition: `${offsetX}% -100%`,
  };
}
