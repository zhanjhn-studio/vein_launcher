"""MLC + 插件系统端到端自检

覆盖：
  1. MLC 从 level.dat / playerdata NBT 读出世界与玩家数据（真实解析）
  2. 插件通过能力层 (mlc.state / mlc.world.info / mlc.player.info) 拿到同一份数据
  3. 插件用 ui.render 渲染出合法 UI 树

全部在临时目录内完成，不触碰用户数据。
运行：python tools/mlc_selftest.py
"""

from __future__ import annotations

import asyncio
import gzip
import io
import json
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import vein_launcher.mlc.service as mlc_service  # noqa: E402
from vein_launcher.infrastructure.plugin_host.capabilities import CapabilityRegistry  # noqa: E402
from vein_launcher.infrastructure.plugin_host.host import PluginHost  # noqa: E402
from vein_launcher.infrastructure.plugin_host.loader import (  # noqa: E402
    InstalledPlugin,
    PluginLoader,
)
from vein_launcher.mlc.service import MlcService  # noqa: E402

# --------------------------------------------------------------- 最小 NBT 写入


class Long(int):
    """TAG_Long 标记"""


class Float(float):
    """TAG_Float 标记"""


def _payload(value) -> bytes:
    if isinstance(value, Long):
        return b"\x04" + struct.pack(">q", int(value))
    if isinstance(value, Float):
        return b"\x05" + struct.pack(">f", float(value))
    if isinstance(value, bool):
        return b"\x01" + struct.pack(">b", int(value))
    if isinstance(value, int):
        return b"\x03" + struct.pack(">i", value)
    if isinstance(value, str):
        raw = value.encode("utf-8")
        return b"\x08" + struct.pack(">H", len(raw)) + raw
    if isinstance(value, dict):
        return b"\x0a" + _compound(value)
    if isinstance(value, list):
        if not value:
            return b"\x09\x00" + struct.pack(">i", 0)
        first = _payload(value[0])
        tag = first[0]
        body = b"".join(_payload(item)[1:] for item in value)
        return b"\x09" + bytes([tag]) + struct.pack(">i", len(value)) + body
    raise TypeError(f"unsupported NBT value: {type(value)}")


def _compound(data: dict) -> bytes:
    out = b""
    for key, value in data.items():
        raw = _payload(value)
        out += raw[:1] + struct.pack(">H", len(key)) + key.encode("utf-8") + raw[1:]
    return out + b"\x00"


