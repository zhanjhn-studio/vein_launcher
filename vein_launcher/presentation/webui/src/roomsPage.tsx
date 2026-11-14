import React, { useCallback, useEffect, useState } from 'react';
import { rpc } from './bridge';

interface Room {
  room_no: string;
  name: string;
  version: string;
  host: string;
  players: number;
  max_players: number;
  created_at?: string;
}

interface AccountUser {
  username: string;
  group: { name: string; can_post: boolean };
}

export function RoomsPage({ notify }: { notify: (text: string) => void }) {
  const [account, setAccount] = useState<{ user: AccountUser } | null>(null);
  const [login, setLogin] = useState<{ token: string; url: string; status: string } | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [versions, setVersions] = useState<string[]>([]);
  const [version, setVersion] = useState('');
  const [port, setPort] = useState('25565');
  const [publicRoom, setPublicRoom] = useState(true);
  const [postToForum, setPostToForum] = useState(true);
  const [password, setPassword] = useState('');
  const [maxPlayers, setMaxPlayers] = useState('8');
  const [hostIp, setHostIp] = useState('');
  const [myRoom, setMyRoom] = useState<{ room_no: string; host: string } | null>(null);
  const [joinCode, setJoinCode] = useState('');
  const [joinPass, setJoinPass] = useState('');
  const [joined, setJoined] = useState<{ room_no: string; host: string } | null>(null);
  const [busy, setBusy] = useState('');

  const refreshAccount = useCallback(async () => {
    try {
      const res = await rpc<{ loggedIn: boolean; user?: AccountUser }>('account.status', []);
      setAccount(res?.loggedIn && res.user ? { user: res.user } : null);
    } catch {
      setAccount(null);
    }
  }, []);

  const loadRooms = useCallback(async () => {
    try {
      setRooms(await rpc<Room[]>('rooms.list', []));
    } catch (err) {
      notify(`房间列表加载失败：${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    refreshAccount();
    loadRooms();
    rpc<Array<{ id: string }>>('versions.info', [])
      .then((list) => {
        const ids = (list || []).map((v) => v.id);
        setVersions(ids);
        if (ids.length) setVersion(ids[0]);
      })
      .catch(() => {});
    rpc<{ ip?: string }>('app.localIp', []).then((r) => setHostIp(r?.ip || '')).catch(() => {});
  }, [refreshAccount, loadRooms]);

  useEffect(() => {
    if (!joined) return;
    const timer = window.setInterval(async () => {
      try {
        const info = await rpc<{ status?: string; players?: number }>('rooms.info', [joined.room_no]);
        if (info.status && info.status !== 'open') {
          setJoined(null);
          notify('房间已关闭');
        }
      } catch {
        setJoined(null);
        notify('房间已关闭或过期');
      }
    }, 15000);
    return () => window.clearInterval(timer);
  }, [joined, notify]);

  useEffect(() => {
    if (!login || login.status !== 'pending') return;
    const timer = window.setInterval(async () => {
      try {
        const res = await rpc<{ status: string; user?: AccountUser }>('account.poll', []);
        if (res.status === 'verified' && res.user) {
          setAccount({ user: res.user });
          setLogin(null);
          window.dispatchEvent(new CustomEvent('vein:accountChanged'));
          notify(`已登录：${res.user.username}`);
          loadRooms();
        } else if (['expired', 'consumed', 'error'].includes(res.status)) {
          setLogin((prev) => (prev ? { ...prev, status: res.status } : prev));
        }
      } catch {
        /* ignore */
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [login, notify, loadRooms]);

  const startLogin = async () => {
    try {
      const res = await rpc<{ token: string; url: string }>('account.start', []);
      setLogin({ token: res.token, url: res.url, status: 'pending' });
      await rpc('app.openUrl', [res.url]).catch((err) => notify(`打开授权页失败：${(err as Error).message}`));
    } catch (err) {
      notify(`登录失败：${(err as Error).message}`);
    }
  };

  const host = `${hostIp || '127.0.0.1'}:${port || '25565'}`;

  const create = async () => {
    if (!account) { startLogin(); return; }
    setBusy('create');
    try {
      const res = await rpc<{ room_no: string; host: string }>('rooms.create', [
        `${account.user.username} 的房间`,
        version,
        host,
        password,
        publicRoom,
        Number(maxPlayers) || 8,
      ]);
      setMyRoom({ room_no: res.room_no, host: res.host });
      notify(`房间已创建：${res.room_no}`);
      if (postToForum) {
        try {
          await rpc('forum.post', [
            `[联机] ${account.user.username} 的房间`,
            `房间号：${res.room_no}\n版本：${version || '任意'}\n地址：${res.host}\n公开：${publicRoom ? '是' : '否'}\n\n在启动器「联机」页输入房间号加入。`,
            ['闲聊'],
            '',
          ]);
          notify('已同步发到广场');
        } catch (err) {
          notify(`房间已建，但发帖失败：${(err as Error).message}`);
        }
      }
      await loadRooms();
    } catch (err) {
      notify(`创建失败：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const join = async (code: string, pass = '') => {
    if (!account) { startLogin(); return; }
    setBusy('join');
    try {
      const res = await rpc<{ room_no: string; host: string }>('rooms.join', [code, pass]);
      setJoined({ room_no: res.room_no, host: res.host });
      notify(`已加入房间 ${res.room_no}`);
    } catch (err) {
      notify(`加入失败：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const close = async () => {
    if (!myRoom) return;
    try {
      await rpc('rooms.close', [myRoom.room_no]);
      setMyRoom(null);
      notify('房间已关闭');
      loadRooms();
    } catch (err) {
      notify(`关闭失败：${(err as Error).message}`);
    }
  };

  return (
    <div className="page fp-page">
      <header className="fp-hero">
        <div>
          <h1>联机</h1>
          <p>一键开房：生成房间号，把房间号 + 密码发给朋友即可。联机流量直连房主（局域网/端口映射）。</p>
        </div>
        <div className="fp-actions">
          {account ? (
            <span className="fp-user"><span className="fp-avatar sm">{account.user.username.slice(0, 1).toUpperCase()}</span><b>{account.user.username}</b></span>
          ) : (
            <button className="btn" onClick={startLogin}>登录 ZHANJHN</button>
          )}
          <button className="btn" onClick={loadRooms}>刷新</button>
        </div>
      </header>

      {!account && (
        <div className="fp-banner">
          <b>登录后可开房</b>
          <span>房间号/密码会保存在 ZHANJHN 账号下，朋友无需账号也能加入。</span>
          <button className="btn sm" onClick={startLogin}>登录 / 注册</button>
        </div>
      )}

      <div className="rm-grid">
        <section className="rm-card">
          <h2>一键开房</h2>
          <p className="muted">游戏里先「对局域网开放」，端口填在下面；地址会自动带上本机内网 IP。</p>
          <label className="rm-field">版本
            <select value={version} onChange={(e) => setVersion(e.target.value)}>
              {versions.length === 0 && <option value="">（先安装版本）</option>}
              {versions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>
          <div className="rm-row">
            <label className="rm-field">端口<input value={port} onChange={(e) => setPort(e.target.value)} placeholder="25565" /></label>
            <label className="rm-field">人数上限<input value={maxPlayers} onChange={(e) => setMaxPlayers(e.target.value)} /></label>
          </div>
          <label className="rm-field">房间密码（可选）<input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="不填则公开" /></label>
          <label className="rm-check"><input type="checkbox" checked={publicRoom} onChange={(e) => setPublicRoom(e.target.checked)} /> 公开房间（出现在列表）</label>
          <label className="rm-check"><input type="checkbox" checked={postToForum} onChange={(e) => setPostToForum(e.target.checked)} /> 同步发到广场（房间号会公开）</label>
          <div className="rm-host">地址：<code>{host}</code></div>
          <button className="btn primary" disabled={busy === 'create' || !account} onClick={create}>
            {busy === 'create' ? '创建中…' : '创建房间'}
          </button>
          {myRoom && (
            <div className="rm-mine">
              <div>房间号 <b className="rm-code">{myRoom.room_no}</b></div>
              <div className="muted">地址：{myRoom.host}</div>
              <div className="rm-row">
                <button className="btn sm" onClick={() => navigator.clipboard?.writeText(`${myRoom.room_no} ${myRoom.host}`)}>复制</button>
                <button className="btn sm" onClick={close}>关闭房间</button>
              </div>
            </div>
          )}
        </section>

        <section className="rm-card">
          <h2>加入房间</h2>
          <p className="muted">输入房间号；私密房间需要密码。</p>
          <div className="rm-row">
            <label className="rm-field">房间号<input value={joinCode} onChange={(e) => setJoinCode(e.target.value)} maxLength={6} placeholder="6 位数字" /></label>
            <label className="rm-field">密码<input value={joinPass} onChange={(e) => setJoinPass(e.target.value)} /></label>
          </div>
          <button className="btn primary" disabled={busy === 'join' || !account} onClick={() => join(joinCode, joinPass)}>
            {busy === 'join' ? '加入中…' : '加入'}
          </button>
          {joined && (
            <div className="rm-mine">
              <div>已加入 <b>{joined.room_no}</b></div>
              <div>服务器地址：<code>{joined.host}</code></div>
              <div className="rm-row">
                <button className="btn sm" onClick={() => navigator.clipboard?.writeText(joined.host)}>复制地址</button>
                <button className="btn sm" onClick={async () => {
                  try { await rpc('rooms.leave', [joined.room_no]); } catch { /* ignore */ }
                  setJoined(null);
                  notify('已离开房间');
                }}>离开房间</button>
              </div>
              <p className="muted">在 Minecraft「多人游戏 → 直接连接」粘贴地址。</p>
            </div>
          )}

          <h2 style={{ marginTop: 18 }}>公开房间</h2>
          {loading ? <div className="fp-loading"><span className="fp-spinner" /> 加载中…</div> : rooms.length === 0 ? (
            <div className="empty">还没有公开房间</div>
          ) : (
            <div className="rm-list">
              {rooms.map((r) => (
                <div className="rm-item" key={r.room_no}>
                  <div>
                    <b>{r.name}</b>
                    <div className="muted">{r.version || '任意版本'} · {r.players}/{r.max_players} 人 · 房间号 {r.room_no}</div>
                  </div>
                  <button className="btn sm" onClick={() => join(r.room_no)}>加入</button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {login && (
        <div className="fp-modal" onClick={(e) => { if (e.target === e.currentTarget) setLogin(null); }}>
          <div className="fp-modal-card">
            <h2>登录 / 授权</h2>
            <p className="muted">浏览器已打开授权页；完成后自动登录。</p>
            <code className="fp-token">{login.token}</code>
            <div className="fp-modal-actions">
              <button className="btn sm primary" onClick={() => rpc('app.openUrl', [login.url]).catch(() => {})}>打开授权页</button>
              <button className="btn sm ghost" onClick={() => setLogin(null)}>取消</button>
            </div>
            <div className="fp-modal-status">
              {login.status === 'pending' ? <><span className="fp-spinner small" /> 等待授权…</> : <span className="fp-error">token 已失效</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
