/**
 * Vein 插件模板
 *
 * 复制本目录到 %APPDATA%\VeinLauncher\plugins\<包名> 即可被加载。
 * package.json 的 vein.permissions 声明你要用的能力，未声明会被拒绝。
 */

export async function activate(vein) {
  vein.log(`插件模板已激活：${vein.plugin.displayName} v${vein.plugin.version}`);
  vein.log(`数据目录：${vein.plugin.dataDir}`);

  // 可用能力示例（需要 package.json 的 vein.permissions 先声明）
  // 文件操作只能写插件自己的 data/ 目录，越界路径会被宿主拒绝：
  // await vein.file.writeText("notes.txt", "hello")
  // await vein.config.get()
  // await vein.mlc.worldInfo("1.20.4")
  // vein.mlc.on("game.log", (p) => vein.log(p.line))
  // 跳转到主界面的某个页面（下载 / 实例 / 设置 …）：
  // await vein.ui.openPage("download")

  vein.log("插件模板就绪");
}

export function deactivate() {
  // 插件被禁用或宿主关闭时调用
}