def write_nbt(path: Path, data: dict) -> None:
    payload = b"\x0a" + struct.pack(">H", 0) + _compound(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb") as gz:
            gz.write(payload)


# --------------------------------------------------------------- 自检主体


async def run() -> int:
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="vein-mlc-") as tmp:
        base = Path(tmp)
        version_dir = base / "instances" / "1.20.1"
        world_dir = version_dir / "saves" / "TestWorld"
        player_id = "a01e3843-e521-5998-558a-f459800e4d11"

        write_nbt(
            world_dir / "level.dat",
            {
                "Data": {
                    "LevelName": "TestWorld",
                    "RandomSeed": Long(123456789),
                    "Difficulty": 2,
                    "GameType": 1,
                    "LastPlayed": Long(1794023638888),
                    "Version": {"Name": "1.20.1"},
                }
            },
        )
        write_nbt(
            world_dir / "playerdata" / f"{player_id}.dat",
            {
                "Health": Float(18.5),
                "foodLevel": 17,
                "XpLevel": 7,
                "playerGameType": 1,
                "Dimension": "minecraft:overworld",
                "Pos": [Float(12.5), Float(70.0), Float(-3.25)],
                "Inventory": [{"Slot": 0}],
            },
        )

        # 让 MLC 认为数据根就在临时目录
        mlc_service.get_version_dir = lambda version_id: base / "instances" / version_id

        class FakeProcess:
            running = False
            _process = None

        class FakeLauncher:
            _process = FakeProcess()

        service = MlcService(FakeLauncher(), plugins_dir=base / "plugins")
        print("== MLC 数据解析 ==")
        state = service.state()
        check("状态可读", state["running"] is False, json.dumps(state, ensure_ascii=False))

        worlds = service.world_info("1.20.1")["worlds"]
        check("存档被识别", len(worlds) == 1, worlds[0]["name"] if worlds else "none")
        check("level.dat 摘要", worlds and worlds[0]["level"]["seed"] == 123456789,
              json.dumps(worlds[0].get("level"), ensure_ascii=False) if worlds else "")
        check("玩家数量统计", worlds and worlds[0]["players"] == 1)

        player = service.player_info("1.20.1", "TestWorld")
        check("玩家数据可读", player.get("supported") is True, json.dumps(player, ensure_ascii=False))
        check("血量/食物正确", player.get("health") == 18.5 and player.get("food") == 17)
        check("坐标解析正确", [round(v, 1) for v in player.get("pos", [])] == [12.5, 70.0, -3.2])

        detail = service.world_detail("1.20.1", "TestWorld")
        check("存档详情含玩家", detail.get("player", {}).get("supported") is True)

        print("== 插件走能力层 ==")
        plugins_root = base / "plugins"
        plugin_dir = plugins_root / "mlc-probe"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "package.json").write_text(
            json.dumps(
                {
                    "name": "mlc-probe",
                    "version": "0.0.1",
                    "type": "module",
                    "main": "index.js",
                    "vein": {
                        "displayName": "mlc-probe",
                        "permissions": ["mlc.state", "mlc.world", "mlc.player", "ui.lua"],
                    },
                }
            ),
            encoding="utf-8",
        )
        (plugin_dir / "index.js").write_text(
            """
export async function activate(vein) {
  const state = await vein.mlc.state();
  const worlds = await vein.mlc.worldInfo(state.version_id || "1.20.1");
  const player = await vein.mlc.playerInfo(state.version_id || "1.20.1", worlds.worlds[0].name);
  await vein.ui.render({
    type: "panel",
    props: { title: "probe" },
    children: [
      { type: "text", props: { value: "worlds=" + worlds.worlds.length } },
      { type: "table", props: { columns: ["k", "v"], rows: [
        ["world", worlds.worlds[0].name],
        ["health", String(player.health)],
      ] } },
    ],
  });
  vein.log("PROBE_OK health=" + player.health);
}
export function deactivate() {}
""",
            encoding="utf-8",
        )

        registry = CapabilityRegistry(allowed_roots=[plugins_root, plugin_dir])
        rendered: list[dict] = []

        async def mlc_state(plugin_id: str):
            return service.state()

        async def mlc_worlds(plugin_id: str, version_id: str = ""):
            return service.world_info(version_id or "1.20.1")

        async def mlc_player(plugin_id: str, version_id: str = "", world: str = ""):
            return service.player_info(version_id or "1.20.1", world)

        async def ui_render(plugin_id: str, tree: dict):
            rendered.append(tree)
            return True

        registry.register("mlc.state", "mlc.state", mlc_state)
        registry.register("mlc.world.info", "mlc.world", mlc_worlds)
        registry.register("mlc.player.info", "mlc.player", mlc_player)
        registry.register("ui.render", "ui.lua", ui_render)

        host = PluginHost(registry)
        plugin = InstalledPlugin(PluginLoader.parse_manifest(plugin_dir), plugin_dir)
        await host.start()
        await host.load(plugin)
        await asyncio.sleep(1.2)

        logs = "\n".join(host.recent_logs(80))
        check("插件加载并调用 MLC", "PROBE_OK health=18.5" in logs,
              logs.split("PROBE_OK")[-1].split("\n")[0][:60] if "PROBE_OK" in logs else logs[-160:])
        check("插件拿到 UI 树", len(rendered) == 1,
              json.dumps(rendered[0], ensure_ascii=False)[:160] if rendered else "none")

        await host.unload("mlc-probe")
        await host.stop()
        check("宿主正常关闭", not host.running)

    print()
    if failures:
        print(f"自检失败 {len(failures)} 项：{', '.join(failures)}")
        return 1
    print("MLC + 插件自检全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
