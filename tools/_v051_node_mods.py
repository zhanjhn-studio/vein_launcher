"""主程序：Node.js 检测/一键安装 + 原版实例装模组守卫。"""

from pathlib import Path

root = Path(r"Z:\Vein Launche")

# ---------------- 1. PluginHost 支持替换 node 路径
host = root / "vein_launcher" / "infrastructure" / "plugin_host" / "host.py"
t = host.read_text(encoding="utf-8")
if "def set_node" not in t:
    t = t.replace("""    @property
    def node_path(self) -> Optional[str]:
        return self._node""",
"""    @property
    def node_path(self) -> Optional[str]:
        return self._node

    def set_node(self, path: Optional[str]) -> None:
        self._node = path or shutil.which("node")""")
    host.write_text(t, encoding="utf-8")
    print("host.set_node added")

# ---------------- 2. PluginService：node 解析、状态、安装
svc = root / "vein_launcher" / "application" / "services" / "plugin_service.py"
t = svc.read_text(encoding="utf-8")

t = t.replace("self._host = PluginHost(self._registry)", "self._host = PluginHost(self._registry, node=self._resolve_node())")

if "def _resolve_node" not in t:
    helper = '''
    # ------------------------------------------------------------------ Node.js
    def _runtime_root(self) -> Path:
        return self._loader.root.parent

    def _node_candidates(self) -> list:
        candidates = [self._runtime_root() / "runtime" / "node" / "node.exe"]
        marker = self._runtime_root() / "config" / "runtime.json"
        try:
            import json as _json

            if marker.is_file():
                saved = _json.loads(marker.read_text(encoding="utf-8")).get("node", "")
                if saved:
                    candidates.insert(0, Path(saved))
        except Exception:
            pass
        return candidates

    def _resolve_node(self):
        import shutil

        for candidate in self._node_candidates():
            if candidate and Path(candidate).is_file():
                return str(candidate)
        return shutil.which("node")

    def node_status(self) -> dict:
        path = self._host.node_path
        version = ""
        if path:
            try:
                import subprocess

                version = subprocess.run(
                    [path, "-v"], capture_output=True, text=True, timeout=5
                ).stdout.strip()
            except Exception:
                version = ""
        return {
            "available": bool(path),
            "path": path or "",
            "version": version,
            "portable": bool(path and str(self._runtime_root() / "runtime" / "node") in path),
        }

    async def install_node(self, progress=None) -> dict:
        """下载 Node.js LTS（win-x64 zip）并解压到 runtime/node。"""
        import asyncio
        import io
        import json
        import os
        import zipfile

        import requests

        def emit(done: int, total: int) -> None:
            if progress:
                progress(done, total)

        def download() -> dict:
            target_dir = self._runtime_root() / "runtime" / "node"
            target_dir.mkdir(parents=True, exist_ok=True)
            if (target_dir / "node.exe").is_file():
                return {"path": str(target_dir / "node.exe"), "cached": True}

            index = requests.get(
                "https://nodejs.org/dist/latest-v20.x/SHASUMS256.txt", timeout=20
            )
            index.raise_for_status()
            name = ""
            for line in index.text.splitlines():
                if "win-x64.zip" in line:
                    name = line.split()[-1]
                    break
            if not name:
                raise RuntimeError("无法解析 Node.js 下载文件名")

            url = f"https://nodejs.org/dist/latest-v20.x/{name}"
            data = io.BytesIO()
            with requests.get(url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("Content-Length", "0") or 0)
                done = 0
                for chunk in resp.iter_content(256 * 1024):
                    if not chunk:
                        continue
                    data.write(chunk)
                    done += len(chunk)
                    emit(done, total)

            with zipfile.ZipFile(io.BytesIO(data.getvalue())) as zf:
                zf.extractall(target_dir)
            inner = next(target_dir.glob("node-v*-win-x64"))
            for item in inner.iterdir():
                os.replace(item, target_dir / item.name)
            inner.rmdir()

            marker = self._runtime_root() / "config" / "runtime.json"
            marker.parent.mkdir(parents=True, exist_ok=True)
            payload = {}
            if marker.is_file():
                try:
                    payload = json.loads(marker.read_text(encoding="utf-8"))
                except Exception:
                    payload = {}
            payload["node"] = str(target_dir / "node.exe")
            marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"path": str(target_dir / "node.exe"), "cached": False}

        result = await asyncio.to_thread(download)
        self._host.set_node(result["path"])
        try:
            await self._host.start()
        except Exception:
            pass
        logger.info("Node.js 已就绪：%s", result["path"])
        return {**result, "status": self.node_status()}
'''
    anchor = "    # ------------------------------------------------------------------\n    @property\n    def host(self) -> PluginHost:"
    assert anchor in t
    t = t.replace(anchor, helper + "\n" + anchor, 1)
    svc.write_text(t, encoding="utf-8")
    print("plugin_service node helpers added")

# ---------------- 3. bridge：RPC + 进度
br = root / "vein_launcher" / "presentation" / "bridge.py"
t = br.read_text(encoding="utf-8")
if "plugins.nodeStatus" not in t:
    t = t.replace('            "plugins.installExample": self._plugins_install_example,',
                  '            "plugins.installExample": self._plugins_install_example,\n'
                  '            "plugins.nodeStatus": self._plugins_node_status,\n'
                  '            "plugins.installNode": self._plugins_install_node,')
    anchor = "    async def _plugins_state(self) -> dict:"
    assert anchor in t
    t = t.replace(anchor, '''    async def _plugins_node_status(self) -> dict:
        return self._ctx.plugins.node_status()

    async def _plugins_install_node(self) -> dict:
        self._downloads["node-install"] = {
            "id": "node-install", "name": "Node.js", "done": 0, "total": 0, "active": True, "error": None,
        }
        try:
            result = await self._ctx.plugins.install_node(
                progress=lambda done, total: self._progress("node-install", done, total)
            )
        finally:
            entry = self._downloads.get("node-install")
            if entry:
                entry.update(active=False)
        return result

''' + anchor, 1)

    # 原版实例装 mod 守卫
    old = '''    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str) -> dict:
        versions = await self._ctx.modrinth.versions(str(slug), loader=str(loader) or None)'''
    new = '''    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str) -> dict:
        import re as _re

        instance_id = str(instance)
        has_loader = any(k in instance_id.lower() for k in ("fabric", "forge", "quilt", "neoforge"))
        if str(project_type) == "mod" and not has_loader and not loader:
            mc_version = _re.sub(r"^(fabric|forge|quilt|neoforge)-", "", instance_id, flags=_re.I)
            return {
                "needsLoader": True,
                "instance": instance_id,
                "mcVersion": mc_version,
                "suggestedLoader": "fabric",
            }

        versions = await self._ctx.modrinth.versions(str(slug), loader=str(loader) or None)'''
    assert old in t
    t = t.replace(old, new, 1)
    br.write_text(t, encoding="utf-8")
    print("bridge RPCs + mod guard")
