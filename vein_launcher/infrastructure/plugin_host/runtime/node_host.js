#!/usr/bin/env node
/**
 * Vein Launcher 插件宿主运行时（Node.js 侧）
 *
 * 职责：
 *  1. 通过 stdio 与 Python 宿主做 JSON-RPC 2.0 通信（每行一个 JSON）。
 *  2. 加载 NPM 插件，向插件注入受限的 `vein` API。
 *  3. 隔离插件异常，转发日志，广播启动器事件。
 *
 * 插件契约（ESM）：
 *   export async function activate(ctx) { ... }   // ctx 即 vein API
 *   export async function deactivate() { ... }    // 可选
 *   export const commands = { doSomething() {} }  // 可选，可被宿主 invoke
 */

import readline from "node:readline";
import process from "node:process";
import { pathToFileURL } from "node:url";
import path from "node:path";

// ---------- 通道：stdout 只允许 JSON-RPC，其他输出全部走 stderr ----------
const originalLog = console.log.bind(console);
console.log = (...args) => process.stderr.write(args.join(" ") + "\n");
console.info = console.log;
console.debug = console.log;
console.warn = (...args) => process.stderr.write("[warn] " + args.join(" ") + "\n");
console.error = (...args) => process.stderr.write("[error] " + args.join(" ") + "\n");

let nextId = 0;
const pending = new Map();
const plugins = new Map(); // pluginId -> { api, exports, listeners }
const globalListeners = new Map(); // topic -> Set<{pluginId, handler}>

function send(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}

function notify(method, params) {
  send({ jsonrpc: "2.0", method, params });
}

/** 向 Python 宿主发起请求 */
function callHost(pluginId, api, args, timeoutMs = 30000) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`能力调用超时: ${api}`));
    }, timeoutMs);

    pending.set(id, {
      resolve: (v) => { clearTimeout(timer); resolve(v); },
      reject: (e) => { clearTimeout(timer); reject(e); },
    });

    send({
      jsonrpc: "2.0",
      id,
      method: "host.call",
      params: { pluginId, api, args },
    });
  });
}

/** 构造某个插件的受限 API */
function buildApi(pluginId, manifest, dataDir) {
  const requirePerm = (perm) => {
    if (!Array.isArray(manifest.permissions) || !manifest.permissions.includes(perm)) {
      throw new Error(`插件未声明权限 ${perm}`);
    }
  };

  return {
    plugin: {
      id: pluginId,
      version: manifest.version,
      displayName: manifest.displayName || pluginId,
      dataDir,
      apiVersion: manifest.apiVersion || "1.0",
    },

    log: (message, level = "info") => {
      notify("plugin.log", { pluginId, level, message: String(message) });
    },

    // ---- 文件能力（宿主侧还会做路径沙箱校验）----
    file: {
      async readText(p) {
        requirePerm("file.read");
        return callHost(pluginId, "file.readText", [p]);
      },
      async writeText(p, content) {
        requirePerm("file.write");
        return callHost(pluginId, "file.writeText", [p, String(content)]);
      },
      async listDir(p = ".") {
        requirePerm("file.read");
        return callHost(pluginId, "file.listDir", [p]);
      },
    },

    // ---- 下载队列 ----
    download: {
      async queueTask(url, savePath) {
        requirePerm("download.queue");
        return callHost(pluginId, "download.queueTask", [url, savePath]);
      },
      async cancel(taskId) {
        requirePerm("download.cancel");
        return callHost(pluginId, "download.cancel", [taskId]);
      },
    },

    // ---- 游戏进程 ----
    game: {
      async launch(versionId, memoryMb = 4096) {
        requirePerm("game.launch");
        return callHost(pluginId, "game.launch", [versionId, memoryMb], 60000);
      },
    },

    // ---- UI ----
    ui: {
      async notify(title, message, type = "info") {
        requirePerm("ui.notify");
        return callHost(pluginId, "ui.notify", [title, message, type]);
      },
    },

    // ---- 配置 ----
    config: {
      async get() {
        requirePerm("config.read");
        return callHost(pluginId, "config.read", []);
      },
      async set(key, value) {
        requirePerm("config.write");
        return callHost(pluginId, "config.write", [key, value]);
      },
    },

    // ---- 网络（宿主代理，避免插件直连）----
    http: {
      async getJson(url) {
        requirePerm("network.http");
        return callHost(pluginId, "network.http.getJson", [url]);
      },
    },

    // ---- 事件订阅 ----
    on(topic, handler) {
      if (typeof handler !== "function") throw new Error("事件处理器必须是函数");
      if (!globalListeners.has(topic)) globalListeners.set(topic, new Set());
      globalListeners.get(topic).add({ pluginId, handler });
      return () => this.off(topic, handler);
    },

    off(topic, handler) {
      const bucket = globalListeners.get(topic);
      if (!bucket) return;
      for (const item of bucket) {
        if (item.pluginId === pluginId && item.handler === handler) bucket.delete(item);
      }
    },
  };
}

