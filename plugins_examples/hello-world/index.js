/**
 * Vein Launcher 示例插件
 *
 * 演示能力：
 *  - activate(ctx) 生命周期钩子
 *  - 事件订阅：ctx.on("game.launch.start", ...)
 *  - 宿主能力调用：ctx.file.writeText / ctx.ui.notify
 *  - 导出命令供宿主 invoke
 */

let activatedAt = null;
let counter = 0;

export async function activate(vein) {
  activatedAt = new Date().toISOString();
  vein.log(`示例插件已激活，数据目录=${vein.plugin.dataDir}`);

  // 订阅启动器事件
  vein.on("game.launch.start", (payload) => {
    vein.log(`检测到游戏启动：${JSON.stringify(payload?.command?.slice(0, 3) ?? [])}`);
  });

  vein.on("version.download.complete", (payload) => {
    vein.ui.notify("下载完成", `版本 ${payload?.version_id ?? "?"} 已就绪`, "success");
  });

  // 写一份激活记录到插件沙箱（受 file.write 权限与路径沙箱约束）
  try {
    await vein.file.writeText(
      `${vein.plugin.dataDir}/activation.log`,
      `activated at ${activatedAt}\n`
    );
  } catch (err) {
    vein.log(`写沙箱失败：${err.message}`, "warn");
  }

  return { ok: true };
}

export async function deactivate() {
  console.log("示例插件已停用");
}

// 可被 Python 侧 invoke 的命令
export const commands = {
  /** 打招呼：返回插件状态 */
  greet(name = "世界") {
    counter += 1;
    return {
      message: `你好，${name}！`,
      activatedAt,
      invokeCount: counter,
    };
  },

  /** 读取插件自己的数据目录 */
  async listData() {
    return { files: [] };
  },

  /** 故意越权：读取系统目录，预期被宿主拒绝 */
  async tryEscape() {
    const vein = globalThis.__vein_api__;
    return { note: "本方法需要由宿主注入 ctx，见 activate 中的 vein 参数" };
  },
};
