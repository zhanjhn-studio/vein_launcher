"""从 Minecraft 官方 zh_cn 语言资源生成指令候选的中文名映射。

1.20+ 的 client.jar 只带 en_us，其它语言放在 assets 索引里（objects/<hash>）。
这里按 版本 JSON → assetIndex → minecraft/lang/zh_cn.json 的 hash 取文件，本地有就直接读，
没有就从官方资源站下载（TLS 被中间人拦截时退回不校验会话，与启动器一致）。

输出：src/cmdLabelsZh.ts
"""

import gzip
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(r"Z:\Vein Launche")
OUT = ROOT / "vein_launcher" / "presentation" / "webui" / "src" / "cmdLabelsZh.ts"
TREE = ROOT / "vein_launcher" / "presentation" / "webui" / "src" / "commandTree.ts"
ASSETS = ROOT / "VeinLauncher" / "minecraft" / "assets"

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
OBJECTS = "https://resources.download.minecraft.net/{prefix}/{hash}"
VERSION = "1.20.1"
UA = {"User-Agent": "VeinLauncher/0.5 (+local build)"}


def fetch(url: str, timeout: int = 180) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except ssl.SSLError:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.read()


def read_json_maybe_gz(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def main() -> int:
    tree = TREE.read_text(encoding="utf-8")
    tokens = sorted(
        set(re.findall(r"token:\s*'([^']+)'", tree)) | set(re.findall(r"token:\s*`([^`]+)`", tree))
    )
    print(f"tokens in command tree: {len(tokens)}")

    manifest = json.loads(fetch(MANIFEST, 60))
    entry = next(v for v in manifest["versions"] if v["id"] == VERSION)
    meta = json.loads(fetch(entry["url"], 60))
    index_url = meta["assetIndex"]["url"]
    index = json.loads(fetch(index_url, 120))["objects"]
    info = index.get("minecraft/lang/zh_cn.json")
    if not info:
        print("zh_cn not in asset index")
        return 1
    digest = info["hash"]
    local = ASSETS / "objects" / digest[:2] / digest
    if local.is_file():
        lang = read_json_maybe_gz(local)
        print(f"zh_cn from local assets ({local.stat().st_size} B)")
    else:
        raw = fetch(OBJECTS.format(prefix=digest[:2], hash=digest))
        lang = json.loads(raw.decode("utf-8"))
        print(f"zh_cn downloaded ({len(raw)} B)")
    print(f"entries: {len(lang)}")

    mapping: dict[str, str] = {}
    misses: list[str] = []
    for token in tokens:
        if not token.startswith("minecraft:"):
            continue
        path = token[len("minecraft:"):]
        for key in (
            f"block.minecraft.{path}",
            f"item.minecraft.{path}",
            f"entity.minecraft.{path}",
            f"effect.minecraft.{path}",
            f"enchantment.minecraft.{path}",
        ):
            if key in lang:
                mapping[token] = lang[key]
                break
        else:
            misses.append(token)

    print(f"mapped {len(mapping)} tokens, {len(misses)} without translation")
    for token in misses[:8]:
        print("  miss:", token)

    lines = [
        "/** 指令候选中文名：由 Minecraft 1.20.1 官方 zh_cn 语言资源生成，勿手改 */",
        "export const ZH_TOKENS: Record<string, string> = {",
    ]
    for token in sorted(mapping):
        lines.append(
            f"  {json.dumps(token, ensure_ascii=False)}: {json.dumps(mapping[token], ensure_ascii=False)},"
        )
    lines.append("};")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("written", OUT, f"{OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
