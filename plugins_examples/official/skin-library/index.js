/**
 * 皮肤下载 · LittleSkin —— 轻量版缺失的「皮肤页」用插件补回来
 *
 * 能力（manifest 里声明）：
 *   network.http     vein.http.getJson(url)        公开皮肤库列表 / 材质 hash
 *   download.queue   vein.download.queueTask()     下载皮肤 PNG
 *   file.read/write  读写插件自身文件（沙箱）
 *   skin.write       vein.skin.apply(accountId, path, model)  把 PNG 套到账号上
 *   accounts.read    vein.accounts.list()          选择目标账号
 *   ui.lua / ui.notify                             沙箱 UI 与通知
 *
 * 皮肤库接口（LittleSkin 公开站点）：
 *   GET /skinlib/list?filter=skin&page=N&keyword=...
 *   GET /texture/<tid>        → { hash }
 *   GET /textures/<hash>      → 皮肤 PNG
 */

const SITE = "https://littleskin.cn";
const PAGE_SIZE_HINT = 12;

let keyword = "";
let page = 1;
let items = [];
let accounts = [];
let accountId = "";
let status = "点「搜索」拉取公开皮肤库，或直接「换一批」看最新的。";
let busy = false;
let booted = false;

function safeName(raw) {
  return String(raw || "skin")
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, "_")
    .slice(0, 40);
}

function accountLabel() {
  if (!accounts.length) return "（无账号，仅能下载）";
  const hit = accounts.find((a) => a.id === accountId) || accounts[0];
  return `${hit.username}${hit.type === "littleskin" ? " · LittleSkin" : ""}`;
}

function itemRow(item) {
  const kind = (item.type === "slim" ? "纤细" : "经典") + (item.hd ? " · HD" : "");
  const buttons = {
    type: "row",
    props: { gap: 8 },
    children: [
      { type: "button", label: "下载", action: `dl:${item.tid}:${safeName(item.name)}` },
    ],
  };
  if (accounts.length) {
    buttons.children.push({
      type: "button",
      label: "应用",
      action: `apply:${item.tid}:${safeName(item.name)}:${item.type}`,
    });
  }
  const row = {
    type: "row",
    props: { card: true, column: true, gap: 6 },
    children: [
      {
        type: "image",
        src: `${SITE}/preview/${item.tid}`,
        alt: item.name,
        width: 120,
        height: 120,
        radius: 12,
        fit: "contain",
      },
      { type: "text", value: `${item.name}` },
      { type: "text", value: `${kind} · ♥ ${item.likes} · ${item.author}` },
      buttons,
    ],
  };
  return row;
}

function render() {
  const children = [
    { type: "text", value: `目标账号：${accountLabel()}` },
    { type: "text", value: status },
    {
      type: "row",
      children: [
        { type: "input", placeholder: "关键词（留空 = 最新）", action: "search" },
        { type: "button", label: "搜索", action: "search" },
        { type: "button", label: "换一批", action: "more" },
        { type: "button", label: "刷新账号", action: "accounts" },
      ],
    },
    { type: "divider" },
  ];

  if (!items.length) {
    children.push({ type: "text", value: "还没有结果。" });
  } else {
    children.push({ type: "text", value: `第 ${page} 页 · ${items.length} 条` });
    children.push({ type: "row", props: { grid: true }, children: items.map((item) => itemRow(item)) });
  }

  children.push({ type: "divider" });
  children.push({
    type: "text",
    value: "「下载」保存到插件 data/skins/；「应用」直接写入目标账号的皮肤。",
  });

  return { type: "panel", title: "皮肤下载 · LittleSkin", children };
}

async function fetchPage(vein, nextPage, kw) {
  let url = `${SITE}/skinlib/list?filter=skin&page=${nextPage}`;
  if (kw && kw.trim()) url += `&keyword=${encodeURIComponent(kw.trim())}`;
  const data = await vein.http.getJson(url);
  const list = Array.isArray(data?.data) ? data.data : [];
  return list
    .filter((raw) => raw && raw.tid != null)
    .map((raw) => ({
      tid: raw.tid,
      name: String(raw.name || `skin-${raw.tid}`),
      type: String(raw.type || "").toLowerCase() === "alex" ? "slim" : "classic",
      hd: Boolean(raw.hd),
      likes: Number(raw.likes || 0),
      author: String(raw.nickname || ""),
    }))
    .slice(0, PAGE_SIZE_HINT);
}

async function downloadSkin(vein, tid, name) {
  const meta = await vein.http.getJson(`${SITE}/texture/${tid}`);
  const hash = String(meta?.hash || "");
  if (!hash) throw new Error(`tid ${tid} 没有 hash`);
  const rel = `data/skins/${tid}-${safeName(name)}.png`;
  return vein.download.queueTask(`${SITE}/textures/${hash}`, rel);
}

async function loadAccounts(vein) {
  try {
    accounts = await vein.accounts.list();
  } catch (err) {
    accounts = [];
    vein.log(`读取账号失败：${err && err.message ? err.message : err}`, "warn");
  }
  accounts = Array.isArray(accounts) ? accounts : [];
  const selected = accounts.find((a) => a.selected);
  accountId = (selected && selected.id) || (accounts[0] && accounts[0].id) || "";
  return accounts;
}

