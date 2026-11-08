/**
 * Example plugin: status panel.
 *
 * Demonstrates the capabilities added for plugin authors:
 *   vein.app.info()      → launcher version + data directory
 *   vein.versions.list() → installed instances
 *   vein.game.running()  → live games (including ones started outside the launcher)
 *   vein.mlc.state()     → MLC master switch + agent state
 *   vein.mlc.on(...)     → MLC events (game.enter / game.leave / dimension / death)
 *
 * Rendering uses the sandboxed UI tree; nothing touches launcher DOM.
 */

function text(value) {
  return { type: "text", value: String(value) };
}

function badge(value, tone) {
  return { type: "badge", value: String(value), tone: tone || "ok" };
}

function row(children) {
  return { type: "row", children };
}

function table(columns, rows) {
  return { type: "table", columns, rows };
}

export async function activate(vein) {
  let lastState = null;

  const refresh = async () => {
    const [info, versions, running, mlc] = await Promise.all([
      vein.app.info().catch(() => ({ version: "?", dataDir: "?" })),
      vein.versions.list().catch(() => []),
      vein.game.running().catch(() => ({ games: [] })),
      vein.mlc.state().catch(() => ({ enabled: false })),
    ]);

    const games = running.games || [];
    const enabled = Boolean(mlc && mlc.enabled);
    lastState = mlc;

    const instanceRows = (versions || []).slice(0, 8).map((item) => [
      item.id || item.version_id || "?",
      item.type || "release",
    ]);

    await vein.ui.render({
      type: "panel",
      title: "Status",
      children: [
        row([
          badge(`v${info.version}`, "info"),
          badge(`${(versions || []).length} instances`, "muted"),
          badge(`${games.length} running`, games.length ? "ok" : "muted"),
          badge(enabled ? "MLC on" : "MLC off", enabled ? "ok" : "warn"),
        ]),
        text(`Data: ${info.dataDir}`),
        { type: "divider" },
        table(["Instance", "Type"], instanceRows.length ? instanceRows : [["—", "none"]]),
        { type: "divider" },
        table(
          ["Running game", "Version", "PID", "Memory"],
          games.length
            ? games.map((game) => [
                game.source === "launcher" ? "launcher" : "external",
                game.version_id || "?",
                String(game.pid),
                game.memory_mb ? `${game.memory_mb} MB` : "—",
              ])
            : [["no game", "—", "—", "—"]],
        ),
        row([{ type: "button", label: "Refresh", action: "refresh" }]),
      ],
    });
  };

  vein.ui.onAction(async (action) => {
    if (action === "refresh") await refresh();
  });

  vein.mlc.on("game.enter", async () => {
    await vein.ui.notify("进入世界", "MLC 检测到游戏已进入世界");
    await refresh();
  });
  vein.mlc.on("game.leave", async () => {
    await vein.ui.notify("离开世界", "MLC 检测到游戏已退回菜单");
    await refresh();
  });

  await refresh();
  vein.log("status-panel ready");
}

export async function deactivate() {
  // nothing to clean up; the host stops this process
}
