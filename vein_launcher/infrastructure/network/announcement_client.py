"""公告与更新数据源（zhanjhn.github.io Pages 静态资源）

约定 schema（兼容 JS 变量包裹）：
{
  "version": "0.0.3",
  "min_version": "0.0.2",           # 低于该版本强制更新
  "announcements": [
    {"id": "...", "level": "light|heavy", "title": "...", "content": "...", "url": "..."}
  ],
  "update": {"version": "0.0.3", "url": "https://...", "notes": "..."}
}

源站不可达时返回缓存（TTL 1 小时），再不行返回空结构，绝不阻塞启动。
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.infrastructure.network.http_client import HttpClient

logger = logging.getLogger(__name__)

SOURCES = (
    "https://zhanjhn.github.io/vl/public.js",
    "https://zhanjhn.github.io/public.js",
    "https://zhanjhn.github.io/announcement.json",
)
CACHE_TTL = 3600

_JS_VAR = re.compile(r"=\s*(\{.*\})\s*;?\s*$", re.S)


def _parse_payload(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # window.X = {...}; / var X = {...};
    match = _JS_VAR.search(text)
    candidate = match.group(1) if match else text[text.find("{"):]
    candidate = candidate.rstrip(";").strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # 去掉尾逗号再试一次
        cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None


class AnnouncementClient:
    def __init__(self, cache_file: Path, http: Optional[HttpClient] = None):
        self._cache_file = cache_file
        self._http = http or HttpClient()
        self._memory: Optional[Dict[str, Any]] = None
        self._fetched_at = 0.0

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    def _read_cache(self) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return None

    def _write_cache(self, data: Dict[str, Any]) -> None:
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            self._cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            logger.warning("公告缓存写入失败")

    async def fetch(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force and self._memory and now - self._fetched_at < CACHE_TTL:
            return self._memory

        for url in SOURCES:
            try:
                text = await self._http.get_text(url)
                data = _parse_payload(text)
                if not data:
                    logger.warning("公告源格式无法识别：%s", url)
                    continue
                data.setdefault("announcements", [])
                data.setdefault("update", {})
                self._memory = data
                self._fetched_at = now
                self._write_cache(data)
                logger.info("公告已更新：%d 条（源 %s）", len(data["announcements"]), url)
                return data
            except Exception as exc:  # 网络失败不应影响启动
                logger.warning("公告源不可达 %s：%s", url, exc)

        cached = self._read_cache()
        if cached:
            self._memory = cached
            self._fetched_at = now
            logger.info("使用缓存的公告：%d 条", len(cached.get("announcements", [])))
            return cached

        empty = {"announcements": [], "update": {}, "version": ""}
        self._memory = empty
        self._fetched_at = now
        return empty


def is_forced(current: str, min_version: str) -> bool:
    """current < min_version 时强制更新"""
    def parse(v: str) -> List[int]:
        return [int(x) for x in re.findall(r"\d+", str(v))[:3]] or [0, 0, 0]

    return parse(current) < parse(min_version)


__all__ = ["AnnouncementClient", "is_forced", "SOURCES"]