/** 激活时跑一次端到端自检：列表 → hash → 下载 → （有账号时）应用到账号 */
async function selfTest(vein) {
  const report = { startedAt: new Date().toISOString(), steps: [], ok: false };
  const save = async () => {
    try {
      await vein.file.writeText("data/selftest.json", JSON.stringify(report, null, 2));
    } catch (err) {
      vein.log(`写自检报告失败：${err && err.message ? err.message : err}`, "error");
    }
  };
  const step = async (name, fn) => {
    const t0 = Date.now();
    try {
      const value = await fn();
      report.steps.push({ name, ok: true, ms: Date.now() - t0, value });
      await save();
      vein.log(`自检 · ${name} 通过（${Date.now() - t0} ms）`);
      return value;
    } catch (err) {
      report.steps.push({
        name,
        ok: false,
        ms: Date.now() - t0,
        error: err && err.message ? err.message : String(err),
      });
      await save();
      vein.log(`自检 · ${name} 失败：${report.steps.at(-1).error}`, "error");
      throw err;
    }
  };

  await save();
  const started = Date.now();
  try {
    await loadAccounts(vein);
    report.accounts = accounts.length;
    const list = await step("列表", () => fetchPage(vein, 1, ""));
    report.listCount = list.length;
    if (!list.length) throw new Error("列表为空");
    const first = list[0];
    report.first = { tid: first.tid, name: first.name };
    const meta = await step("材质 hash", () => vein.http.getJson(`${SITE}/texture/${first.tid}`));
    report.hash = String(meta?.hash || "").slice(0, 16);
    const saved = await step("下载 PNG", () => downloadSkin(vein, first.tid, first.name));
    report.saved = saved;

    const applyable = list.find((it) => !it.hd) || null;
    if (accounts.length && applyable) {
      report.applyTarget = { tid: applyable.tid, name: applyable.name, hd: applyable.hd };
      const rel = `data/skins/${applyable.tid}-${safeName(applyable.name)}.png`;
      if (applyable.tid !== first.tid) {
        await step("下载（应用目标）", () => downloadSkin(vein, applyable.tid, applyable.name));
      }
      const applied = await step("应用到账号", () => vein.skin.apply(accountId, rel, applyable.type));
      report.applied = applied;
    } else {
      report.steps.push({ name: "应用到账号", ok: true, skipped: "无账号" });
      vein.log("自检 · 应用到账号 跳过（当前没有账号）");
    }

    report.ok = true;
    report.totalMs = Date.now() - started;
    await save();
    await vein.ui.notify(
      "皮肤插件自检通过",
      `下载 #${first.tid}${accounts.length ? " 并已应用" : ""}，用时 ${report.totalMs} ms`
    );
  } catch (err) {
    report.ok = false;
    report.totalMs = Date.now() - started;
    await save();
  }
}

export async function activate(vein) {
  vein.log(`皮肤下载插件已激活，数据目录 ${vein.dataDir || "(未知)"}`);

  if (!booted) {
    booted = true;
    selfTest(vein);
  }

  vein.ui.onAction(async (action, payload) => {
    if (busy) return;
    busy = true;
    try {
      if (action === "refresh") {
        // 侧栏「皮肤」页进入时触发：重新拉一次账号与列表再渲染
        await loadAccounts(vein);
        if (!items.length) {
          items = await fetchPage(vein, page, keyword);
        }
        status = `已加载 ${items.length} 条，可直接下载${accounts.length ? "或应用" : ""}。`;
      } else if (action === "search") {
        keyword = (payload && payload.value) || "";
        page = 1;
        status = keyword ? `搜索「${keyword}」…` : "拉取最新…";
        await vein.ui.render(render());
        items = await fetchPage(vein, page, keyword);
        status = items.length ? `「${keyword || "最新"}」共 ${items.length} 条` : "没有结果，换个关键词试试。";
      } else if (action === "more") {
        page += 1;
        status = `加载第 ${page} 页…`;
        await vein.ui.render(render());
        items = await fetchPage(vein, page, keyword);
        if (!items.length) {
          page -= 1;
          status = "没有更多了。";
        } else {
          status = `第 ${page} 页 · ${items.length} 条`;
        }
      } else if (action === "accounts") {
        await loadAccounts(vein);
        status = accounts.length ? `已载入 ${accounts.length} 个账号` : "当前没有账号，只能下载不能应用。";
      } else if (action.startsWith("dl:")) {
        const [, tid, name] = action.split(":");
        status = `下载 #${tid} …`;
        await vein.ui.render(render());
        const saved = await downloadSkin(vein, tid, name);
        status = `已保存：${saved}`;
        await vein.ui.notify("皮肤已下载", String(saved));
      } else if (action.startsWith("apply:")) {
        const [, tid, name, model] = action.split(":");
        const target = items.find((it) => String(it.tid) === String(tid));
        if (target && target.hd) {
          throw new Error("这是 HD 皮肤（128×128），启动器只支持 64×64 / 64×32");
        }
        if (!accounts.length) throw new Error("没有账号可应用");
        status = `下载并应用 #${tid} …`;
        await vein.ui.render(render());
        const saved = await downloadSkin(vein, tid, name);
        const rel = String(saved).split("skins").pop();
        const applied = await vein.skin.apply(accountId, `data/skins${rel}`, model || "classic");
        status = `已应用到 ${accountLabel()}：${applied && applied.path ? applied.path : "ok"}`;
        await vein.ui.notify("皮肤已应用", accountLabel());
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

  try {
    await loadAccounts(vein);
    items = await fetchPage(vein, page, keyword);
    status = `已加载 ${items.length} 条，可直接下载${accounts.length ? "或应用" : ""}。`;
  } catch (err) {
    status = `列表加载失败：${err && err.message ? err.message : err}`;
  }
  await vein.ui.render(render());
}
