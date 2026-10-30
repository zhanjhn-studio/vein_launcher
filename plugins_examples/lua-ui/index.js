export async function activate(vein) {
  vein.log("LuaUI 示例已启动");

  vein.ui.onAction((action, payload) => {
    vein.log(`UI action: ${action} ${JSON.stringify(payload || {})}`);
  });

  try {
    await vein.ui.lua("./ui.lua");
    vein.log("LuaUI 已渲染");
  } catch (err) {
    vein.log(`LuaUI 渲染失败：${err.message}`, "error");
  }
}
