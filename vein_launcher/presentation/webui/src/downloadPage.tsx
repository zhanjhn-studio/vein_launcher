import React, { useEffect, useMemo, useState } from 'react';
import { on, rpc } from './bridge';
import { RemoteIcon } from './ui';
import type { ModItem, VersionInfo } from './types';

type Category = 'version' | 'mod' | 'modpack' | 'datapack' | 'shader' | 'resourcepack' | 'optifine';

const CATEGORIES: { key: Category; label: string; desc: string; icon: string; project?: string }[] = [
  { key: 'version', label: '原版与加载器', desc: '安装游戏本体，可搭配 Fabric / Forge / Quilt / NeoForge', icon: 'grass_block.png' },
  { key: 'mod', label: '模组', desc: '来自 Modrinth，按游戏版本与加载器筛选', icon: 'crafting_table.png', project: 'mod' },
  { key: 'modpack', label: '整合包', desc: '完整整合包（.mrpack），自动装配', icon: 'chest.png', project: 'modpack' },
  { key: 'resourcepack', label: '资源包', desc: '材质与资源包', icon: 'writable_book.png', project: 'resourcepack' },
  { key: 'shader', label: '光影', desc: '适用于 Iris / OptiFine 的光影包', icon: 'spyglass.png', project: 'shader' },
  { key: 'datapack', label: '数据包', desc: '用于存档与服务器的数据包', icon: 'command_block.png', project: 'datapack' },
  { key: 'optifine', label: 'OptiFine', desc: '对当前游戏目录运行 OptiFine 安装器', icon: 'emerald.png' },
];

const LOADERS = [
  { key: '', label: '原版', icon: 'grass_block.png' },
  { key: 'fabric', label: 'Fabric', icon: 'loom.png' },
  { key: 'quilt', label: 'Quilt', icon: 'string.png' },
  { key: 'forge', label: 'Forge', icon: 'anvil.png' },
  { key: 'neoforge', label: 'NeoForge', icon: 'golden_apple.png' },
];

interface RemoteVersion {
  id: string;
  type?: string;
  release_time?: string;
}

