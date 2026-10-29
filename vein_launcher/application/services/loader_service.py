"""应用层 - 加载器服务（Fabric / Quilt / Forge / NeoForge）

Fabric / Quilt：读取 Meta API 的安装 profile，落成本地版本 JSON。
Forge / NeoForge：下载官方 installer，用 Java 以 --installClient 运行，
再把生成的版本 JSON 导入实例目录。
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.application.services.version_service import VersionService
from vein_launcher.common.exceptions import VeinError
from vein_launcher.common.utils.path_utils import ensure_dir, get_version_dir
from vein_launcher.infrastructure.network.http_client import HttpClient, HttpClientError
from vein_launcher.infrastructure.process.java_detector import JavaDetector

logger = logging.getLogger(__name__)

FABRIC_META = "https://meta.fabricmc.net/v2"
QUILT_META = "https://meta.quiltmc.org/v3"
FORGE_PROMOS = "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
NEOFORGE_MAVEN = (
    "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
)
FORGE_MAVEN = "https://maven.minecraftforge.net/net/minecraftforge/forge"

LOADERS = ("fabric", "quilt", "forge", "neoforge")


class LoaderService:
    """加载器安装"""

    def __init__(
        self,
        versions: VersionService,
        http: Optional[HttpClient] = None,
        detector: Optional[JavaDetector] = None,
    ):
        self._versions = versions
        self._http = http or HttpClient()
        self._detector = detector or JavaDetector()

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    async def install(
        self, loader: str, mc_version: str, loader_version: Optional[str] = None
    ) -> Dict[str, Any]:
        loader = loader.lower()
        if loader not in LOADERS:
            raise VeinError(f"不支持的加载器：{loader}")

        # 先确保原版本体已安装
        await self._versions.install(mc_version)

        if loader in ("fabric", "quilt"):
            return await self._install_meta_loader(loader, mc_version, loader_version)
        return await self._install_forge_like(loader, mc_version, loader_version)

    # ------------------------------------------------------------------
    async def _install_meta_loader(
        self, loader: str, mc_version: str, loader_version: Optional[str]
    ) -> Dict[str, Any]:
        base = FABRIC_META if loader == "fabric" else QUILT_META
        versions = await self._http.get_json(f"{base}/versions/loader/{mc_version}")
        if not versions:
            raise VeinError(f"{loader} 没有适配 {mc_version} 的版本")

        if loader_version:
            matched = [v for v in versions if v.get("loader", {}).get("version") == loader_version]
            chosen = matched[0] if matched else None
        else:
            stable = [v for v in versions if v.get("loader", {}).get("stable")]
            chosen = (stable or versions)[0]
        if chosen is None:
            raise VeinError(f"未找到加载器版本 {loader_version}")

        lv = chosen["loader"]["version"]
        profile = await self._http.get_json(
            f"{base}/versions/loader/{mc_version}/{lv}/profile/json"
        )

        version_id = f"{loader}-{mc_version}"
        profile["id"] = version_id
        profile["inheritsFrom"] = mc_version

        target = ensure_dir(get_version_dir(version_id)) / f"{version_id}.json"
        target.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("%s 安装完成：%s（loader %s）", loader, version_id, lv)
        return {"version_id": version_id, "loader": loader, "loader_version": lv}

    # ------------------------------------------------------------------
    async def _install_forge_like(
        self, loader: str, mc_version: str, loader_version: Optional[str]
    ) -> Dict[str, Any]:
        if loader == "forge":
            full = await self._resolve_forge(mc_version, loader_version)
            artifact = f"{full}/forge-{full}-installer.jar"
            base = FORGE_MAVEN
        else:
            full = await self._resolve_neoforge(mc_version, loader_version)
            artifact = f"{full}/neoforge-{full}-installer.jar"
            base = "https://maven.neoforged.net/releases/net/neoforged/neoforge"

        java = await self._detector.select(8)
        if java is None:
            raise VeinError("安装 Forge 需要本机 Java")

        work = Path(tempfile.mkdtemp(prefix="vein_forge_"))
        installer = work / "installer.jar"
        (work / "launcher_profiles.json").write_text(
            json.dumps({"profiles": {}, "settings": {}, "version": 3}), encoding="utf-8"
        )

        url = f"{base}/{artifact}"
        await self._download(url, installer)

        proc = await asyncio.create_subprocess_exec(
            str(java.path), "-jar", str(installer), "--installClient",
            cwd=str(work),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        log = out.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            shutil.rmtree(work, ignore_errors=True)
            raise VeinError(f"{loader} 安装器失败：{log[-400:]}")

        produced = sorted((work / "versions").glob("*/*.json")) if (work / "versions").is_dir() else []
        if not produced:
            shutil.rmtree(work, ignore_errors=True)
            raise VeinError(f"{loader} 安装器未生成版本 JSON")

        version_id = f"{loader}-{mc_version}"
        target_dir = ensure_dir(get_version_dir(version_id))
        data = json.loads(produced[0].read_text(encoding="utf-8"))
        data["id"] = version_id
        (target_dir / f"{version_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        shutil.rmtree(work, ignore_errors=True)
        logger.info("%s 安装完成：%s", loader, version_id)
        return {"version_id": version_id, "loader": loader, "loader_version": full}

    # ------------------------------------------------------------------
    async def _resolve_forge(self, mc_version: str, version: Optional[str]) -> str:
        if version:
            return version if version.startswith(mc_version) else f"{mc_version}-{version}"
        data = await self._http.get_json(FORGE_PROMOS)
        promos = data.get("promos", {})
        for key in (f"{mc_version}-recommended", f"{mc_version}-latest"):
            if key in promos:
                return f"{mc_version}-{promos[key]}"
        raise VeinError(f"Forge 没有 {mc_version} 的安装版本")

    async def _resolve_neoforge(self, mc_version: str, version: Optional[str]) -> str:
        if version:
            return version
        xml = await self._http.get_text(NEOFORGE_MAVEN)
        import re

        all_versions = re.findall(r"<version>([^<]+)</version>", xml)
        # NeoForge 版本号形如 21.1.77，主版本对应 MC 1.21.1
        prefix = mc_version.replace("1.", "")
        matched = [v for v in all_versions if v.startswith(prefix + ".")]
        if not matched:
            raise VeinError(f"NeoForge 没有 {mc_version} 的版本")
        return matched[-1]

    async def _download(self, url: str, dest: Path) -> None:
        session = await self._http.session()
        async with session.get(url) as response:
            if response.status != 200:
                raise HttpClientError(f"HTTP {response.status}", url=url, status=response.status)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as fh:
                async for chunk in response.content.iter_chunked(64 * 1024):
                    fh.write(chunk)


__all__ = ["LoaderService", "LOADERS"]
