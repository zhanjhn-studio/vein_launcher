import React, { useMemo, useState } from 'react';
import { rpc } from './bridge';
import { LayuiCheckbox } from './ui';

export function Splash({ firstRun }: { firstRun: boolean }) {
  return (
    <div className="splash">
      <div className="splash-mark">
        <img src="logo.png" alt="" />
        <span>VEIN</span>
      </div>
      <h1>欢迎使用 Vein Launcher</h1>
      <p className="muted">
        {firstRun
          ? "First time here? We're getting everything ready for you."
          : 'Starting up, one moment…'}
      </p>
      <div className="splash-bar">
        <i />
      </div>
    </div>
  );
}

type Method = 'offline' | 'microsoft' | 'littleskin';

const STEPS = [
  { key: 'welcome', title: 'Welcome', sub: 'A quick tour' },
  { key: 'features', title: 'What you can do', sub: 'Launch, install, manage' },
  { key: 'account', title: 'Your account', sub: 'Offline · Microsoft · LittleSkin' },
  { key: 'privacy', title: 'Privacy', sub: 'What stays on your PC' },
  { key: 'ready', title: 'Ready', sub: 'Start playing' },
];

const FEATURES = [
  {
    title: 'Launch in one click',
    body: 'Every installed version shows up as a card. Pick one, press Launch, done.',
    icon: 'grass_block.png',
  },
  {
    title: 'Install anything',
    body: 'Vanilla, Fabric, Forge, Quilt, NeoForge, mods, modpacks, shaders and datapacks.',
    icon: 'crafting_table.png',
  },
  {
    title: 'Worlds & Java handled',
    body: 'Reads your worlds without opening the game and fetches a matching Java runtime.',
    icon: 'chest.png',
  },
  {
    title: 'Skins from LittleSkin',
    body: 'Sign in to littleskin.cn to use its skins and its online servers.',
    icon: 'writable_book.png',
  },
];

