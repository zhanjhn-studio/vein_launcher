-- LuaUI 示例：只使用受支持的声明式子集
-- 可用组件：panel / row / text / button / input / table / badge / image / divider

return ui.panel{
  title = "Lua UI sandbox",
  children = {
    ui.text{ value = "这段界面由插件用 Lua 声明，在 Shadow DOM 内渲染。" },
    ui.divider{},
    ui.row{
      children = {
        ui.button{ label = "Ping", action = "ping" },
        ui.badge{ value = "sandboxed" }
      }
    },
    ui.table{
      columns = { "能力", "状态" },
      rows = {
        { "ui.render", "ok" },
        { "ui.lua", "ok" },
        { "文件系统", "受限" }
      }
    }
  }
}
