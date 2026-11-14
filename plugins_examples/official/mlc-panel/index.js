/**
 * MLC 面板 · 轻量版的「MLC」页替代品
 *
 * 能力：mlc.state / mlc.world / mlc.player / versions.read / ui.lua
 *
 * 展示：MLC 总开关与 agent 状态、已装实例、选中实例的世界列表、玩家坐标
 * 注意：插件只能读状态；开总开关、发指令仍需在主程序里操作。
 */

let state = null;
let versions = [];
let worlds = [];
let player = null;
let status = "正在读取 MLC 状态…";
let versionId = "";
let busy = false;

function fmtPlayer(info) {
  if (!info) return "未取到玩家信息";
  const pos = info.position || info.pos || null;
  if (Array.isArray(pos) && pos.length >= 3) {
    return `坐标 ${pos.map((n) => Number(n).toFixed(1)).join(", ")}`;
  }
  if (pos && typeof pos === "object") {
    return `坐标 ${[pos.x, pos.y, pos.z].map((n) => Number(n).toFixed(1)).join(", ")}`;
  }
  return info.world ? `所在世界：${info.world}` : "已连接（无坐标）";
}

function render() {
  const enabled = state && (state.enabled === true || state.enabled === "on");
  const children = [
    { type: "text", value: `MLC 总开关：${enabled ? "已开启" : "未开启（需在主程序 MLC 页打开）"}` },
    { type: "text", value: `Agent：${state && state.connected ? "已连接" : "未连接"}` },
    { type: "text", value: status },
    {
      type: "row",
      children: [
        { type: "button", label: "刷新", action: "refresh" },
        { type: "input", placeholder: "实例 ID（留空 = 第一个）", action: "pick" },
      ],
    },
    { type: "divider" },
    { type: "text", value: `实例：${versions.length ? versions.join("、") : "（无）"}` },
  ];

  if (worlds.length) {
    children.push({ type: "text", value: `世界（${worlds.length}）` });
    worlds.slice(0, 12).forEach((w) => {
      const name = typeof w === "string" ? w : w.name || w.id || "?";
      children.push({ type: "text", value: `· ${name}` });
    });
  } else {
    children.push({ type: "text", value: "世界：未读取（选中实例后自动读取）" });
  }

  children.push({ type: "divider" });
  children.push({ type: "text", value: `玩家：${fmtPlayer(player)}` });

  return { type: "panel", title: "MLC 状态", children };
}

async function refresh(vein) {
  try {
    state = await vein.mlc.state();
  } catch (err) {
    state = null;
    status = `读取 MLC 状态失败：${err && err.message ? err.message : err}`;
  }

  try {
    const list = await vein.versions.list();
    versions = (list || []).map((v) => (typeof v === "string" ? v : v.id || v.version || "?"));
  } catch {
    versions = [];
  }

  if (!versionId) versionId = versions[0] || "";
  if (!versionId) {
    worlds = [];
    player = null;
    status = "还没有安装任何实例，先到「下载」页装一个版本。";
    return;
  }

  try {
    const info = await vein.mlc.worldInfo(versionId);
    const list = Array.isArray(info) ? info : info && Array.isArray(info.worlds) ? info.worlds : [];
    worlds = list;
  } catch (err) {
    worlds = [];
  }

  try {
    player = await vein.mlc.playerInfo(versionId);
  } catch {
    player = null;
  }

  status = `已读取实例 ${versionId} 的状态`;
}

export async function activate(vein) {
  vein.log("MLC 面板插件已激活");

  vein.ui.onAction(async (action, payload) => {
    if (busy) return;
    busy = true;
    try {
      if (action === "refresh") {
        await refresh(vein);
      } else if (action === "pick") {
        const value = String((payload && payload.value) || "").trim();
        if (value) {
          versionId = value;
          await refresh(vein);
        }
      }
    } catch (err) {
      status = `出错：${err && err.message ? err.message : err}`;
      vein.log(status, "error");
    } finally {
      busy = false;
      try {
        await vein.ui.render(render());
      } catch (err) {
        vein.log(`渲染失败：${err && err.message ? err.message : err}`, "error");
      }
    }
  });

  await refresh(vein);
  await vein.ui.render(render());
}