export function Onboarding({ onDone }: { notify?: (text: string) => void; onDone: () => void }) {
  const [step, setStep] = useState(0);
  const [method, setMethod] = useState<Method>('offline');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [device, setDevice] = useState<{ code: string; uri: string; deviceCode: string } | null>(null);
  const [lsEmail, setLsEmail] = useState('');
  const [lsPassword, setLsPassword] = useState('');
  const [consent, setConsent] = useState(false);
  const [accountLabel, setAccountLabel] = useState('');

  const last = STEPS.length - 1;
  const stepKey = STEPS[step].key;

  const canNext = useMemo(() => {
    if (stepKey === 'privacy') return consent;
    return true;
  }, [consent, stepKey]);

  const complete = async (accepted: boolean) => {
    try {
      await rpc('onboarding.complete', [accepted]);
    } catch {
      /* 写标记失败不阻塞进入启动器 */
    }
    onDone();
  };

  const next = () => setStep((s) => Math.min(s + 1, last));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  const addOffline = async () => {
    setBusy(true);
    setMessage('');
    try {
      const account = await rpc<{ username: string }>('accounts.add', [name.trim()]);
      setAccountLabel(account.username);
      setMessage('');
      next();
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const startMicrosoft = async () => {
    setBusy(true);
    setMessage('');
    try {
      const info = await rpc<{ device_code: string; user_code: string; verification_uri: string }>(
        'accounts.msStart'
      );
      setDevice({ code: info.user_code, uri: info.verification_uri, deviceCode: info.device_code });
      await rpc('app.openUrl', [info.verification_uri]);
      setMessage(`Enter code ${info.user_code} on the page that just opened.`);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const completeMicrosoft = async () => {
    if (!device) return;
    setBusy(true);
    setMessage('Waiting for Microsoft to confirm…');
    try {
      const account = await rpc<{ username: string }>('accounts.msLogin', [device.deviceCode]);
      setAccountLabel(account.username);
      setMessage('');
      next();
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const signInLittleSkin = async () => {
    setBusy(true);
    setMessage('');
    try {
      const account = await rpc<{ username: string }>('accounts.littleSkin', [
        '',
        lsEmail.trim(),
        lsPassword,
      ]);
      setLsPassword('');
      setAccountLabel(account.username);
      next();
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const renderStep = () => {
    switch (stepKey) {
      case 'welcome':
        return (
          <div className="setup-page">
            <span className="setup-kicker">首次启动</span>
            <h1>欢迎使用 Vein Launcher</h1>
            <p className="setup-lead">
              A Minecraft launcher that keeps out of your way: one click to play, everything
              else one page away. Let&apos;s set it up for you in four short steps.
            </p>
            <ul className="setup-points">
              <li>选择登录方式 —— 离线、微软 或 LittleSkin</li>
              <li>选择游戏文件存放位置</li>
              <li>看看启动器在你电脑上存了什么</li>
            </ul>
          </div>
        );

      case 'features':
        return (
          <div className="setup-page">
            <span className="setup-kicker">功能一览</span>
            <h1>所有功能都在一个窗口里</h1>
            <div className="feature-grid">
              {FEATURES.map((f) => (
                <div className="feature-card" key={f.title}>
                  <img src={`icons/${f.icon}`} alt="" />
                  <b>{f.title}</b>
                  <span>{f.body}</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'account':
        return (
          <div className="setup-page">
            <span className="setup-kicker">第 3 步</span>
            <h1>选择账号</h1>
            <p className="setup-lead">
              You can add more accounts later in Settings → Accounts.
            </p>
            <div className="account-setup">
              <aside className="account-rail">
                <button
                  className={`account-option ${method === 'offline' ? 'active' : ''}`}
                  onClick={() => setMethod('offline')}
                >
                  <b>离线</b>
                  <span>只需一个名字</span>
                </button>
                <button
                  className={`account-option ${method === 'microsoft' ? 'active' : ''}`}
                  onClick={() => setMethod('microsoft')}
                >
                  <b>微软</b>
                  <span>官方正版账号</span>
                </button>
                <button
                  className={`account-option ${method === 'littleskin' ? 'active' : ''}`}
                  onClick={() => setMethod('littleskin')}
                >
                  <b>LittleSkin</b>
                  <span>皮肤站账号</span>
                </button>
              </aside>

              <div className="account-form">
                {method === 'offline' && (
                  <>
                    <p className="muted">
                      Play singleplayer and LAN without an account. The name is only used
                      locally.
                    </p>
                    <div className="row-actions">
                      <input
                        className="input"
                        placeholder="离线用户名（3–16 个字符）"
                        value={name}
                        maxLength={16}
                        onChange={(e) => setName(e.target.value)}
                      />
                      <button
                        className="btn primary"
                        disabled={busy || name.trim().length < 3}
                        onClick={addOffline}
                      >
                        {busy ? 'Creating…' : 'Use this name'}
                      </button>
                    </div>
                  </>
                )}

                {method === 'microsoft' && (
                  <>
                    <p className="muted">
                      Microsoft opens its own page with a short code — your password never
                      touches Vein Launcher.
                    </p>
                    {!device ? (
                      <button className="btn primary" disabled={busy} onClick={startMicrosoft}>
                        {busy ? 'Requesting code…' : 'Sign in with Microsoft'}
                      </button>
                    ) : (
                      <div className="row-actions">
                        <code className="device-code">{device.code}</code>
                        <button className="btn primary" disabled={busy} onClick={completeMicrosoft}>
                          {busy ? 'Waiting…' : 'I entered the code'}
                        </button>
                      </div>
                    )}
                  </>
                )}

                {method === 'littleskin' && (
                  <>
                    <p className="muted">
                      Use your littleskin.cn email and password. Only the access token is stored.
                    </p>
                    <div className="row-actions">
                      <input
                        className="input"
                        placeholder="Email"
                        value={lsEmail}
                        onChange={(e) => setLsEmail(e.target.value)}
                      />
                      <input
                        className="input"
                        type="password"
                        placeholder="密码"
                        value={lsPassword}
                        onChange={(e) => setLsPassword(e.target.value)}
                      />
                      <button
                        className="btn primary"
                        disabled={busy || !lsEmail.trim() || !lsPassword}
                        onClick={signInLittleSkin}
                      >
                        {busy ? 'Signing in…' : 'Sign in'}
                      </button>
                    </div>
                  </>
                )}

                {message && <p className="setup-msg">{message}</p>}
                {accountLabel && (
                  <p className="setup-ok">Signed in as {accountLabel}</p>
                )}
              </div>
            </div>
          </div>
        );

      case 'privacy':
        return (
          <div className="setup-page">
            <span className="setup-kicker">开始之前</span>
            <h1>数据只保存在你自己的电脑上</h1>
            <div className="privacy-list">
              <div>
                <b>本地保存</b>
                <span>
                  Accounts and access tokens, launcher settings, logs, downloaded game files —
                  all inside your VeinLauncher folder.
                </span>
              </div>
              <div>
                <b>会联网发送</b>
                <span>
                  Version and asset lists from Mojang / BMCLAPI, mod metadata from Modrinth,
                  sign-in traffic to Microsoft or littleskin.cn. Nothing else.
                </span>
              </div>
              <div>
                <b>不收集</b>
                <span>没有遥测、没有统计、没有广告标识。</span>
              </div>
            </div>
            <div className="consent">
              <LayuiCheckbox
                checked={consent}
                onChange={setConsent}
                label="I understand and agree to the terms and privacy policy of Vein Launcher."
              />
            </div>
          </div>
        );

      default:
        return (
          <div className="setup-page">
            <span className="setup-kicker">全部完成</span>
            <h1>可以开始玩了</h1>
            <p className="setup-lead">
              {accountLabel
                ? `Signed in as ${accountLabel}. `
                : 'No account yet — you can add one anytime in Settings → Accounts. '}
              Install a game version from the Download page and press Launch.
            </p>
            <ul className="setup-points">
              <li>「下载 → 原版与加载器」安装 1.20.1</li>
              <li>启动页 → 选版本卡 → 启动</li>
              <li>设置 → Java、游戏目录、主题与账号</li>
            </ul>
          </div>
        );
    }
  };

  return (
    <div className="setup">
      <aside className="setup-rail">
        <div className="setup-brand">
          <img src="logo.png" alt="" />
          <span>VEIN</span>
        </div>
        <ol className="setup-steps">
          {STEPS.map((s, index) => (
            <li
              key={s.key}
              className={`setup-step ${index === step ? 'active' : ''} ${index < step ? 'done' : ''}`}
            >
              <i>{index < step ? '✓' : index + 1}</i>
              <div>
                <b>{s.title}</b>
                <span>{s.sub}</span>
              </div>
            </li>
          ))}
        </ol>
        <div className="setup-rail-foot">
          <span>Vein Launcher 0.5.0</span>
          <button className="link-btn" onClick={() => complete(false)}>
            Skip setup
          </button>
        </div>
      </aside>

      <section className="setup-main">
        <div className="setup-content">{renderStep()}</div>
        <footer className="setup-actions">
          <button className="btn" onClick={back} disabled={step === 0 || busy}>
            Back
          </button>
          <div className="spacer" />
          <span className="setup-count">
            {step + 1} / {STEPS.length}
          </span>
          {step < last ? (
            <button className="btn primary" onClick={next} disabled={!canNext || busy}>
              Continue
            </button>
          ) : (
            <button className="btn primary" onClick={() => complete(consent)}>
              Enter launcher
            </button>
          )}
        </footer>
      </section>
    </div>
  );
}
