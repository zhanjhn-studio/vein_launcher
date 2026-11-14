import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { rpc } from './bridge';

interface ForumPost {
  id: number;
  title: string;
  excerpt: string;
  author_name: string;
  likes: number;
  tags: string[];
  created_at: string;
}

interface ForumDetail {
  id: number;
  title: string;
  content: string;
  author_name: string;
  likes: number;
  tags: string[];
  created_at: string;
}

interface ForumTag {
  name: string;
  count: number;
}

interface AccountUser {
  id: number;
  username: string;
  status: string;
  group: { name: string; key: string; can_post: boolean };
}

interface Feed {
  items: ForumPost[];
  total: number;
  has_more: boolean;
}

const AUTH_URL = 'https://account.zhanjhn.cn/';

function relTime(iso: string): string {
  const t = new Date(iso).getTime();
  if (!t) return '';
  const diff = (Date.now() - t) / 1000;
  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)} 天前`;
  return new Date(t).toLocaleDateString();
}

function initials(name: string): string {
  return (name || '?').trim().slice(0, 1).toUpperCase();
}

export function ForumPage({ notify }: { notify: (text: string) => void }) {
  const [sort, setSort] = useState<'hot' | 'new'>('hot');
  const [tag, setTag] = useState('');
  const [tags, setTags] = useState<ForumTag[]>([]);
  const [items, setItems] = useState<ForumPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<ForumDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [compose, setCompose] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [pickTag, setPickTag] = useState('');
  const [sending, setSending] = useState(false);
  const [account, setAccount] = useState<{ user: AccountUser } | null>(null);
  const [login, setLogin] = useState<{ token: string; url: string; status: string } | null>(null);

  const loadTags = useCallback(async () => {
    try {
      setTags(await rpc<ForumTag[]>('forum.tags', []));
    } catch {
      /* 标签失败不阻塞 */
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await rpc<Feed>('forum.feed', [sort, tag, 1]);
      setItems(data.items || []);
    } catch (err) {
      notify(`广场加载失败：${(err as Error).message}`);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [sort, tag, notify]);

  const refreshAccount = useCallback(async () => {
    try {
      const res = await rpc<{ loggedIn: boolean; user?: AccountUser }>('account.status', []);
      setAccount(res?.loggedIn && res.user ? { user: res.user } : null);
    } catch {
      setAccount(null);
    }
  }, []);

  useEffect(() => {
    loadTags();
    refreshAccount();
  }, [loadTags, refreshAccount]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!login || login.status !== 'pending') return;
    const timer = window.setInterval(async () => {
      try {
        const res = await rpc<{ status: string; user?: AccountUser }>('account.poll', []);
        if (res.status === 'verified' && res.user) {
          setAccount({ user: res.user });
          setLogin(null);
          notify(`已登录：${res.user.username}（${res.user.group.name}）`);
        } else if (['expired', 'consumed', 'error'].includes(res.status)) {
          setLogin((prev) => (prev ? { ...prev, status: res.status } : prev));
        }
      } catch {
        /* 忽略单次轮询失败 */
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
    setAccount(null);
    setDetail(null);
    setCompose(false);
    notify('已退出账号');
  };

  const openPost = async (id: number) => {
    setDetailLoading(true);
    setDetail(null);
    try {
      setDetail(await rpc<ForumDetail>('forum.detail', [id]));
    } catch (err) {
      notify(`帖子打开失败：${(err as Error).message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  const likePost = async (id: number) => {
    try {
      const res = await rpc<{ likes: number; liked: boolean }>('forum.like', [id]);
      setItems((prev) => prev.map((p) => (p.id === id ? { ...p, likes: res.likes } : p)));
      setDetail((prev) => (prev && prev.id === id ? { ...prev, likes: res.likes } : prev));
      if (res.liked) notify('已点赞');
    } catch (err) {
      notify(`点赞失败：${(err as Error).message}`);
    }
  };

  const publish = async () => {
    if (!account) {
      startLogin();
      return;
    }
    if (title.trim().length < 4) {
      notify('标题至少 4 个字');
      return;
    }
    if (content.trim().length < 2) {
      notify('正文至少 2 个字');
      return;
    }
    setSending(true);
    try {
      await rpc('forum.post', [title.trim(), content.trim(), pickTag ? [pickTag] : [], '']);
      setTitle('');
      setContent('');
      setCompose(false);
      setSort('new');
      await loadTags();
      await load();
      notify('发布成功');
    } catch (err) {
      notify(`发布失败：${(err as Error).message}`);
    } finally {
      setSending(false);
    }
  };

  const tagOptions = useMemo(() => tags.map((t) => t.name), [tags]);

  if (detailLoading) {
    return (
      <div className="page fp-page">
        <div className="fp-loading"><span className="fp-spinner" /> 正在加载帖子…</div>
      </div>
    );
  }

  if (detail) {
    return (
      <div className="page fp-page">
        <button className="btn sm ghost fp-back" onClick={() => setDetail(null)}>← 返回广场</button>
        <article className="fp-detail">
          <div className="fp-detail-head">
            <span className="fp-avatar">{initials(detail.author_name)}</span>
            <div>
              <div className="fp-author">{detail.author_name}</div>
              <div className="fp-time">{relTime(detail.created_at)}</div>
            </div>
            <div className="fp-detail-tags">
              {detail.tags.map((t) => <span className="fp-tag" key={t}>{t}</span>)}
            </div>
          </div>
          <h1>{detail.title}</h1>
          <div className="fp-content">{detail.content}</div>
          <div className="fp-detail-foot">
            <button className={`fp-like big ${detail.likes > 0 ? 'on' : ''}`} onClick={() => likePost(detail.id)}>
              <span className="fp-heart">♥</span> {detail.likes} 赞
            </button>
            <button className="btn sm" onClick={() => setDetail(null)}>返回</button>
          </div>
        </article>
      </div>
    );
  }

  return (
    <div className="page fp-page">
      <header className="fp-hero">
        <div>
          <h1>广场</h1>
          <p>发教程、求助、插件与作品；登录后即可发言。</p>
        </div>
        <div className="fp-actions">
          {account ? (
            <div className="fp-user">
              <span className="fp-avatar sm">{initials(account.user.username)}</span>
              <div>
                <b>{account.user.username}</b>
                <span className="fp-group">{account.user.group.name}</span>
              </div>
              <button className="btn sm ghost" onClick={logout}>退出</button>
            </div>
          ) : (
            <button className="btn" onClick={startLogin}>登录</button>
          )}
          <button className="btn primary" onClick={() => (account ? setCompose((v) => !v) : startLogin())}>
            发帖
          </button>
        </div>
      </header>

      {!account && (
        <div className="fp-banner">
          <b>登录后发帖</b>
          <span>使用 ZHANJHN 统一账号，绑定后可直接在这里发帖、点赞。</span>
          <button className="btn sm" onClick={startLogin}>登录 / 注册</button>
        </div>
      )}

      {account && compose && (
        <div className="fp-compose">
          <div className="fp-compose-head">
            <b>发布新帖</b>
            <button className="btn sm ghost" onClick={() => setCompose(false)}>取消</button>
          </div>
          <input
            className="input"
            placeholder="标题（4-120 字）"
            value={title}
            maxLength={120}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            className="input fp-textarea"
            placeholder="正文，支持纯文本 / Markdown 源"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="fp-compose-foot">
            <select value={pickTag} onChange={(e) => setPickTag(e.target.value)}>
              <option value="">不选标签</option>
              {tagOptions.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <span className="muted">以 {account.user.username} 身份发布</span>
            <button className="btn primary" disabled={sending} onClick={publish}>
              {sending ? '发布中…' : '发布'}
            </button>
          </div>
        </div>
      )}

      <div className="fp-toolbar">
        <div className="fp-seg">
          <button className={sort === 'hot' ? 'on' : ''} onClick={() => setSort('hot')}>热门</button>
          <button className={sort === 'new' ? 'on' : ''} onClick={() => setSort('new')}>最新</button>
        </div>
        <div className="fp-chips">
          <button className={`fp-chip ${tag === '' ? 'on' : ''}`} onClick={() => setTag('')}>全部</button>
          {tags.map((t) => (
            <button
              key={t.name}
              className={`fp-chip ${tag === t.name ? 'on' : ''}`}
              onClick={() => setTag(tag === t.name ? '' : t.name)}
            >
              {t.name}<i>{t.count}</i>
            </button>
          ))}
        </div>
        <button className="btn sm ghost" style={{ marginLeft: 'auto' }} onClick={load}>刷新</button>
      </div>

      {loading ? (
        <div className="fp-loading"><span className="fp-spinner" /> 加载中…</div>
      ) : items.length === 0 ? (
        <div className="fp-empty">
          <b>这里还很安静</b>
          <span>{account ? '点右上角「发帖」写第一条。' : '登录后发第一条帖子。'}</span>
          <button className="btn primary" onClick={() => (account ? setCompose(true) : startLogin())}>去发帖</button>
        </div>
      ) : (
        <div className="fp-list">
          {items.map((p) => (
            <article className="fp-post" key={p.id} onClick={() => openPost(p.id)}>
              <button
                className={`fp-like ${p.likes > 0 ? 'on' : ''}`}
                onClick={(e) => { e.stopPropagation(); likePost(p.id); }}
                title="点赞"
              >
                <span className="fp-heart">♥</span>
                <b>{p.likes}</b>
              </button>
              <div className="fp-body">
                <h3>{p.title}</h3>
                <p>{p.excerpt}</p>
                <div className="fp-meta">
                  <span className="fp-avatar sm">{initials(p.author_name)}</span>
                  <span>{p.author_name}</span>
                  <span className="fp-dot">·</span>
                  <span>{relTime(p.created_at)}</span>
                  <span className="fp-mini-tags">
                    {p.tags.map((t) => <span className="fp-tag" key={t}>{t}</span>)}
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {login && (
        <div className="fp-modal" onClick={(e) => { if (e.target === e.currentTarget) setLogin(null); }}>
          <div className="fp-modal-card">
            <h2>{login.status === 'pending' ? '登录 / 注册' : '授权失败'}</h2>
            <p className="muted">浏览器已打开统一认证页面；登录后点「同意并授权」。若没打开，点下面按钮。</p>
            <code className="fp-token">{login.token}</code>
            <div className="fp-modal-actions">
              <button className="btn sm" onClick={() => navigator.clipboard?.writeText(login.token)}>复制 token</button>
              <button className="btn sm primary" onClick={() => rpc('app.openUrl', [login.url]).catch(() => {})}>打开授权页</button>
              <button className="btn sm ghost" onClick={() => setLogin(null)}>取消</button>
            </div>
            <div className="fp-modal-status">
              {login.status === 'pending' && <><span className="fp-spinner small" /> 等待授权…（10 分钟内有效）</>}
              {login.status !== 'pending' && <span className="fp-error">token 已过期或被使用，请重新点「登录」</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
