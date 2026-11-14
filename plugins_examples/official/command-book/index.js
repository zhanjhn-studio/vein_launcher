/**
 * 指令速查 · 轻量版的「工具」页替代品
 *
 * 数据：data/commands.json（6660 条，由全量版的 commandTree.ts 导出）
 * 能力：file.read（读数据）、system.clipboard（复制指令）、ui.lua（渲染面板）
 *
 * 用法：输入中文或英文关键词 → 列出匹配指令 → 点「复制」写进剪贴板
 */

const PAGE_SIZE = 30;

let all = [];
let keyword = "";
let page = 1;
let results = [];
let status = "正在载入指令库…";
let busy = false;

function match(item, kw) {
  if (!kw) return true;
  const k = kw.toLowerCase();
  return (
    String(item.token || "").toLowerCase().includes(k) ||
    String(item.hint || "").toLowerCase().includes(k) ||
    String(item.hintZh || "").toLowerCase().includes(k) ||
    String(item.parent || "").toLowerCase().includes(k)
  );
}

function fullCommand(item) {
  const parent = String(item.parent || "").trim();
  const token = String(item.token || "").trim();
  return ("/" + parent + (parent && token ? " " : "") + token).trim();
}

function row(item, index) {
  const cmd = fullCommand(item);
  const label = item.hintZh || item.hint || item.token;
  return {
    type: "row",
    props: { card: true, gap: 12, align: "center" },
    children: [
      { type: "text", value: `${String(index + 1).padStart(2, " ")}. ${label}` },
      { type: "text", value: cmd },
      { type: "button", label: "复制", action: `copy:${encodeURIComponent(cmd)}` },
    ],
  };
}

function render() {
  const children = [
    { type: "text", value: status },
    {
      type: "row",
      children: [
        { type: "input", placeholder: "关键词：中文名 / 英文名 / 指令前缀", action: "search" },
        { type: "button", label: "搜索", action: "search" },
        { type: "button", label: "下一页", action: "more" },
        { type: "button", label: "回到第 1 页", action: "reset" },
      ],
    },
    { type: "divider" },
  ];

  if (!results.length) {
    children.push({ type: "text", value: all.length ? "没有匹配的指令，换个关键词试试。" : "指令库还没载入。" });
  } else {
    const start = (page - 1) * PAGE_SIZE;
    const slice = results.slice(start, start + PAGE_SIZE);
    children.push({
      type: "text",
      value: `第 ${page} 页 / 共 ${Math.max(1, Math.ceil(results.length / PAGE_SIZE))} 页 · 匹配 ${results.length} 条`,
    });
    slice.forEach((item, i) => children.push(row(item, start + i)));
  }

  children.push({ type: "divider" });
  children.push({
    type: "text",
    value: "数据来自全量版指令树（6660 条候选 / 684 个前缀），支持中文名检索。",
  });

  return { type: "panel", title: "指令速查", children };
}

async function loadData(vein) {
  const raw = await vein.file.readText("data/commands.json");
  const parsed = JSON.parse(raw);
  all = Array.isArray(parsed) ? parsed : [];
  vein.log(`指令库已载入：${all.length} 条`);
}

function applySearch() {
  results = all.filter((item) => match(item, keyword));
  page = 1;
  status = keyword
    ? `「${keyword}」匹配 ${results.length} 条`
    : `共 ${all.length} 条指令，输入关键词检索`;
}

export async function activate(vein) {
  vein.log("指令速查插件已激活");
  try {
    await loadData(vein);
    applySearch();
    try {
      await vein.file.writeText("data/selftest.json", JSON.stringify({ ok: all.length > 0, count: all.length }));
    } catch (err) {
      vein.log(`自检报告写入失败（不影响使用）：${err && err.message ? err.message : err}`, "warn");
    }
  } catch (err) {
    status = `载入失败：${err && err.message ? err.message : err}`;
    vein.log(status, "error");
  }

  vein.ui.onAction(async (action, payload) => {
    if (busy) return;
    busy = true;
    try {
      if (action === "search") {
        keyword = (payload && payload.value) || "";
        applySearch();
      } else if (action === "more") {
        const max = Math.max(1, Math.ceil(results.length / PAGE_SIZE));
        page = page >= max ? 1 : page + 1;
      } else if (action === "reset") {
        page = 1;
      } else if (action === "refresh") {
        if (!all.length) await loadData(vein);
        applySearch();
      } else if (action.startsWith("copy:")) {
        const cmd = decodeURIComponent(action.slice(5));
        await vein.clipboard.write(cmd);
        status = `已复制：${cmd}`;
        await vein.ui.notify("指令已复制", cmd);
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

  await vein.ui.render(render());
}
