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
  hot_score?: number;
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

interface Feed {
  items: ForumPost[];
  page: number;
  total: number;
  has_more: boolean;
}

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

export function ForumPage({ notify }: { notify: (text: string) => void }) {
  const [sort, setSort] = useState<'hot' | 'new'>('hot');
  const [tag, setTag] = useState('');
  const [tags, setTags] = useState<ForumTag[]>([]);
  const [items, setItems] = useState<ForumPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<ForumDetail | null>(null);
  const [compose, setCompose] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [pickTag, setPickTag] = useState('');
  const [author, setAuthor] = useState(() => localStorage.getItem('vl.forum.author') || '');
  const [sending, setSending] = useState(false);

  const loadTags = useCallback(async () => {
    try {
      setTags(await rpc<ForumTag[]>('forum.tags', []));
    } catch {
      /* 标签失败不阻塞列表 */
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

  useEffect(() => {
    loadTags();
  }, [loadTags]);

  useEffect(() => {
    load();
  }, [load]);

  const openPost = async (id: number) => {
    try {
      setDetail(await rpc<ForumDetail>('forum.detail', [id]));
    } catch (err) {
      notify(`帖子打开失败：${(err as Error).message}`);
    }
  };

  const send = async () => {
    if (!title.trim() || !content.trim()) {
      notify('标题和正文都要填');
      return;
    }
    setSending(true);
    try {
      const name = author.trim() || '匿名';
      await rpc('forum.post', [title.trim(), content.trim(), pickTag ? [pickTag] : [], name]);
      localStorage.setItem('vl.forum.author', name);
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

  const like = async () => {
    if (!detail) return;
    try {
      const res = await rpc<{ likes: number; liked: boolean }>('forum.like', [detail.id]);
      setDetail({ ...detail, likes: res.likes });
      setItems((prev) => prev.map((p) => (p.id === detail.id ? { ...p, likes: res.likes } : p)));
    } catch (err) {
      notify(`点赞失败：${(err as Error).message}`);
    }
  };

  const tagOptions = useMemo(() => tags.map((t) => t.name), [tags]);

  if (detail) {
    return (
      <div className="page forum-page">
        <div className="page-head">
          <h1>{detail.title}</h1>
          <span className="muted">
            {detail.author_name} · {relTime(detail.created_at)}
          </span>
        </div>
        <div className="forum-detail">
          <div className="forum-detail-tags">
            {detail.tags.map((t) => (
              <span className="forum-tag" key={t}>{t}</span>
            ))}
          </div>
          <div className="forum-content">{detail.content}</div>
          <div className="forum-actions">
            <button className="btn primary" onClick={like}>赞 {detail.likes}</button>
            <button className="btn" onClick={() => setDetail(null)}>返回列表</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page forum-page">
      <div className="page-head">
        <h1>广场</h1>
        <span className="muted">{items.length} 条 · 来自 api.zhanjhn.cn</span>
        <button className="btn primary" style={{ marginLeft: 'auto' }} onClick={() => setCompose((v) => !v)}>
          发帖
        </button>
      </div>

      {compose && (
        <div className="forum-compose">
          <div className="forum-compose-row">
            <input
              className="input"
              placeholder="昵称（1-20 字）"
              value={author}
              maxLength={20}
              onChange={(e) => setAuthor(e.target.value)}
            />
            <select value={pickTag} onChange={(e) => setPickTag(e.target.value)}>
              <option value="">不选标签</option>
              {tagOptions.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <input
            className="input"
            placeholder="标题（4-120 字）"
            value={title}
            maxLength={120}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            className="input forum-textarea"
            placeholder="正文，支持纯文本 / Markdown 源"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="forum-compose-actions">
            <button className="btn primary" disabled={sending} onClick={send}>
              {sending ? '发布中…' : '发布'}
            </button>
            <button className="btn" onClick={() => setCompose(false)}>取消</button>
          </div>
        </div>
      )}

      <div className="forum-toolbar">
        <button className={`btn sm ${sort === 'hot' ? 'primary' : ''}`} onClick={() => setSort('hot')}>热门</button>
        <button className={`btn sm ${sort === 'new' ? 'primary' : ''}`} onClick={() => setSort('new')}>最新</button>
        <div className="forum-tags">
          <button className={`forum-chip ${tag === '' ? 'on' : ''}`} onClick={() => setTag('')}>全部</button>
          {tags.map((t) => (
            <button
              key={t.name}
              className={`forum-chip ${tag === t.name ? 'on' : ''}`}
              onClick={() => setTag(tag === t.name ? '' : t.name)}
            >
              {t.name} <span>{t.count}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="forum-list">
        {loading && <div className="empty">加载中…</div>}
        {!loading && items.length === 0 && <div className="empty">还没有帖子，点右上角「发帖」写第一条。</div>}
        {items.map((p) => (
          <button className="forum-item" key={p.id} onClick={() => openPost(p.id)}>
            <span className="forum-likes"><b>{p.likes}</b>赞</span>
            <span className="forum-item-body">
              <b>{p.title}</b>
              <span className="forum-excerpt">{p.excerpt}</span>
              <span className="forum-meta">
                {p.tags.map((t) => <span className="forum-tag" key={t}>{t}</span>)}
                {p.author_name} · {relTime(p.created_at)}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
