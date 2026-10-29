/**
 * 示例插件：游戏日志记录
 *
 * 演示三件事：
 * 1. 订阅 MLC 事件（mlc.game.log / mlc.game.exit）
 * 2. 用宿主能力写自己的沙箱目录
 * 3. 调用 MLC 能力读取存档
 */

import path from "node:path";

const MAX_LINES = 2000;

export async function activate(vein) {
  vein.log("游戏日志记录插件已启动");

  const logFile = path.join(vein.plugin.dataDir, "game.log");
  let buffer = [];
  let timer = null;

  const flush = async () => {
    if (buffer.length === 0) return;
    const chunk = buffer.join("");
    buffer = [];
    try {
      const previous = await vein.file.readText(logFile).catch(() => "");
      const merged = (previous + chunk).split("\n").slice(-MAX_LINES).join("\n");
      await vein.file.writeText(logFile, merged);
    } catch (err) {
      vein.log(`写入日志失败：${err.message}`, "error");
    }
  };

  vein.mlc.on("game.log", (payload) => {
    const line = String(payload?.line ?? "");
    if (!line) return;
    buffer.push(line + "\n");
    if (!timer) {
      timer = setTimeout(async () => {
        timer = null;
        await flush();
      }, 5000);
    }
  });

  vein.mlc.on("game.exit", async (payload) => {
    await flush();
    vein.ui.notify("游戏已退出", `退出码 ${payload?.exit_code ?? "?"}，日志已保存`);
  });

  try {
    const info = await vein.mlc.worldInfo("1.20.4");
    vein.log(`当前存档数量：${(info.worlds || []).length}`);
  } catch (err) {
    vein.log(`读取存档失败：${err.message}`, "warn");
  }

  vein.log(`日志文件：${logFile}`);
}

export async function deactivate() {
  // 宿主会回收进程；这里保持无状态
}
