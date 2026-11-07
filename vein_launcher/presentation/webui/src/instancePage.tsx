import React, { useEffect, useMemo, useState } from 'react';
import { rpc } from './bridge';
import { Empty, LayuiCheckbox } from './ui';
import type { VersionInfo } from './types';

type Kind = 'mod' | 'resourcepack' | 'shader' | 'datapack' | 'modpack';
type Tab = Kind | 'worlds' | 'console';

interface Entry {
  name: string;
  enabled: boolean;
  size: number;
  dir: boolean;
}

interface WorldInfo {
  name: string;
  seed: number;
  version: string;
  instance: string;
  path: string;
  folder: string;
  difficulty?: string;
  last_played?: string;
}

const TABS: { key: Tab; label: string; folder?: string }[] = [
  { key: 'mod', label: 'Mods', folder: 'mods' },
  { key: 'resourcepack', label: 'Resource packs', folder: 'resourcepacks' },
  { key: 'shader', label: 'Shaders', folder: 'shaderpacks' },
  { key: 'datapack', label: 'Datapacks', folder: 'datapacks' },
  { key: 'modpack', label: 'Modpacks', folder: 'modpacks' },
  { key: 'worlds', label: 'Worlds' },
  { key: 'console', label: 'Console' },
];

function humanSize(bytes: number): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function InstancePage({
  installed,
  selected,
  notify,
  onSelect,
  onDownload,
  onDeleted,
  Console,
}: {
  installed: VersionInfo[];
  selected: string;
  notify: (text: string) => void;
  onSelect: (id: string) => void;
  onDownload: () => void;
  onDeleted: () => Promise<void> | void;
  Console: React.ReactNode;
}) {
  const [tab, setTab] = useState<Tab>('mod');
  const [contents, setContents] = useState<Record<string, Entry[]>>({});
  const [worlds, setWorlds] = useState<WorldInfo[]>([]);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [confirm, setConfirm] = useState<
    | { kind: 'file'; type: Kind; name: string }
    | { kind: 'world'; folder: string }
    | { kind: 'instance' }
    | null
  >(null);
  const [scan, setScan] = useState<{ world: WorldInfo; data: unknown } | null>(null);

  const version = selected || installed[0]?.id || '';

  const load = async (target = version) => {
    if (!target) return;
    setBusy('load');
    try {
      const [content, worldsList] = await Promise.all([
        rpc<Record<string, Entry[]>>('instances.contents', [target]),
        rpc<WorldInfo[]>('instances.worlds', [target]),
      ]);
      setContents(content || {});
      setWorlds(worldsList || []);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy('');
    }
  };

  useEffect(() => {
    load(version);
    setScan(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

  const entries = useMemo(
    () => (tab === 'worlds' || tab === 'console' ? [] : contents[tab] || []),
    [contents, tab]
  );

  const toggle = async (entry: Entry) => {
    setBusy(`toggle-${entry.name}`);
    try {
      await rpc('instances.toggle', [version, tab, entry.name, !entry.enabled]);
      await load(version);
    } catch (err) {
      notify((err as Error).message);
    } finally {
      setBusy('');
    }
  };

  const doDelete = async () => {
    if (!confirm) return;
    setBusy('delete');
    try {
      if (confirm.kind === 'file') {
        await rpc('instances.deleteFile', [version, confirm.type, confirm.name]);
        await load(version);
      } else if (confirm.kind === 'world') {
        await rpc('instances.deleteWorld', [version, confirm.folder]);
        await load(version);
      } else {
        await rpc('versions.delete', [version]);
        await onDeleted();
        notify(`Deleted instance ${version}`);
      }
      setConfirm(null);
    } catch (err) {
      notify((err as Error).message);
    } finally {
      setBusy('');
    }
  };

  const scanWorld = async (world: WorldInfo) => {
    setBusy('scan');
    setScan(null);
    try {
      const data = await rpc('mc2.scan', [version, world.folder]);
      setScan({ world, data });
    } catch (err) {
      notify((err as Error).message);
    } finally {
      setBusy('');
    }
  };

  if (installed.length === 0) {
    return (
      <div className="page">
        <div className="page-head">
          <h1>Instances</h1>
          <span className="muted">Manage mods, worlds and files per version</span>
        </div>
        <Empty>
          No installed versions yet.{' '}
          <button className="link-btn" onClick={onDownload}>
            Go install one →
          </button>
        </Empty>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>Instances</h1>
        <span className="muted">{installed.length} installed</span>
      </div>

      <div className="instance-layout">
        <aside className="instance-list">
          {installed.map((item) => (
            <button
              key={item.id}
              className={`instance-item ${item.id === version ? 'active' : ''}`}
              onClick={() => onSelect(item.id)}
            >
              <b>{item.id}</b>
              <span>{item.type || 'release'}</span>
            </button>
          ))}
        </aside>

        <section className="instance-main">
          <header className="instance-head">
            <div>
              <h2>{version}</h2>
              <span className="muted">
                {contents.mod?.length ?? 0} mods · {worlds.length} worlds
              </span>
            </div>
            <div className="row-actions">
              <button
                className="btn sm"
                onClick={() => rpc('versions.openFolder', [version]).catch(() => {})}
              >
                <i className="layui-icon layui-icon-folder" /> Open folder
              </button>
              <button
                className="btn sm"
                onClick={() => setConfirm({ kind: 'instance' })}
                style={{ color: '#e07a7a' }}
              >
                <i className="layui-icon layui-icon-delete" /> Delete instance
              </button>
            </div>
          </header>

          <div className="instance-tabs">
            {TABS.map((item) => (
              <button
                key={item.key}
                className={`instance-tab ${tab === item.key ? 'active' : ''}`}
                onClick={() => setTab(item.key)}
              >
                {item.label}
                {item.key !== 'worlds' && item.key !== 'console' && (
                  <em>{contents[item.key]?.length ?? 0}</em>
                )}
              </button>
            ))}
          </div>

          {message && <p className="muted">{message}</p>}

          {tab === 'console' ? (
            <div className="instance-console">{Console}</div>
          ) : tab === 'worlds' ? (
            <div className="instance-worlds">
              {worlds.length === 0 ? (
                <Empty>No worlds in this instance yet.</Empty>
              ) : (
                <div className="world-rows">
                  {worlds.map((world) => (
                    <div className="world-row" key={world.folder}>
                      <button className="world-main" onClick={() => scanWorld(world)}>
                        <b>{world.name}</b>
                        <span>seed {world.seed}</span>
                        <span>{world.version}</span>
                      </button>
                      <button
                        className="btn sm ghost"
                        onClick={() => setConfirm({ kind: 'world', folder: world.folder })}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {scan && (
                <div className="scan-panel">
                  <div className="scan-head">
                    <b>{scan.world.name}</b>
                    <span className="muted">seed {scan.world.seed}</span>
                    <button className="btn sm ghost" onClick={() => setScan(null)}>
                      Close
                    </button>
                  </div>
                  <pre className="scan-body">{JSON.stringify(scan.data, null, 2)}</pre>
                </div>
              )}
            </div>
          ) : (
            <div className="instance-files">
              <div className="files-toolbar">
                <span className="muted">
                  {TABS.find((t) => t.key === tab)?.folder}/ · {entries.length} files
                </span>
                <div className="spacer" />
                <button className="btn sm primary" onClick={onDownload}>
                  <i className="layui-icon layui-icon-download-circle" /> Download more
                </button>
                <button className="btn sm" onClick={() => load(version)} disabled={busy !== ''}>
                  <i className="layui-icon layui-icon-refresh" /> Refresh
                </button>
              </div>

              {entries.length === 0 ? (
                <Empty>
                  Nothing in this folder yet.{' '}
                  <button className="link-btn" onClick={onDownload}>
                    Browse the download page →
                  </button>
                </Empty>
              ) : (
                <div className="file-rows">
                  {entries.map((entry) => (
                    <div className={`file-row ${entry.enabled ? '' : 'off'}`} key={entry.name}>
                      <span className="file-name" title={entry.name}>
                        {entry.name}
                      </span>
                      <span className="file-size">{humanSize(entry.size)}</span>
                      <LayuiCheckbox
                        checked={entry.enabled}
                        disabled={busy === `toggle-${entry.name}`}
                        onChange={() => toggle(entry)}
                        label={entry.enabled ? 'Enabled' : 'Disabled'}
                      />
                      <button
                        className="btn sm ghost"
                        onClick={() =>
                          setConfirm({ kind: 'file', type: tab as Kind, name: entry.name })
                        }
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      {confirm && (
        <div className="modal-mask">
          <div className="modal">
            <h3>
              {confirm.kind === 'instance'
                ? `Delete instance ${version}?`
                : confirm.kind === 'world'
                  ? 'Delete this world?'
                  : `Delete ${confirm.kind === 'file' ? confirm.name : ''}?`}
            </h3>
            <p className="muted">
              {confirm.kind === 'instance'
                ? 'The whole version folder will be removed, including mods and worlds inside it. This cannot be undone.'
                : 'This removes the file from disk. This cannot be undone.'}
            </p>
            <div className="row-actions">
              <button className="btn" onClick={() => setConfirm(null)}>
                Cancel
              </button>
              <button
                className="btn primary"
                style={{ background: '#b45454', borderColor: '#b45454' }}
                onClick={doDelete}
                disabled={busy === 'delete'}
              >
                {busy === 'delete' ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
