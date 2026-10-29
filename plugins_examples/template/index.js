/**
 * Vein 插件模板
 *
 * 复制本目录到 %APPDATA%\VeinLauncher\plugins\<包名> 即可被加载。
 * package.json 的 vein.permissions 声明你要用的能力，未声明会被拒绝。
 */

export async function activate(vein) {
  vein.log(`插件模板已激活：${vein.plugin.displayName} v${vein.plugin.version}`);
  vein.log(`数据目录：${vein.plugin.dataDir}`);

  // 可用能力示例（需要对应权限）
  // await vein.config.get()
  // await vein.file.writeText(`${vein.plugin.dataDir}/hello.txt`, "hello")
  // await vein.mlc.worldInfo("1.20.4")
  // vein.mlc.on("game.log", (p) => vein.log(p.line))

  vein.log("插件模板就绪");
}

export function deactivate() {
  // 插件被禁用或宿主关闭时调用
}
