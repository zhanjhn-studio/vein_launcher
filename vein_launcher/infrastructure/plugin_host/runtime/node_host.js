#!/usr/bin/env node
/**
 * Vein Launcher 插件宿主运行时
 *
 * - 通过 stdio 与 Python 宿主做 JSON-RPC 2.0（逐行 JSON）
 * - 加载 NPM 风格插件，注入受限的 vein API
 * - 插件异常隔离，日志转发到 Python
 */

import readline from "node:readline";
import process from "node:process";
import path from "node:path";
import { pathToFileURL } from "node:url";

// stdout 只允许 JSON-RPC；插件里的 console 全部转 stderr
const toErr = (...args) => process.stderr.write(args.join(" ") + "\n");
console.log = toErr;
console.info = toErr;
console.warn = toErr;
console.error = toErr;
console.debug = toErr;

let nextId = 0;
const pending = new Map();
const plugins = new Map(); // id -> {api, exports}
const listeners = new Map(); // topic -> Set<{pluginId, handler}>

const send = (message) => process.stdout.write(JSON.stringify(message) + "\n");
const notify = (method, params) => send({ jsonrpc: "2.0", method, params });

function callHost(pluginId, api, args, timeoutMs = 30000) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`能力调用超时: ${api}`));
    }, timeoutMs);
    pending.set(id, {
      resolve: (value) => { clearTimeout(timer); resolve(value); },
      reject: (err) => { clearTimeout(timer); reject(err); },
    });
    send({ jsonrpc: "2.0", id, method: "host.call", params: { pluginId, api, args } });
  });
}

function buildApi(pluginId, manifest, dataDir) {
  const guard = (perm) => {
    if (!Array.isArray(manifest.permissions) || !manifest.permissions.includes(perm)) {
      throw new Error(`插件未声明权限 ${perm}`);
    }
  };

  const api = {
    plugin: {
      id: pluginId,
      version: manifest.version,
      displayName: manifest.displayName || pluginId,
      dataDir,
    },
    log(message, level = "info") {
      notify("plugin.log", { pluginId, level, message: String(message) });
    },
    file: {
      async readText(p) { guard("file.read"); return callHost(pluginId, "file.readText", [p]); },
      async writeText(p, content) { guard("file.write"); return callHost(pluginId, "file.writeText", [p, String(content)]); },
      async listDir(p = ".") { guard("file.read"); return callHost(pluginId, "file.listDir", [p]); },
    },
    http: {
      async getJson(url) { guard("network.http"); return callHost(pluginId, "network.http.getJson", [url]); },
    },
    config: {
      async get() { guard("config.read"); return callHost(pluginId, "config.read", []); },
      async set(key, value) { guard("config.write"); return callHost(pluginId, "config.write", [key, value]); },
    },
    ui: {
      async notify(title, message) { guard("ui.notify"); return callHost(pluginId, "ui.notify", [title, message]); },
    },
    download: {
      async queueTask(url, savePath) { guard("download.queue"); return callHost(pluginId, "download.queueTask", [url, savePath]); },
    },
    game: {
      async launch(versionId, username = "Player") { guard("game.launch"); return callHost(pluginId, "game.launch", [versionId, username]); },
    },
    mlc: {
      async launch(versionId, username = "Player") { guard("game.launch"); return callHost(pluginId, "mlc.launch", [versionId, username], 60000); },
      async worldInfo(versionId) { guard("mlc.world"); return callHost(pluginId, "mlc.world.info", [versionId]); },
      async worldCreate(versionId, name) { guard("mlc.world"); return callHost(pluginId, "mlc.world.create", [versionId, name]); },
      async playerInfo() { guard("mlc.player"); return callHost(pluginId, "mlc.player.info", []); },
      async modLoad() { guard("mlc.mod"); return callHost(pluginId, "mlc.mod.load", []); },
      async pluginSearch(keyword = "") { guard("mlc.plugin"); return callHost(pluginId, "mlc.plugin.search", [keyword]); },
      on(topic, handler) { return api.on(`mlc.${topic}`, handler); },
    },
    on(topic, handler) {
      if (typeof handler !== "function") throw new Error("handler 必须是函数");
      if (!listeners.has(topic)) listeners.set(topic, new Set());
      listeners.get(topic).add({ pluginId, handler });
      return () => api.off(topic, handler);
    },
    off(topic, handler) {
      const bucket = listeners.get(topic);
      if (!bucket) return;
      for (const item of [...bucket]) {
        if (item.pluginId === pluginId && item.handler === handler) bucket.delete(item);
      }
    },
  };
  return api;
}

