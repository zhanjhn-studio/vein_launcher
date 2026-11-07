"""生成 chest / anvil 图标：取游戏内的等距方块渲染图，裁边后缩到 64×64。

为什么不用原版贴图：
    `textures/block/anvil.png` 只是一块灰色噪面，铁砧的形状来自 3D 模型，
    把贴图放大永远看不出铁砧。等距渲染图才是玩家在游戏里看到的样子。

为什么是 64×64：
    侧栏显示 24px、分类卡 46px，64px 源在 1~2.7 倍缩放下都清晰；
    这两个图标在 CSS 里用 `image-rendering: auto` 平滑缩放（像素贴图仍用 pixelated）。

用法：python tools/fetch_render_icons.py
"""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "vein_launcher" / "presentation" / "webui" / "assets" / "icons"

BASE = "https://minecraftitemids.com/item/{name}.png"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
SIZE = 64
TARGETS = ("chest", "anvil")

# 等距渲染本身偏暗（铁砧尤其），在深色界面上要提亮才看得清
TUNING = {
    "anvil": {"brightness": 1.55, "contrast": 1.10},
    "chest": {"brightness": 1.05, "contrast": 1.02},
}


def fetch(name: str) -> Image.Image:
    request = urllib.request.Request(BASE.format(name=name), headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    image = image.resize((SIZE, SIZE), Image.LANCZOS)

    tune = TUNING.get(name, {})
    if tune:
        # 只提亮 RGB，保留 alpha，避免边缘出现灰底
        rgb = image.convert("RGB")
        rgb = ImageEnhance.Brightness(rgb).enhance(tune.get("brightness", 1.0))
        rgb = ImageEnhance.Contrast(rgb).enhance(tune.get("contrast", 1.0))
        image = Image.merge("RGBA", (*rgb.split(), image.getchannel("A")))
    return image


def main() -> int:
    ICONS.mkdir(parents=True, exist_ok=True)
    for name in TARGETS:
        image = fetch(name)
        path = ICONS / f"{name}.png"
        image.save(path, optimize=True)
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B, {image.width}×{image.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
