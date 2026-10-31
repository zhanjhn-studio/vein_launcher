export async function activate(vein) {
  vein.log("LuaUI sample activated");

  vein.ui.onAction((action, payload) => {
    vein.log(`UI action: ${action} ${JSON.stringify(payload || {})}`);
  });

  try {
    await vein.ui.lua("./ui.lua");
    vein.log("LuaUI rendered");
  } catch (err) {
    vein.log(`LuaUI failed: ${err.message}`, "error");
  }
}