async function loadPlugin({ pluginId, entry, manifest, dataDir }) {
  if (plugins.has(pluginId)) await unloadPlugin(pluginId);

  const api = buildApi(pluginId, manifest, dataDir);
  const module = await Promise.race([
    import(pathToFileURL(path.resolve(entry)).href),
    new Promise((_, reject) => setTimeout(() => reject(new Error("插件加载超时(10s)")), 10000)),
  ]);

  const exportsObj = module.default ?? module;
  if (typeof exportsObj.activate === "function") {
    await exportsObj.activate(api);
  } else {
    api.log("插件未导出 activate(ctx)，按声明式插件处理", "warn");
  }

  plugins.set(pluginId, { api, exports: exportsObj });
  api.log(`已激活 v${manifest.version}`);
  return { ok: true };
}

async function unloadPlugin(pluginId) {
  const record = plugins.get(pluginId);
  if (!record) return { ok: true };
  try {
    if (typeof record.exports?.deactivate === "function") await record.exports.deactivate();
  } catch (err) {
    notify("plugin.error", { pluginId, error: String(err) });
  }
  for (const [topic, bucket] of listeners) {
    for (const item of [...bucket]) if (item.pluginId === pluginId) bucket.delete(item);
    if (bucket.size === 0) listeners.delete(topic);
  }
  plugins.delete(pluginId);
  return { ok: true };
}

function dispatch(topic, payload) {
  const bucket = listeners.get(topic);
  if (!bucket) return;
  for (const { pluginId, handler } of [...bucket]) {
    try {
      const result = handler(payload, topic);
      if (result && typeof result.catch === "function") {
        result.catch((err) => notify("plugin.error", { pluginId, error: String(err) }));
      }
    } catch (err) {
      notify("plugin.error", { pluginId, error: String(err) });
    }
  }
}

async function handleRequest(method, params) {
  switch (method) {
    case "host.ping":
      return { node: process.version, platform: process.platform };
    case "plugin.load":
      return loadPlugin(params);
    case "plugin.unload":
      return unloadPlugin(params.pluginId);
    case "host.shutdown":
      setTimeout(() => process.exit(0), 50);
      return { ok: true };
    default:
      throw new Error(`未知方法: ${method}`);
  }
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

rl.on("line", async (line) => {
  const text = line.trim();
  if (!text) return;

  let message;
  try {
    message = JSON.parse(text);
  } catch {
    process.stderr.write(`非法 JSON: ${text.slice(0, 120)}\n`);
    return;
  }

  if (message.id !== undefined && (message.result !== undefined || message.error !== undefined)) {
    const entry = pending.get(message.id);
    if (entry) {
      pending.delete(message.id);
      if (message.error) entry.reject(new Error(message.error.message ?? "调用失败"));
      else entry.resolve(message.result);
    }
    return;
  }

  if (message.id === undefined) {
    if (message.method === "event.emit") {
      const { topic, payload } = message.params ?? {};
      dispatch(topic, payload);
    }
    return;
  }

  try {
    const result = await handleRequest(message.method, message.params ?? {});
    send({ jsonrpc: "2.0", id: message.id, result });
  } catch (err) {
    send({ jsonrpc: "2.0", id: message.id, error: { code: -32603, message: String(err?.message ?? err) } });
  }
});

rl.on("close", async () => {
  for (const id of [...plugins.keys()]) {
    try { await unloadPlugin(id); } catch { /* 关闭期忽略 */ }
  }
  process.exit(0);
});

process.on("uncaughtException", (err) => {
  notify("plugin.error", { pluginId: "<host>", error: String(err?.stack ?? err) });
});
process.on("unhandledRejection", (reason) => {
  notify("plugin.error", { pluginId: "<host>", error: String(reason) });
});

process.stderr.write("[vein-plugin-host] ready\n");
