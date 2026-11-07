"""安装皮肤支持：为指定 MC 版本创建 Fabric 实例并装入 CustomSkinLoader。

用法：python tools/install_skin_support.py [1.20.1]
效果：生成 Fabric 实例（instances/fabric-loader-<loader>-<mc>），mods 里带 CustomSkinLoader，
      启动该实例后本地 PNG 皮肤与 LittleSkin 皮肤都能显示。
"""

from __future__ import annotations

import asyncio
import json
import ssl
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vein_launcher.application.services.loader_service import LoaderService  # noqa: E402
from vein_launcher.application.services.version_service import VersionService  # noqa: E402
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir  # noqa: E402

MODRINTH = "https://api.modrinth.com/v2"
PROJECT = "customskinloader"


async def fetch_json(session, url: str):
    import aiohttp

    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}: {url}")
            return await resp.json(content_type=None)
    except aiohttp.ClientSSLError:
        async with session.get(url, ssl=False) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}: {url}")
            return await resp.json(content_type=None)


async def fetch_bytes(session, url: str) -> bytes:
    import aiohttp

    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}: {url}")
            return await resp.read()
    except aiohttp.ClientSSLError:
        async with session.get(url, ssl=False) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}: {url}")
            return await resp.read()


def pick_file(version: dict) -> dict:
    files = version.get("files") or []
    for item in files:
        if item.get("primary"):
            return item
    if files:
        return files[0]
    raise RuntimeError("该版本没有可下载文件")


async def main() -> int:
    import aiohttp

    mc_version = sys.argv[1] if len(sys.argv) > 1 else "1.20.1"

    print(f"==> 安装 Fabric 加载器（{mc_version}）")
    service = LoaderService(VersionService())
    result = await service.install("fabric", mc_version)
    instance_id = str(result.get("version_id") or result.get("id") or "")
    if not instance_id:
        # LoaderService 返回里有 id 字段时优先用 id；都没有就按命名规则推断
        candidates = [p.name for p in (get_version_dir("x").parent).iterdir() if p.is_dir() and p.name.startswith("fabric-loader")]
        instance_id = sorted(candidates)[-1] if candidates else f"fabric-loader-{mc_version}"
    print(f"    实例：{instance_id}")

    query = json.dumps({"game_versions": [mc_version], "loaders": ["fabric"]})
    url = f"{MODRINTH}/project/{PROJECT}/version?game_versions={query}"

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as session:
        rows = await fetch_json(session, url) or []
        match = None
        for row in rows:
            if mc_version in (row.get("game_versions") or []) and "fabric" in (row.get("loaders") or []):
                match = row
                break
        if not match:
            raise RuntimeError(f"Modrinth 上没有适配 {mc_version}/fabric 的 CustomSkinLoader")

        payload = pick_file(match)
        print(f"==> 下载 {payload['filename']}（{payload.get('size', 0) / 1024:.0f} KB）")
        data = await fetch_bytes(session, payload["url"])

    mods = ensure_dir(get_version_dir(instance_id) / "mods")
    target = mods / payload["filename"]
    target.write_bytes(data)
    print(f"    已写入 {target}（{len(data) / 1024:.0f} KB）")

    print()
    print(f"皮肤支持安装完成：启动实例「{instance_id}」即可看到皮肤。")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
