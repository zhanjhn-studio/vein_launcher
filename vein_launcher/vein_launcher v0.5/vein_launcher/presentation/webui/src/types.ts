export interface VersionInfo {
  id: string;
  type?: string;
  release_time?: string;
}

export interface AccountInfo {
  id: string;
  username: string;
  selected?: boolean;
  type?: string;
  uuid?: string;
  online?: boolean;
  server?: string;
}

export interface ModItem {
  slug: string;
  title: string;
  description: string;
  icon: string;
  downloads: number;
  author: string;
  type: string;
  url: string;
}

export interface PluginInfo {
  name: string;
  version: string;
  displayName: string;
  description: string;
  permissions: string[];
  enabled: boolean;
  loaded: boolean;
  path: string;
}

export interface HostState {
  running: boolean;
  pid: number | null;
  node: string | null;
}

export interface PluginState {
  host: HostState;
  plugins: PluginInfo[];
}

export interface DownloadTask {
  id: string;
  name: string;
  done: number;
  total: number;
  active: boolean;
  error: string | null;
}

export interface MlcState {
  connected: boolean;
  pid: number | null;
}

export interface JavaRuntime {
  path: string;
  major: number;
  version: string;
  vendor: string;
}

export interface AppInfo {
  version: string;
  dataDir: string;
  accountCount?: number;
  firstRun?: boolean;
}

export type Category =
  | 'vanilla'
  | 'modpack'
  | 'mod'
  | 'resourcepack'
  | 'shader'
  | 'datapack'
  | 'plugin';