export function DownloadPage({
  installed,
  onInstalled,
  notify,
}: {
  installed: VersionInfo[];
  onInstalled: () => Promise<void>;
  notify: (text: string) => void;
}) {
  const [category, setCategory] = useState<Category | null>(null);
  const [versions, setVersions] = useState<RemoteVersion[]>([]);
  const [items, setItems] = useState<ModItem[]>([]);
  const [query, setQuery] = useState('');
  const [mcVersion, setMcVersion] = useState('');
  const [loader, setLoader] = useState('');
  const [busy, setBusy] = useState('');
  const [chosenVersion, setChosenVersion] = useState('');
  const [custom, setCustom] = useState('');
  const [detail, setDetail] = useState<ModItem | null>(null);
  const [targetInstance, setTargetInstance] = useState('');
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [installing, setInstalling] = useState('');
  const [optiLog, setOptiLog] = useState('');

  useEffect(() => {
    rpc<RemoteVersion[]>('versions.remote', [200]).then(setVersions).catch(() => {});
    const off = on<{ done: number; total: number }>('vein:progress', (d) =>
      setProgress({ done: d.done, total: d.total })
    );
    return () => off();
  }, []);

  useEffect(() => {
    if (installed.length && !targetInstance) setTargetInstance(installed[0].id);
  }, [installed, targetInstance]);

  const percent = progress && progress.total > 0 ? Math.round((progress.done / progress.total) * 100) : 0;
  const projectType = CATEGORIES.find((c) => c.key === category)?.project;

  const runOptifine = async () => {
    const picked = await rpc<{ path: string }>('app.pickFile', [
      'Select OptiFine installer (.jar)',
      'OptiFine installer (*.jar);;All files (*.*)',
    ]);
    if (!picked.path) return;
    setBusy('install');
    setInstalling('OptiFine installer');
    setOptiLog('Running installer…');
    try {
      const result = await rpc<{ ok: boolean }>('optifine.install', [picked.path]);
      setOptiLog(result.ok ? 'Installer finished. Refresh versions if it created one.' : 'Failed');
      await onInstalled();
    } catch (err) {
      setOptiLog(`Failed: ${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
    }
  };

  const openCategory = (key: Category) => {
    setCategory(key);
    setItems([]);
    setQuery('');
    setChosenVersion('');
    setDetail(null);
    if (key !== 'version') {
      const project = CATEGORIES.find((c) => c.key === key)?.project || 'mod';
      rpc<ModItem[]>('mods.featured', [project, mcVersion, loader])
        .then(setItems)
        .catch(() => {});
    }
  };

  const runSearch = async () => {
    if (!category) return;
    setBusy('search');
    try {
      if (category === 'version') {
        if (!versions.length) setVersions(await rpc<RemoteVersion[]>('versions.remote', [200]));
      } else {
        const list = query.trim()
          ? await rpc<ModItem[]>('mods.search', [query.trim(), projectType || 'mod', mcVersion, loader])
          : await rpc<ModItem[]>('mods.featured', [projectType || 'mod', mcVersion, loader]);
        setItems(list);
      }
    } catch (err) {
      notify(`搜索失败：${(err as Error).message}`);
    } finally {
      setBusy('');
    }
  };

  const installVersion = async () => {
    if (!chosenVersion) {
      notify('请先选择一个游戏版本');
      return;
    }
    setBusy('install');
    setInstalling(`${chosenVersion}${loader ? ` + ${loader}` : ''}`);
    setProgress({ done: 0, total: 1 });
    try {
      await rpc('versions.install', [chosenVersion, loader, '', custom.trim()]);
      await onInstalled();
    } catch (err) {
      notify(`安装失败：${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
      setProgress(null);
    }
  };

  const installProject = async (item: ModItem) => {
    const instance = targetInstance || installed[0]?.id;
    if (!instance) {
      notify('请先安装一个游戏版本');
      return;
    }
    setBusy('install');
    setInstalling(item.title);
    setProgress({ done: 0, total: 1 });
    try {
      await rpc('mods.install', [item.slug, instance, projectType || 'mod', loader]);
      notify(`${item.title} 已安装到 ${instance}`);
      await onInstalled();
      setDetail(null);
    } catch (err) {
      notify(`安装失败：${(err as Error).message}`);
    } finally {
      setBusy('');
      setInstalling('');
      setProgress(null);
    }
  };

  const filteredVersions = useMemo(
    () =>
      versions.filter(
        (v) =>
          (v.type === 'release' || v.id.includes('.')) &&
          (!query.trim() || v.id.includes(query.trim()))
      ),
    [versions, query]
  );

  // ---------- 一级：分类菜单 ----------
  if (!category) {
    return (
      <div className="page">
        <div className="page-head">
          <h1>下载</h1>
          <span className="muted">先选分类，再挑要安装的内容</span>
        </div>
        <div className="cat-grid">
          {CATEGORIES.map((c) => (
            <button className="cat-card" key={c.key} onClick={() => openCategory(c.key)}>
              <img src={`icons/${c.icon}`} alt="" />
              <div>
                <b>{c.label}</b>
                <p>{c.desc}</p>
              </div>
            </button>
          ))}
        </div>

        {installing && (
          <div className="install-status">
            <i className="layui-icon layui-icon-loading layui-anim layui-anim-rotate layui-anim-loop" />
            <span>Installing {installing}</span>
            <span className="muted">进度见侧栏监控</span>
          </div>
        )}
      </div>
    );
  }

  // ---------- 二级：分类内页面 ----------
  return (
    <div className="page">
      <div className="dl-head">
        <button className="btn sm ghost" onClick={() => setCategory(null)}>
          ← Back
        </button>
        <h1>{CATEGORIES.find((c) => c.key === category)?.label}</h1>
        {category !== 'version' && (
          <span className="muted">
            {mcVersion ? `MC ${mcVersion}` : 'Any MC version'} · {loader || 'Any loader'}
          </span>
        )}
      </div>

      <div className="filter-row">
        <select value={mcVersion} onChange={(e) => setMcVersion(e.target.value)}>
          <option value="">任意 MC 版本</option>
          {versions.slice(0, 80).map((v) => (
            <option key={v.id} value={v.id}>
              {v.id}
            </option>
          ))}
        </select>
        {(category === 'version' || category === 'mod' || category === 'modpack') && (
          <select value={loader} onChange={(e) => setLoader(e.target.value)}>
            {LOADERS.map((l) => (
              <option key={l.key} value={l.key}>
                {l.label}
              </option>
            ))}
          </select>
        )}
        <input
          className="input"
          placeholder={category === 'version' ? 'Filter versions' : 'Search Modrinth'}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') runSearch();
          }}
        />
        <button className="btn primary sm" onClick={runSearch} disabled={busy === 'search'}>
          {busy === 'search' ? '…' : 'Search'}
        </button>
      </div>

      {category === 'optifine' ? (
        <div className="card">
          <div className="card-title">OptiFine 安装器</div>
          <p className="muted">
            OptiFine is not redistributable, so bring your own installer. The launcher runs it against
            your game folder with Java and then rescans installed versions.
          </p>
          <div className="kv">
            <span>游戏目录</span>
            <b>在「设置 → 游戏目录」里修改</b>
          </div>
          <div className="row-actions">
            <button className="btn primary" onClick={runOptifine} disabled={busy === 'install'}>
              {busy === 'install' ? 'Running…' : 'Choose installer & run'}
            </button>
          </div>
          {optiLog && <div className="activity">{optiLog}</div>}
        </div>
      ) : category === 'version' ? (
        <div className="dl-grid">
          <div className="card">
            <div className="card-title">游戏版本</div>
            <div className="ver-list">
              {filteredVersions.length === 0 && <div className="empty">没有可选版本</div>}
              {filteredVersions.map((v) => (
                <button
                  key={v.id}
                  className={`ver-row ${chosenVersion === v.id ? 'active' : ''}`}
                  onClick={() => setChosenVersion(v.id)}
                >
                  <img src="icons/grass_block.png" alt="" />
                  <span className="name">{v.id}</span>
                  <span className="tag">{v.type || 'release'}</span>
                  {installed.some((i) => i.id === v.id) && <span className="badge">已安装</span>}
                </button>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-title">安装</div>
            <div className="kv">
              <span>游戏版本</span>
              <b>{chosenVersion || '—'}</b>
            </div>
            <div className="kv">
              <span>加载器</span>
              <b>{LOADERS.find((l) => l.key === loader)?.label || 'Vanilla'}</b>
            </div>
            <div className="loader-grid">
              {LOADERS.map((l) => (
                <button
                  key={l.key || 'vanilla'}
                  className={`loader-card ${loader === l.key ? 'active' : ''}`}
                  onClick={() => setLoader(l.key)}
                >
                  <img className="loader-ico" src={`icons/${l.icon}`} alt="" />
                  <b>{l.label}</b>
                </button>
              ))}
            </div>
            <label className="muted">自定义实例名（可选）</label>
            <input
              className="input"
              placeholder={chosenVersion || 'instance name'}
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
            />
            <button className="btn primary block" style={{ marginTop: 10 }} onClick={installVersion} disabled={busy === 'install'}>
              {busy === 'install' ? 'Installing…' : `Install ${chosenVersion || ''}`}
            </button>
          </div>
        </div>
      ) : detail ? (
        <div className="card project-detail">
          <div className="mod-head">
            {detail.icon ? (
              <RemoteIcon src={detail.icon} className="detail-icon" />
            ) : (
              <RemoteIcon className="detail-icon" />
            )}
            <div>
              <h2>{detail.title}</h2>
              <p className="muted">{detail.author} · {(detail.downloads || 0).toLocaleString()} downloads</p>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <button className="btn sm" onClick={() => setDetail(null)}>
                Back
              </button>
            </div>
          </div>
          <p className="desc">{detail.description}</p>
          <div className="kv">
            <span>分类</span>
            <b>{CATEGORIES.find((c) => c.key === category)?.label}</b>
          </div>
          <div className="kv">
            <span>MC 版本 / 加载器</span>
            <b>
              {mcVersion || 'any'} · {loader || 'any'}
            </b>
          </div>
          <div className="row-actions">
            <select value={targetInstance} onChange={(e) => setTargetInstance(e.target.value)}>
              {installed.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id}
                </option>
              ))}
            </select>
            <button className="btn primary" onClick={() => installProject(detail)} disabled={busy === 'install'}>
              {busy === 'install' ? 'Installing…' : 'Install'}
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="proj-grid">
            {items.map((item) => (
              <button className="proj-card" key={item.slug} onClick={() => setDetail(item)}>
                <RemoteIcon src={item.icon} />
                <div>
                  <b>{item.title}</b>
                  <p>{item.description}</p>
                  <span className="muted">
                    {item.author} · {(item.downloads || 0).toLocaleString()}
                  </span>
                </div>
              </button>
            ))}
          </div>
          {items.length === 0 && <div className="empty">没找到，换个关键词试试。</div>}
        </>
      )}

      {installing && (
        <div className="install-status">
          <i className="layui-icon layui-icon-loading layui-anim layui-anim-rotate layui-anim-loop" />
          <span>Installing {installing}</span>
          <span className="muted">进度见侧栏监控</span>
        </div>
      )}
    </div>
  );
}
