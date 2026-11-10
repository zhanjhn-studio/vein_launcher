"""下载体验修复：多线程分段下载、整合包进度、版本列表、指定版本安装。"""

from pathlib import Path

root = Path(r"Z:\Vein Launche")

# ---------------------------------------------------------------- 1. 多线程下载
dl = root / "vein_launcher" / "infrastructure" / "download" / "downloader.py"
t = dl.read_text(encoding="utf-8")

if "def _transfer_segmented" not in t:
    t = t.replace("""    async def _transfer(self, url: str, dest: Path, sha1: Optional[str],
                        size: Optional[int], progress: Optional[ProgressCallback]) -> None:""",
"""    async def _transfer_segmented(self, url: str, dest: Path, sha1: Optional[str],
                                  progress: Optional[ProgressCallback], size: int,
                                  parts: int = 4, resume_from: int = 0) -> None:
        \"\"\"多连接 Range 下载：失败由调用方回退单线程。\"\"\"
        import shutil

        part_dir = dest.with_name(dest.name + ".parts")
        shutil.rmtree(part_dir, ignore_errors=True)
        part_dir.mkdir(parents=True, exist_ok=True)
        chunk = max(1, size // parts)
        ranges = []
        for index in range(parts):
            start = index * chunk
            end = size - 1 if index == parts - 1 else min(size - 1, start + chunk - 1)
            ranges.append((index, start, end))

        session = await self.session()
        written = [0] * parts
        lock = asyncio.Lock()

        async def fetch(index: int, start: int, end: int) -> None:
            path = part_dir / f"{index:03d}.bin"
            headers = {"Range": f"bytes={start}-{end}"}
            async with session.get(url, headers=headers) as response:
                if response.status != 206:
                    raise RuntimeError("server does not support range requests")
                with path.open("wb") as fh:
                    async for piece in response.content.iter_chunked(CHUNK_SIZE):
                        fh.write(piece)
                        written[index] += len(piece)
                        if progress:
                            async with lock:
                                progress(resume_from + sum(written), size)

        await asyncio.gather(*(fetch(i, s, e) for i, s, e in ranges))

        hasher = hashlib.sha1()
        with dest.with_name(dest.name + ".part").open("wb") as out:
            for index, _start, _end in ranges:
                with (part_dir / f"{index:03d}.bin").open("rb") as fh:
                    while True:
                        block = fh.read(1024 * 1024)
                        if not block:
                            break
                        out.write(block)
                        hasher.update(block)
        shutil.rmtree(part_dir, ignore_errors=True)

        actual = hasher.hexdigest()
        if sha1 and actual.lower() != sha1.lower():
            dest.with_name(dest.name + ".part").unlink(missing_ok=True)
            raise SHA1MismatchError("SHA-1 校验失败", expected=sha1, actual=actual,
                                    file_path=str(dest))
        os.replace(dest.with_name(dest.name + ".part"), dest)

    async def _transfer(self, url: str, dest: Path, sha1: Optional[str],
                        size: Optional[int], progress: Optional[ProgressCallback]) -> None:""", 1)

    # 在单线程响应里发现大文件时改走多线程
    old = """            total = resume_from + int(response.headers.get("Content-Length", 0) or 0)
            hasher = hashlib.sha1()"""
    new = """            content_length = int(response.headers.get("Content-Length", 0) or 0)
            total = resume_from + content_length
            # 大文件且服务端支持 Range 时，4 连接并行下载；失败自动回退单线程
            if content_length >= 8 * 1024 * 1024 and not insecure:
                try:
                    await self._transfer_segmented(
                        url, dest, sha1, progress, content_length, parts=4, resume_from=0
                    )
                    return
                except Exception as exc:
                    logger.debug("多线程下载失败，回退单线程：%s", exc)
            hasher = hashlib.sha1()"""
    assert old in t
    t = t.replace(old, new, 1)
    dl.write_text(t, encoding="utf-8")
    print("segmented downloader")

