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
        {firstRun ? '第一次使用？正在为你准备运行环境。' : '正在启动，请稍候…'}
      </p>
      <div className="splash-bar">
        <i />
      </div>
    </div>
  );
}

type Method = 'offline' | 'microsoft' | 'littleskin';

const STEPS = [
  { key: 'welcome', title: '欢迎', sub: '快速了解' },
  { key: 'features', title: '能做什么', sub: '启动、安装、管理' },
  { key: 'account', title: '账号', sub: '离线 · 微软 · LittleSkin' },
  { key: 'privacy', title: '隐私', sub: '哪些数据留在本机' },
  { key: 'ready', title: '完成', sub: '开始游戏' },
];

const FEATURES = [
  { title: '一键启动', body: '已安装的版本会显示为卡片，选中后点启动即可。', icon: 'grass_block.png' },
  { title: '什么都能装', body: '原版、Fabric、Forge、Quilt、NeoForge、模组、整合包、光影与数据包。', icon: 'crafting_table.png' },
  { title: '存档与 Java', body: '不启动游戏也能读取存档，并自动匹配 Java 运行环境。', icon: 'chest.png' },
  { title: 'LittleSkin 皮肤', body: '登录 littleskin.cn 后可使用其皮肤与在线服务器。', icon: 'writable_book.png' },
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

  const canNext = useMemo(() => (stepKey === 'privacy' ? consent : true), [consent, stepKey]);

  const complete = async (accepted: boolean) => {
    try {
      await rpc('onboarding.complete', [accepted]);
    } catch {
      /* 写入失败不阻断进入启动器 */
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
      const info = await rpc<{ device_code: string; user_code: string; verification_uri: string }>('accounts.msStart');
      setDevice({ code: info.user_code, uri: info.verification_uri, deviceCode: info.device_code });
      await rpc('app.openUrl', [info.verification_uri]);
      setMessage(`请在刚打开的页面输入代码：${info.user_code}`);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const completeMicrosoft = async () => {
    if (!device) return;
    setBusy(true);
    setMessage('等待微软确认…');
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
      const account = await rpc<{ username: string }>('accounts.littleSkin', ['', lsEmail.trim(), lsPassword]);
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
            <span className="setup-kicker">首次使用</span>
            <h1>欢迎使用 Vein Launcher</h1>
            <p className="setup-lead">
              一个不挡路的 Minecraft 启动器：一键开玩，其他功能都在一页之内。用四个小步骤完成初始化。
            </p>
            <ul className="setup-points">
              <li>选择登录方式：离线、微软或 LittleSkin</li>
              <li>确认游戏文件存放位置</li>
              <li>了解启动器会在本机保存哪些数据</li>
            </ul>
          </div>
        );

      case 'features':
        return (
          <div className="setup-page">
            <span className="setup-kicker">功能一览</span>
            <h1>一个窗口搞定一切</h1>
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
            <p className="setup-lead">之后可以在「设置 → 账号」里继续添加。</p>
            <div className="account-setup">
              <aside className="account-rail">
                <button className={`account-option ${method === 'offline' ? 'active' : ''}`} onClick={() => setMethod('offline')}>
                  <b>离线</b><span>只需一个名字</span>
                </button>
                <button className={`account-option ${method === 'microsoft' ? 'active' : ''}`} onClick={() => setMethod('microsoft')}>
                  <b>微软</b><span>正版账号</span>
                </button>
                <button className={`account-option ${method === 'littleskin' ? 'active' : ''}`} onClick={() => setMethod('littleskin')}>
                  <b>LittleSkin</b><span>皮肤站账号</span>
                </button>
              </aside>

              <div className="account-form">
                {method === 'offline' && (
                  <>
                    <p className="muted">无需账号即可玩单人与局域网，名字只保存在本机。</p>
                    <div className="row-actions">
                      <input
                        className="input"
                        placeholder="离线用户名（3–16 个字符）"
                        value={name}
                        maxLength={16}
                        onChange={(e) => setName(e.target.value)}
                      />
                      <button className="btn primary" disabled={busy || name.trim().length < 3} onClick={addOffline}>
                        {busy ? '创建中…' : '使用这个名字'}
                      </button>
                    </div>
                  </>
                )}

                {method === 'microsoft' && (
                  <>
                    <p className="muted">微软会在自己的页面显示一个短代码，密码不会经过启动器。</p>
                    {!device ? (
                      <button className="btn primary" disabled={busy} onClick={startMicrosoft}>
                        {busy ? '请求代码中…' : '使用微软登录'}
                      </button>
                    ) : (
                      <div className="row-actions">
                        <code className="device-code">{device.code}</code>
                        <button className="btn primary" disabled={busy} onClick={completeMicrosoft}>
                          {busy ? '等待中…' : '我已经输入代码'}
                        </button>
                      </div>
                    )}
                  </>
                )}

                {method === 'littleskin' && (
                  <>
                    <p className="muted">使用 littleskin.cn 的邮箱和密码，仅保存访问令牌。</p>
                    <div className="row-actions">
                      <input className="input" placeholder="邮箱" value={lsEmail} onChange={(e) => setLsEmail(e.target.value)} />
                      <input className="input" type="password" placeholder="密码" value={lsPassword} onChange={(e) => setLsPassword(e.target.value)} />
                      <button className="btn primary" disabled={busy || !lsEmail.trim() || !lsPassword} onClick={signInLittleSkin}>
                        {busy ? '登录中…' : '登录'}
                      </button>
                    </div>
                  </>
                )}

                {message && <p className="setup-msg">{message}</p>}
                {accountLabel && <p className="setup-ok">已登录：{accountLabel}</p>}
              </div>
            </div>
          </div>
        );

      case 'privacy':
        return (
          <div className="setup-page">
            <span className="setup-kicker">开始之前</span>
            <h1>你的数据留在本机</h1>
            <div className="privacy-list">
              <div><b>本地保存</b><span>账号与访问令牌、启动器设置、日志、下载的游戏文件，都在 VeinLauncher 文件夹内。</span></div>
              <div><b>联网获取</b><span>Mojang / BMCLAPI 的版本与资源列表、Modrinth 的模组信息、微软或 littleskin.cn 的登录请求。除此之外不发送其他内容。</span></div>
              <div><b>不会收集</b><span>没有遥测、没有统计、没有广告标识。</span></div>
            </div>
            <div className="consent">
              <LayuiCheckbox checked={consent} onChange={setConsent} label="我已了解并同意 Vein Launcher 的使用条款与隐私政策。" />
            </div>
          </div>
        );

      default:
        return (
          <div className="setup-page">
            <span className="setup-kicker">全部完成</span>
            <h1>可以开始游戏了</h1>
            <p className="setup-lead">
              {accountLabel ? `已登录：${accountLabel}。` : '还没有账号，之后可在「设置 → 账号」添加。'}
              去下载页安装一个版本，然后点启动。
            </p>
            <ul className="setup-points">
              <li>下载 → 原版与加载器，安装 1.20.1</li>
              <li>启动页 → 选卡片 → 启动</li>
              <li>设置 → Java、游戏目录、主题与账号</li>
            </ul>
          </div>
        );
    }
  };

  return (
    <div className="setup">
      <aside className="setup-rail">
        <div className="setup-brand"><img src="logo.png" alt="" /><span>VEIN</span></div>
        <ol className="setup-steps">
          {STEPS.map((s, index) => (
            <li key={s.key} className={`setup-step ${index === step ? 'active' : ''} ${index < step ? 'done' : ''}`}>
              <i>{index < step ? '✓' : index + 1}</i>
              <div><b>{s.title}</b><span>{s.sub}</span></div>
            </li>
          ))}
        </ol>
        <div className="setup-rail-foot">
          <span>Vein Launcher 0.5.1</span>
          <button className="link-btn" onClick={() => complete(false)}>跳过引导</button>
        </div>
      </aside>

      <section className="setup-main">
        <div className="setup-content">{renderStep()}</div>
        <footer className="setup-actions">
          <button className="btn" onClick={back} disabled={step === 0 || busy}>上一步</button>
          <div className="spacer" />
          <span className="setup-count">{step + 1} / {STEPS.length}</span>
          {step < last ? (
            <button className="btn primary" onClick={next} disabled={!canNext || busy}>继续</button>
          ) : (
            <button className="btn primary" onClick={() => complete(consent)}>进入启动器</button>
          )}
        </footer>
      </section>
    </div>
  );
}