/** 加载单个插件 */
async function loadPlugin({ pluginId, entry, manifest, dataDir }) {
  if (plugins.has(pluginId)) {
    await unloadPlugin(pluginId);
  }

  const api = buildApi(pluginId, manifest, dataDir);
  const entryUrl = pathToFileURL(path.resolve(entry)).href;

  const loaded = await Promise.race([
    import(entryUrl),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error("插件加载超时(10s)")), 10000)
    ),
  ]);

  const exportsObj = loaded.default ?? loaded;

  if (typeof exportsObj.activate === "function") {
    await exportsObj.activate(api);
  } else if (typeof loaded.activate === "function") {
    await loaded.activate(api);
  } else {
    api.log("插件未导出 activate()，按声明式插件处理", "warn");
  }

  plugins.set(pluginId, { api, exports: exportsObj, dataDir });
  notify("plugin.ready", { pluginId });
  api.log(`插件已激活 v${manifest.version}`);
  return { ok: true };
}

async function unloadPlugin(pluginId) {
  const record = plugins.get(pluginId);
  if (!record) return { ok: true };

  try {
    if (typeof record.exports?.deactivate === "function") {
      await record.exports.deactivate();
    }
  } catch (err) {
    notify("plugin.error", { pluginId, error: String(err) });
  }

  for (const [topic, bucket] of globalListeners) {
    for (const item of bucket) if (item.pluginId === pluginId) bucket.delete(item);
    if (bucket.size === 0) globalListeners.delete(topic);
  }

  plugins.delete(pluginId);
  return { ok: true };
}

/** 分发事件给插件（单个插件异常不影响其他插件） */
function dispatchEvent(topic, payload) {
  const bucket = globalListeners.get(topic);
  if (!bucket) return 0;

  let delivered = 0;
  for (const { pluginId, handler } of [...bucket]) {
    try {
      const result = handler(payload, topic);
      if (result && typeof result.catch === "function") {
        result.catch((err) =>
          notify("plugin.error", { pluginId, error: `事件处理失败: ${err}` })
        );
      }
      delivered += 1;
    } catch (err) {
      notify("plugin.error", { pluginId, error: `事件处理失败: ${err}` });
    }
  }
  return delivered;
}

/** 方法分发表 */
async function handleRequest(method, params) {
  switch (method) {
    case "host.ping":
      return {
        node: process.version,
        platform: process.platform,
        pluginsRoot: params?.pluginsRoot ?? null,
        hostVersion: "1.0.0",
      };

    case "plugin.load":
      return loadPlugin(params);

    case "plugin.unload":
      return unloadPlugin(params.pluginId);

    case "plugin.invoke": {
      const record = plugins.get(params.pluginId);
      if (!record) throw new Error(`插件未加载: ${params.pluginId}`);
      const method = params.method;
      const candidates = [
        record.exports?.[method],
        record.exports?.commands?.[method],
        record.exports?.default?.[method],
      ];
      const fn = candidates.find((c) => typeof c === "function");
      if (!fn) throw new Error(`插件未导出方法: ${method}`);
      const result = await fn(...(params.args ?? []));
      return { result: result ?? null };
    }

    case "plugin.list":
      return { plugins: [...plugins.keys()] };

    case "host.shutdown":
      setTimeout(() => process.exit(0), 50);
      return { ok: true };

    default:
      throw new Error(`未知方法: ${method}`);
  }
}

// ---------- JSON-RPC 主循环 ----------
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

rl.on("line", async (line) => {
  const text = line.trim();
  if (!text) return;

  let message;
  try {
    message = JSON.parse(text);
  } catch {
    process.stderr.write(`非法 JSON 行: ${text.slice(0, 200)}\n`);
    return;
  }

  // 响应
  if (message.id !== undefined && (message.result !== undefined || message.error !== undefined)) {
    const entry = pending.get(message.id);
    if (entry) {
      pending.delete(message.id);
      if (message.error) entry.reject(new Error(message.error.message ?? "能力调用失败"));
      else entry.resolve(message.result);
    }
    return;
  }

  // 通知
  if (message.id === undefined) {
    if (message.method === "event.emit") {
      const { topic, payload } = message.params ?? {};
      dispatchEvent(topic, payload);
    }
    return;
  }

  // 请求
  try {
    const result = await handleRequest(message.method, message.params ?? {});
    send({ jsonrpc: "2.0", id: message.id, result });
  } catch (err) {
    send({
      jsonrpc: "2.0",
      id: message.id,
      error: { code: -32603, message: String(err?.message ?? err) },
    });
  }
});

rl.on("close", async () => {
  for (const pluginId of [...plugins.keys()]) {
    try {
      await unloadPlugin(pluginId);
    } catch {
      /* 忽略关闭期异常 */
    }
  }
  process.exit(0);
});

// ---------- 全局异常隔离 ----------
process.on("uncaughtException", (err) => {
  notify("plugin.error", { pluginId: "<unknown>", error: String(err?.stack ?? err) });
  process.stderr.write(`[uncaught] ${err?.stack ?? err}\n`);
});

process.on("unhandledRejection", (reason) => {
  notify("plugin.error", { pluginId: "<unknown>", error: String(reason) });
  process.stderr.write(`[unhandled] ${reason}\n`);
});

process.stderr.write("[vein-plugin-host] 已启动，等待 Python 宿主指令\n");
