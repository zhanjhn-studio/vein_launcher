"""插件宿主端到端自检：加载示例 → 能力调用 → 权限/路径拦截。

运行：python tools/plugin_selftest.py
不修改用户数据目录，全部在临时目录内完成。
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vein_launcher.infrastructure.plugin_host.capabilities import (  # noqa: E402
    CapabilityRegistry,
    CapabilityTimeoutError,
    PluginPermissionError,
)
from vein_launcher.infrastructure.plugin_host.host import PluginHost  # noqa: E402
from vein_launcher.infrastructure.plugin_host.loader import (  # noqa: E402
    InstalledPlugin,
    PluginLoader,
)

EXAMPLES = ROOT / "plugins_examples"


def build_manifest(name: str, perms: list[str], desc: str = "") -> dict:
    return {
        "name": name,
        "version": "0.0.1",
        "type": "module",
        "main": "index.js",
        "vein": {"displayName": name, "permissions": perms},
        "description": desc,
    }


async def run() -> int:
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="vein-plugin-test-") as tmp:
        root = Path(tmp) / "plugins"
        root.mkdir(parents=True)

        # --- 造一个带完整能力的测试插件 ---
        plugin_dir = root / "selftest"
        plugin_dir.mkdir()
        (plugin_dir / "package.json").write_text(
            json.dumps(build_manifest("selftest", ["file.read", "file.write", "ui.notify", "ui.open_page"])),
            encoding="utf-8",
        )
        (plugin_dir / "index.js").write_text(
            """
export async function activate(vein) {
  await vein.file.writeText("hello.txt", "vein-ok");
  const text = await vein.file.readText("hello.txt");
  await vein.ui.notify("selftest", "activate done:" + text);
  await vein.ui.openPage("download");
  let escapeErr = "";
  try { await vein.file.readText("../../../escape.txt"); }
  catch (e) { escapeErr = String(e.message || e); }
  let permErr = "";
  try { await vein.http.getJson("https://example.com"); }
  catch (e) { permErr = String(e.message || e); }
  vein.log("ESCAPE_ERR=" + escapeErr);
  vein.log("PERM_ERR=" + permErr);
}
export function deactivate() {}
""",
            encoding="utf-8",
        )

        registry = CapabilityRegistry(allowed_roots=[root])
        registry.add_root(plugin_dir)

        async def read_text(plugin_id: str, path: str) -> str:
            target = registry.check_path(str(plugin_dir / path))
            return target.read_text(encoding="utf-8")

        async def write_text(plugin_id: str, path: str, content: str) -> bool:
            target = registry.check_path(str(plugin_dir / path))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return True

        registry.register("file.readText", "file.read", read_text)
        registry.register("file.writeText", "file.write", write_text)

        opened_pages: list[str] = []

        async def ui_notify(plugin_id: str, title: str, message: str) -> bool:
            print(f"    [notify] {title}: {message}")
            return True

        async def ui_open_page(plugin_id: str, page: str) -> bool:
            opened_pages.append(str(page))
            return True

        registry.register("ui.notify", "ui.notify", ui_notify)
        registry.register("ui.openPage", "ui.open_page", ui_open_page)

        async def slow(plugin_id: str) -> str:
            await asyncio.sleep(5)
            return "never"

        registry.register("slow.op", "file.read", slow, timeout=0.2)

        host = PluginHost(registry)
        plugin = InstalledPlugin(PluginLoader.parse_manifest(plugin_dir), plugin_dir)

        print("== 宿主启动 ==")
        await host.start()
        check("宿主运行中", host.running, f"pid={host.pid}")

        print("== 加载插件 ==")
        await host.load(plugin)
        await asyncio.sleep(0.6)
        check("插件已加载", "selftest" in host._plugins)

        print("== 能力结果 ==")
        written = (plugin_dir / "hello.txt")
        check("沙箱内写入成功", written.is_file(), written.read_text(encoding="utf-8") if written.is_file() else "")

        logs = "\n".join(host.recent_logs(60))
        check(
            "越权路径被拒绝",
            "ESCAPE_ERR=" in logs and "越权" in logs,
            logs.split("ESCAPE_ERR=")[-1].split("\n")[0][:80] if "ESCAPE_ERR=" in logs else "无日志",
        )
        # Node 侧 guard() 在发往 Python 之前就拦下了未声明权限的调用，
        # 插件把捕获到的错误写进自身日志，据此确认拦截确实发生。
        check(
            "未声明权限被 Node 侧拦截",
            "PERM_ERR=" in logs and "未声明权限" in logs.split("PERM_ERR=")[-1].split("\n")[0],
            logs.split("PERM_ERR=")[-1].split("\n")[0][:80] if "PERM_ERR=" in logs else "无日志",
        )

        print("== 能力层拦截 ==")
        try:
            await registry.execute("selftest", ["file.read"], "file.writeText", ["x.txt", "1"])
            check("权限不足应抛错", False)
        except PluginPermissionError:
            check("权限不足抛 PluginPermissionError", True)

        try:
            await registry.execute("selftest", ["file.read"], "slow.op", [])
            check("超时应抛错", False)
        except CapabilityTimeoutError as exc:
            check("超时抛 CapabilityTimeoutError", True, str(exc))

        print("== 卸载与关闭 ==")
        await host.unload("selftest")
        check("插件已卸载", "selftest" not in host._plugins)
        await host.stop()
        check("宿主已停止", not host.running)

    print()
    if failures:
        print(f"自检失败 {len(failures)} 项：{', '.join(failures)}")
        return 1
    print("插件自检全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))