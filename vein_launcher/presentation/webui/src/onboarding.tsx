import React, { useEffect, useState } from 'react';
import { rpc } from './bridge';

export function Splash({ firstRun }: { firstRun: boolean }) {
  return (
    <div className="splash">
      <div className="splash-mark">
        <img src="logo.png" alt="" />
        <span>VEIN</span>
      </div>
      <h1>Welcome to Vein Launcher</h1>
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

interface Props {
  notify: (text: string) => void;
  onDone: () => void;
}

export function Onboarding({ notify, onDone }: Props) {
  const [step, setStep] = useState(0);
  const [method, setMethod] = useState<Method>('offline');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [device, setDevice] = useState<{ code: string; uri: string; deviceCode: string } | null>(null);
  const [lsEmail, setLsEmail] = useState('');
  const [lsPassword, setLsPassword] = useState('');

  useEffect(() => {
    setMessage('');
  }, [method]);

  const finish = () => setStep(2);

  const addOffline = async () => {
    setBusy(true);
    try {
      await rpc('accounts.add', [name.trim()]);
      setMessage('');
      finish();
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
      setMessage(`Enter code ${info.user_code} in the page we just opened.`);
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
      await rpc('accounts.msLogin', [device.deviceCode]);
      setMessage('');
      finish();
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
      await rpc('accounts.littleSkin', ['', lsEmail.trim(), lsPassword]);
      setLsPassword('');
      finish();
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const skip = async () => {
    try {
      await rpc('onboarding.complete');
    } catch {
      /* 跳过失败不阻塞 */
    }
    onDone();
  };

  return (
    <div className="onboard-mask">
      <div className="onboard">
        <img className="onboard-logo" src="logo.png" alt="" />

        {step === 0 && (
          <>
            <h1>Welcome to Vein Launcher</h1>
            <p className="muted">
              It looks like this is your first time here. Pick how you want to sign in and
              we&apos;ll take care of the rest.
            </p>
            <div className="onboard-actions">
              <button className="btn primary" onClick={() => setStep(1)}>
                Get started
              </button>
              <button className="btn" onClick={skip}>
                Skip for now
              </button>
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <h1>How do you play?</h1>
            <div className="method-grid">
              <button
                className={`method-card ${method === 'offline' ? 'active' : ''}`}
                onClick={() => setMethod('offline')}
              >
                <b>Offline account</b>
                <span>Pick a name and play singleplayer or LAN right away.</span>
              </button>
              <button
                className={`method-card ${method === 'microsoft' ? 'active' : ''}`}
                onClick={() => setMethod('microsoft')}
              >
                <b>Microsoft account</b>
                <span>Official login for online servers and your own skin.</span>
              </button>
              <button
                className={`method-card ${method === 'littleskin' ? 'active' : ''}`}
                onClick={() => setMethod('littleskin')}
              >
                <b>LittleSkin</b>
                <span>Sign in with littleskin.cn to use its skins and servers.</span>
              </button>
            </div>

            {method === 'offline' && (
              <div className="row-actions onboard-form">
                <input
                  className="input"
                  placeholder="Your offline name (3–16 characters)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={16}
                />
                <button
                  className="btn primary"
                  disabled={busy || name.trim().length < 3}
                  onClick={addOffline}
                >
                  Create account
                </button>
              </div>
            )}

            {method === 'microsoft' && (
              <div className="onboard-form">
                <p className="muted">
                  We&apos;ll open Microsoft&apos;s page with a short code. Your password never
                  touches Vein Launcher.
                </p>
                {!device && (
                  <button className="btn primary" disabled={busy} onClick={startMicrosoft}>
                    {busy ? 'Requesting code…' : 'Sign in with Microsoft'}
                  </button>
                )}
                {device && (
                  <div className="row-actions">
                    <code className="device-code">{device.code}</code>
                    <button className="btn primary" disabled={busy} onClick={completeMicrosoft}>
                      {busy ? 'Waiting…' : 'I entered the code'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {method === 'littleskin' && (
              <div className="onboard-form">
                <p className="muted">
                  Use the email and password of your littleskin.cn account. We keep only the
                  access token, never the password.
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
                    placeholder="Password"
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
              </div>
            )}

            {message && <p className="onboard-msg">{message}</p>}

            <div className="onboard-actions">
              <button className="btn" onClick={() => setStep(0)}>
                Back
              </button>
              <button className="btn" onClick={skip}>
                Skip for now
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h1>You&apos;re all set</h1>
            <p className="muted">
              Your account is ready. You can add more accounts, change Java or pick a game
              folder anytime in Settings.
            </p>
            <div className="onboard-actions">
              <button className="btn primary" onClick={onDone}>
                Enter launcher
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