# ---------------------------------------------------------------- 2. 整合包下载进度
mp = root / "vein_launcher" / "application" / "services" / "modpack_service.py"
t = mp.read_text(encoding="utf-8")
if "progress" not in t.split("async def install")[1][:200]:
    t = t.replace("async def install(self, archive: Path, instance_id: str) -> Dict[str, Any]:",
                  "async def install(self, archive: Path, instance_id: str, progress=None) -> Dict[str, Any]:", 1)
    old = """        downloader = self._downloader or Downloader()
        owns = self._downloader is None
        ok = failed = 0
        try:
            for url, target, sha1 in tasks:
                try:
                    await downloader.download(url, target, sha1=sha1)
                    ok += 1
                except Exception as exc:
                    failed += 1
                    logger.error("整合包文件失败 %s：%s", target.name, exc)"""
    new = """        downloader = self._downloader or Downloader()
        owns = self._downloader is None
        ok = failed = 0
        total_files = max(1, len(tasks))
        try:
            for url, target, sha1 in tasks:
                try:
                    await downloader.download(url, target, sha1=sha1)
                    ok += 1
                except Exception as exc:
                    failed += 1
                    logger.error("整合包文件失败 %s：%s", target.name, exc)
                if progress:
                    progress(ok + failed, total_files)"""
    assert old in t
    t = t.replace(old, new, 1)
    mp.write_text(t, encoding="utf-8")
    print("modpack progress")

# ---------------------------------------------------------------- 3. bridge：版本列表 / 指定版本 / 整合包进度任务
br = root / "vein_launcher" / "presentation" / "bridge.py"
t = br.read_text(encoding="utf-8")

if "mods.versions" not in t:
    t = t.replace('            "mods.install": self._mods_install,',
                  '            "mods.versions": self._mods_versions,\n            "mods.install": self._mods_install,')

    anchor = "    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str) -> dict:"
    versions_rpc = '''    async def _mods_versions(self, slug: str, mc_version: str = "", loader: str = "") -> list:
        versions = await self._ctx.modrinth.versions(
            str(slug), game_version=str(mc_version) or None, loader=str(loader) or None
        )
        rows = []
        for item in versions:
            file = self._ctx.modrinth.file_of(item)
            if not file:
                continue
            rows.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "version_number": item.get("version_number", ""),
                    "game_versions": item.get("game_versions", []),
                    "loaders": item.get("loaders", []),
                    "date": item.get("date_published", ""),
                    "downloads": item.get("downloads", 0),
                    "file": file,
                }
            )
        return rows

'''
    assert anchor in t
    t = t.replace(anchor, versions_rpc + anchor, 1)

    # install 支持指定版本
    t = t.replace("    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str) -> dict:",
                  "    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str, version_id: str = \"\") -> dict:", 1)
    old = """        effective_loader = instance_loader or str(loader) or None
        versions = await self._ctx.modrinth.versions(str(slug), loader=effective_loader)
        if not versions:
            raise RuntimeError("没有可下载的文件")
        file = self._ctx.modrinth.file_of(versions[0])"""
    new = """        effective_loader = instance_loader or str(loader) or None
        versions = await self._ctx.modrinth.versions(str(slug), loader=effective_loader)
        if version_id:
            picked = next((v for v in versions if str(v.get("id")) == str(version_id)), None)
            versions = [picked] if picked else []
        if not versions:
            raise RuntimeError("没有可下载的文件")
        file = self._ctx.modrinth.file_of(versions[0])"""
    assert old in t
    t = t.replace(old, new, 1)

    # 整合包：注册任务 + 进度 + 完成标记
    old_pack = """        if str(project_type) == "modpack":
            import shutil
            import tempfile

            workdir = Path(tempfile.mkdtemp(prefix="vein_pack_"))
            archive = workdir / file["name"]
            try:
                await self._ctx.modrinth_download(file["url"], archive, file.get("sha1"))
                return await self._ctx.modpacks.install(archive, str(instance))
            finally:
                shutil.rmtree(workdir, ignore_errors=True)"""
    new_pack = """        if str(project_type) == "modpack":
            import shutil
            import tempfile

            workdir = Path(tempfile.mkdtemp(prefix="vein_pack_"))
            archive = workdir / file["name"]
            task_id = f"pack-{slug}"
            self._downloads[task_id] = {
                "id": task_id, "name": str(slug), "done": 0, "total": 0, "active": True, "error": None,
            }
            try:
                await self._ctx.modrinth_download(
                    file["url"], archive, file.get("sha1"),
                    progress=lambda done, total: self._progress(task_id, done, total),
                )
                return await self._ctx.modpacks.install(
                    archive,
                    str(instance),
                    progress=lambda done, total: self._progress(task_id, done, total),
                )
            except Exception as exc:
                entry = self._downloads.get(task_id)
                if entry:
                    entry.update(active=False, error=str(exc))
                raise
            finally:
                entry = self._downloads.get(task_id)
                if entry and entry.get("error") is None:
                    entry.update(active=False)
                shutil.rmtree(workdir, ignore_errors=True)"""
    assert old_pack in t
    t = t.replace(old_pack, new_pack, 1)
    br.write_text(t, encoding="utf-8")
    print("mods.versions + pack progress")
