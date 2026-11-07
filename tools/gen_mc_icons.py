"""生成 16×16 的 Minecraft 风格小图标（chest / anvil）。

背景：`webui/assets/icons/chest.png` 原是一张 64×64 的 GUI 图集碎片（带透明边、
残缺格线），`anvil.png` 是一团纯灰噪点、没有轮廓。这两个文件被侧栏（MLC / Tools）、
下载页分类（Modpacks / Forge）、加载器卡片以及 RemoteIcon 兜底共用，直接重绘最省事。

画法：16×16 字符网格 + 调色板，逐像素写，保证像素块大小与其余 16×16 图标一致。

用法：python tools/gen_mc_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "vein_launcher" / "presentation" / "webui" / "assets" / "icons"

CHEST = [
    "................",
    "................",
    "..############..",
    "..#lLLlLLlLLl#..",
    "..#LLlLLlLLLL#..",
    "..#lLLLLLlLLl#..",
    "..############..",
    "..#BBBbBBbBBB#..",
    "..#BBBBggBBBB#..",
    "..#BBBbggbBBB#..",
    "..#BbBBBBBBbB#..",
    "..#BBBbBBbBBB#..",
    "..#bBBBBBBBBb#..",
    "..############..",
    "................",
    "................",
]

ANVIL = [
    "................",
    "................",
    "...##########...",
    "..#hHHHHHHHHh#..",
    "..#HHttttttHH#..",
    "..############..",
    "....########....",
    "....#sSSSSs#....",
    "....#sSSSSs#....",
    "....#SSSSSS#....",
    "..############..",
    "..#PPPPPPPPPP#..",
    "..############..",
    "................",
    "................",
    "................",
]

PALETTES = {
    "chest": {
        "#": (46, 32, 16, 255),
        "L": (166, 118, 60, 255),
        "l": (138, 96, 46, 255),
        "B": (150, 104, 46, 255),
        "b": (120, 82, 36, 255),
        "g": (219, 181, 76, 255),
    },
    "anvil": {
        "#": (42, 42, 42, 255),
        "H": (196, 196, 196, 255),
        "h": (215, 215, 215, 255),
        "t": (168, 168, 168, 255),
        "S": (138, 138, 138, 255),
        "s": (156, 156, 156, 255),
        "P": (122, 122, 122, 255),
    },
}

GRIDS = {"chest": CHEST, "anvil": ANVIL}


def render(name: str) -> Image.Image:
    grid = GRIDS[name]
    palette = PALETTES[name]
    if len(grid) != 16 or any(len(row) != 16 for row in grid):
        raise ValueError(f"{name}: 网格必须是 16×16")
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            try:
                pixels[x, y] = palette[ch]
            except KeyError as exc:  # pragma: no cover - 便于发现拼错
                raise ValueError(f"{name}: 第 {y} 行出现未定义色 {ch!r}") from exc
    return image


def main() -> int:
    ICONS.mkdir(parents=True, exist_ok=True)
    for name in GRIDS:
        path = ICONS / f"{name}.png"
        render(name).save(path, optimize=True)
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
