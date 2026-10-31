import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';
import type { AppInfo, JavaRuntime } from './types';
import { applyTheme, currentTheme, Theme } from './theme';
import { currentLang, setLang } from './i18n';

export function SettingsPage({ notify }: { notify: (text: string) => void }) {
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [runtimes, setRuntimes] = useState<JavaRuntime[]>([]);
  const [javaBusy, setJavaBusy] = useState(0);
  const [javaMsg, setJavaMsg] = useState('');
  const [mcDir, setMcDir] = useState('');
  const [theme, setTheme] = useState<Theme>(currentTheme());
  const [transparent, setTransparent] = useState(
    localStorage.getItem('vl.transparent') === 'on'
  );

  useEffect(() => {
    rpc<AppInfo>('app.info').then(setInfo).catch(() => {});
    rpc<{ path: string }>('minecraft.getDir')
      .then((r) => setMcDir(r.path))
      .catch(() => {});
  }, []);

  const detect = async () => {
    try {
      setRuntimes(await rpc<JavaRuntime[]>('java.detect'));
    } catch (err) {
      notify(`探测失败：${(err as Error).message}`);
    }
  };

  const installJava = async (major: number) => {
    setJavaBusy(major);
    setJavaMsg(`正在安装 Java ${major}…`);
    try {
      const r = await rpc<{ path: string; downloaded: boolean }>('java.ensure', [major]);
      setJavaMsg(`Java ${major}：${r.path}（${r.downloaded ? '已下载' : '已存在'}）`);
    } catch (err) {
      setJavaMsg(`Java ${major} 失败：${(err as Error).message}`);
    } finally {
      setJavaBusy(0);
    }
  };

  const chooseDir = async () => {
    const picked = await rpc<{ path: string }>('app.pickDirectory', ['选择 .minecraft 目录']);
    if (!picked.path) return;
    const applied = await rpc<{ path: string }>('minecraft.setDir', [picked.path]);
    setMcDir(applied.path);
    notify(`游戏目录：${applied.path}`);
  };

  return (
    <div className="page">
      <div className="page-head">
        <h1>设置</h1>
        <span className="muted">分组展开，避免一屏堆满</span>
      </div>

      <div className="accordion">
        <details className="acc-item" open>
          <summary>外观与语言</summary>
          <div className="acc-body">
            <div className="kv">
              <span>主题</span>
              <b>
                <select
                  value={theme}
                  onChange={(e) => {
                    const next = e.target.value as Theme;
                    setTheme(next);
                    applyTheme(next);
                  }}
                >
                  <option value="dark">深色</option>
                  <option value="light">浅色</option>
                  <option value="system">跟随系统</option>
                </select>
              </b>
            </div>
            <div className="kv">
              <span>透明背景</span>
              <b>
                <button
                  className={transparent ? 'btn sm primary' : 'btn sm'}
                  onClick={() => {
                    const next = !transparent;
                    setTransparent(next);
                    localStorage.setItem('vl.transparent', next ? 'on' : 'off');
                    document.documentElement.dataset.transparent = next ? 'on' : 'off';
                  }}
                >
                  {transparent ? '已开启' : '已关闭'}
                </button>
              </b>
            </div>
            <div className="kv">
              <span>语言</span>
              <b>
                <button className={currentLang() === 'en' ? 'btn sm primary' : 'btn sm'} onClick={() => setLang('en')}>
                  English
                </button>{' '}
                <button className={currentLang() === 'zh' ? 'btn sm primary' : 'btn sm'} onClick={() => setLang('zh')}>
                  简体中文
                </button>
              </b>
            </div>
          </div>
        </details>

        <details className="acc-item">
          <summary>Java 运行时</summary>
          <div className="acc-body">
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button className="btn sm" onClick={detect}>自动探测</button>
              {[8, 17, 21].map((major) => (
                <button key={major} className="btn sm" disabled={javaBusy === major} onClick={() => installJava(major)}>
                  {javaBusy === major ? '…' : `安装 Java ${major}`}
                </button>
              ))}
            </div>
            {javaMsg && <p className="muted">{javaMsg}</p>}
            {runtimes.length === 0 ? (
              <p className="muted">尚未探测，点击「自动探测」扫描本机 Java</p>
            ) : (
              runtimes.map((rt) => (
                <div className="kv" key={rt.path}>
                  <span>Java {rt.major}</span>
                  <b className="mono">{rt.path}</b>
                </div>
              ))
            )}
          </div>
        </details>

        <details className="acc-item">
          <summary>游戏目录</summary>
          <div className="acc-body">
            <div className="kv">
              <span>当前</span>
              <b className="mono">{mcDir || '—'}</b>
            </div>
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button className="btn sm" onClick={chooseDir}>选择 .minecraft</button>
              <button
                className="btn sm"
                onClick={async () => {
                  const applied = await rpc<{ path: string }>('minecraft.setDir', ['']);
                  setMcDir(applied.path);
                }}
              >
                恢复默认
              </button>
            </div>
          </div>
        </details>

        <details className="acc-item">
          <summary>日志</summary>
          <div className="acc-body">
            <p className="muted">按天写入 VeinLauncher/log，分类存放 launcher / plugin / mlc / download。</p>
            <div className="row-actions" style={{ marginTop: 0 }}>
              <button className="btn sm" onClick={() => rpc('logs.openDir').catch(() => {})}>
                打开日志目录
              </button>
            </div>
          </div>
        </details>

        <details className="acc-item">
          <summary>关于</summary>
          <div className="acc-body">
            <div className="kv"><span>版本</span><b>{info?.version ?? '—'}</b></div>
            <div className="kv"><span>数据目录</span><b className="mono">{info?.dataDir ?? '—'}</b></div>
            <div className="kv"><span>架构</span><b>Python + PySide6 WebView + React + TS</b></div>
          </div>
        </details>
      </div>
    </div>
  );
}
