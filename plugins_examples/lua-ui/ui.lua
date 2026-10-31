-- LuaUI sample: declarative subset only
-- Components: panel / row / text / button / input / table / badge / image / divider

return ui.panel{
  title = "Lua UI sandbox",
  children = {
    ui.text{ value = "This panel is declared in Lua and rendered inside a closed Shadow DOM." },
    ui.divider{},
    ui.row{
      children = {
        ui.button{ label = "Ping", action = "ping" },
        ui.badge{ value = "sandboxed" }
      }
    },
    ui.table{
      columns = { "Capability", "Status" },
      rows = {
        { "ui.render", "ok" },
        { "ui.lua", "ok" },
        { "file system", "sandboxed" }
      }
    }
  }
}
