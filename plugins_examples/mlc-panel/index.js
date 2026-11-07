/**
 * Example plugin: MLC status panel.
 *
 * Shows what the MLC layer can do without a game-side mod:
 *   - mlc.state      → running / pid / uptime / last launched version
 *   - mlc.worldInfo  → saves with level.dat summary and player count
 *   - mlc.playerInfo → health / food / XP / position read from playerdata NBT
 *
 * Rendering goes through the sandboxed Lua UI tree (`vein.ui.render`), so the
 * panel cannot touch launcher DOM or styles.
 */

function badge(text, tone = "ok") {
  return { type: "badge", props: { value: String(text), tone } };
}

function text(value) {
  return { type: "text", props: { value: String(value) } };
}

function row(children) {
  return { type: "row", props: {}, children };
}

function table(columns, rows) {
  return { type: "table", props: { columns, rows } };
}

function fmtTime(seconds) {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function fmtSeed(seed) {
  if (seed === null || seed === undefined) return "—";
  return String(seed);
}

function buildPanel(state, worlds, player) {
  const running = Boolean(state?.running);
  const version = state?.version_id || (worlds[0]?.level?.version ?? "—");

  const children = [
    row([
      badge(running ? "running" : "stopped", running ? "ok" : "muted"),
      text(running ? `pid ${state.pid} · up ${fmtTime(state.uptime)}` : "no game process"),
    ]),
    text(`Version: ${version}`),
    { type: "divider", props: {} },
  ];

  if (worlds.length === 0) {
    children.push(text("No saves yet — create a world in game and it will show up here."));
  } else {
    children.push(
      table(
        ["World", "Day", "Seed", "Players"],
        worlds.slice(0, 5).map((world) => [
          world.name,
          String(world.level?.day ?? "—"),
          fmtSeed(world.level?.seed),
          String(world.players ?? 0),
        ]),
      ),
    );
  }

  children.push({ type: "divider", props: {} });

  if (player?.supported) {
    children.push(
      row([badge(player.world || "player", "info"), text(`${player.dimension || ""}`)]),
      table(
        ["Stat", "Value"],
        [
          ["Health", String(player.health ?? "—")],
          ["Food", String(player.food ?? "—")],
          ["XP level", String(player.xp_level ?? "—")],
          ["Position", (player.pos || []).map((n) => Math.round(n)).join(", ")],
          ["Inventory", `${player.inventory_slots ?? 0} slots`],
        ],
      ),
    );
  } else {
    children.push(text(player?.reason || "No player data yet."));
  }

  children.push(row([{ type: "button", props: { label: "Refresh", action: "refresh" } }]));

  return { type: "panel", props: { title: "MLC status" }, children };
}

export async function activate(vein) {
  const refresh = async () => {
    try {
      const state = await vein.mlc.state();
      const versionId = state?.version_id || "";
      const worldsPayload = await vein.mlc.worldInfo(versionId);
      const worlds = worldsPayload?.worlds || [];
      let player = { supported: false, reason: "No player data yet." };
      if (worlds.length > 0) {
        try {
          player = await vein.mlc.playerInfo(versionId, worlds[0].name);
        } catch (err) {
          player = { supported: false, reason: String(err.message || err) };
        }
      }
      await vein.ui.render(buildPanel(state, worlds, player));
    } catch (err) {
      vein.log(`MLC panel refresh failed: ${err.message}`, "error");
    }
  };

  vein.ui.onAction(async (action) => {
    if (action === "refresh") await refresh();
  });

  await refresh();
  vein.log("MLC status panel activated (manual refresh only)");
}

export async function deactivate() {
  // host disposes timers when the plugin process ends
}
