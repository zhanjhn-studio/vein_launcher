import React, { useCallback, useEffect, useState } from 'react';
import { rpc } from './bridge';

interface AccountUser {
  id: number;
  username: string;
  email?: string;
  avatar?: string;
  status: string;
  group: { key: string; name: string; can_post: boolean; is_admin: boolean };
}

export function AccountPage({ notify }: { notify: (text: string) => void }) {
  const [user, setUser] = useState<AccountUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [login, setLogin] = useState<{ token: string; url: string; status: string } | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await rpc<{ loggedIn: boolean; user?: AccountUser }>('account.status', []);
      setUser(res?.loggedIn && res.user ? res.user : null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!login || login.status !== 'pending') return;
    const timer = window.setInterval(async () => {
      try {
        const res = await rpc<{ status: string; user?: AccountUser }>('account.poll', []);
        if (res.status === 'verified' && res.user) {
          setUser(res.user);
          setLogin(null);
          window.dispatchEvent(new CustomEvent('vein:accountChanged'));
          notify(`已登录：${res.user.username}`);
        } else if (['expired', 'consumed', 'error'].includes(res.status)) {
          setLogin((prev) => (prev ? { ...prev, status: res.status } : prev));
        }
      } catch {
        /* ignore */
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [login, notify]);

  const startLogin = async () => {
    try {
      const res = await rpc<{ token: string; url: string }>('account.start', []);
      setLogin({ token: res.token, url: res.url, status: 'pending' });
      await rpc('app.openUrl', [res.url]).catch(() => {});
    } catch (err) {
      notify(`登录初始化失败：${(err as Error).message}`);
    }
  };

  const logout = async () => {
    await rpc('account.logout', []).catch(() => {});
    setUser(null);
    window.dispatchEvent(new CustomEvent('vein:accountChanged'));
    notify('已退出 ZHANJHN 账号');
  };

  const open = (url: string) => rpc('app.openUrl', [url]).catch((err) => notify(`打开失败：${(err as Error).message}`));

  if (loading) {
    return (
      <div className="page fp-page">
        <div className="fp-loading"><span className="fp-spinner" /> 读取账号…</div>
      </div>
    );
  }

  return (
    <div className="page fp-page">
      <header className="fp-hero">
        <div>
          <h1>我的</h1>
          <p>ZHANJHN 统一账号 · 登录后可关联 Vein Launcher 等项目</p>
        </div>
      </header>

      {!user ? (
        <div className="ac-card">
          <div className="ac-hero">
            <div className="fp-avatar" style={{ width: 56, height: 56, fontSize: 22 }}>Z</div>
            <div>
              <b>未登录</b>
              <p>登录 ZHANJHN 统一账号，授权后请求会自动携带 token。</p>
            </div>
          </div>
          <button className="btn primary" onClick={startLogin}>登录 / 注册 ZHANJHN</button>
          <button className="btn" onClick={() => open('https://account.zhanjhn.cn/')}>打开账号中心</button>
        </div>
      ) : (
        <div className="ac-card">
          <div className="ac-hero">
            <div className="fp-avatar" style={{ width: 56, height: 56, fontSize: 22 }}>{user.avatar ? <img src={user.avatar} alt="" style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }} /> : user.username.slice(0, 1).toUpperCase()}</div>
            <div>
              <b>{user.username}</b>
              <p>
                <span className="fp-tag">{user.group.name}</span>
                <span style={{ marginLeft: 8 }}>{user.status === 'banned' ? '封禁（只读）' : '正常'}</span>
              </p>
            </div>
            <button className="btn sm ghost" style={{ marginLeft: 'auto' }} onClick={logout}>退出</button>
          </div>
          <div className="ac-grid">
            <div className="ac-item"><span>权限组</span><b>{user.group.name}</b></div>
            <div className="ac-item"><span>发帖权限</span><b>{user.group.can_post && user.status !== 'banned' ? '允许' : '只读'}</b></div>
            <div className="ac-item"><span>账号状态</span><b>{user.status === 'banned' ? '封禁' : '正常'}</b></div>
            <div className="ac-item"><span>管理后台</span><b>{user.group.is_admin ? '可访问' : '—'}</b></div>
          </div>
          <div className="ac-actions">
            <button className="btn primary" onClick={() => open('https://account.zhanjhn.cn/veinlauncher/')}>启动器仪表盘</button>
            <button className="btn" onClick={() => open('https://account.zhanjhn.cn/')}>账号中心 / 绑定设备</button>
            <button className="btn" onClick={startLogin}>关联新项目</button>
          </div>
          <p className="muted">token 已在所有请求中自动携带；远程指令可在仪表盘下发。</p>
        </div>
      )}

      {login && (
        <div className="fp-modal" onClick={(e) => { if (e.target === e.currentTarget) setLogin(null); }}>
          <div className="fp-modal-card">
            <h2>登录 / 关联 ZHANJHN</h2>
            <p className="muted">浏览器已打开统一认证页；登录后确认「关联 Vein Launcher」。</p>
            <code className="fp-token">{login.token}</code>
            <div className="fp-modal-actions">
              <button className="btn sm" onClick={() => navigator.clipboard?.writeText(login.token)}>复制 token</button>
              <button className="btn sm primary" onClick={() => rpc('app.openUrl', [login.url]).catch(() => {})}>重新打开授权页</button>
              <button className="btn sm ghost" onClick={() => setLogin(null)}>取消</button>
            </div>
            <div className="fp-modal-status">
              {login.status === 'pending' ? <><span className="fp-spinner small" /> 等待授权…</> : <span className="fp-error">token 已失效，请重新登录</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
