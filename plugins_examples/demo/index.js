/**
 * Vein Launcher 插件 demo
 *
 * 验证：
 * 1. 加载后调用宿主能力（config.read / file.writeText / mlc.world.info）
 * 2. 订阅 MLC 事件（mlc.game.log / mlc.game.exit）
 * 3. 越权路径会被宿主拒绝
 */

export async function activate(vein) {
  vein.log("demo 插件已激活");

  // 读取配置（宿主能力）
  try {
    const config = await vein.config.get();
    vein.log(`拿到配置，键：${Object.keys(config).join(",")}`);
  } catch (err) {
    vein.log(`读取配置失败：${err.message}`, "warn");
  }

  // 写入自己的沙箱目录
  try {
    await vein.file.writeText(
      `${vein.plugin.dataDir}/activation.log`,
      `activated at ${new Date().toISOString()}\n`
    );
    vein.log("已写入 data/activation.log");
  } catch (err) {
    vein.log(`写入沙箱失败：${err.message}`, "error");
  }

  // 查询最近启动实例的存档（MLC 能力）
  try {
    const info = await vein.mlc.worldInfo("1.20.4");
    vein.log(`MLC world.info：${(info.worlds || []).length} 个存档`);
  } catch (err) {
    vein.log(`MLC 调用失败：${err.message}`, "warn");
  }

  // 越权访问应当被拒绝
  try {
    await vein.file.readText("C:/Windows/win.ini");
    vein.log("越权竟然成功了（不应发生）", "error");
  } catch (err) {
    vein.log(`越权被拒绝：${err.message}`);
  }

  // 订阅 MLC 事件
  vein.mlc.on("game.log", (payload) => {
    const line = String(payload?.line ?? "");
    if (line) vein.log(`[game] ${line.slice(0, 120)}`);
  });

  vein.mlc.on("game.exit", (payload) => {
    vein.ui.notify("游戏已退出", `退出码 ${payload?.exit_code ?? "?"}`);
  });

  vein.log("demo 插件就绪");
}
