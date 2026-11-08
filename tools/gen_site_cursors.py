"""生成 MC 风格像素光标（箭头 / 手型），供网站自定义鼠标指针。"""

from pathlib import Path

from PIL import Image

OUT_DIR = Path(r"Z:\Vein Launche\veinwebsite-don'tupdategithub\assets")
SIZE = 32


def grid(rows, palette):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in palette:
                px[x, y] = palette[ch]
    return img


# 32x32 像素箭头（MC 风格白边 + 黑描边 + 主题紫填充）
ARROW = [
    "................................",
    ".########.......................",
    ".#wwwwww##......................",
    ".#wwwwwwww#.....................",
    ".#wwwwwwwww#....................",
    ".#wwwwwwwwww#...................",
    ".#wwwwwwwwwww#..................",
    ".#wwwwwwwwwwww#.................",
    ".#wwwwwwwwwwwww#................",
    ".#wwwwwwwwwwwwww#...............",
    ".#wwwwwwwwwwwwwww#..............",
    ".#wwwwwwwwwwwwwwww#.............",
    ".#wwwwwwwwwwwwwwwww#............",
    ".#wwwwwwwwwwwwwwwwww#...........",
    ".#wwwwwwwwwwwwwwwwwww#..........",
    ".#wwwwwwwwwwwwwwwwwwww#.........",
    ".#wwwwwwwwwwwwwwwww####.........",
    ".#wwwwwwwww#wwwwww#.............",
    ".#wwwwwwww#.#wwww#..............",
    ".#wwwwwww#..#wwww#..............",
    ".#wwwwww#...#wwww#..............",
    ".#wwwww#....#wwww#..............",
    ".#wwww#.....#wwww#..............",
    ".#www#......#wwww#..............",
    ".#ww#.......#wwww#..............",
    ".#w#........#wwww#..............",
    ".##..........#ww#...............",
    ".#............##................",
    "................................",
    "................................",
    "................................",
    "................................",
]

# 手型（指针）简化版
HAND = [
    "................................",
    "................................",
    "..........####..................",
    ".........#wwww#.................",
    ".........#wwww#.................",
    ".........#wwww#.................",
    ".........#wwww#......####.......",
    ".........#wwww#.....#wwww#......",
    ".........#wwww#.....#wwww#......",
    "....######wwww#.....#wwww#......",
    "...#wwwwwwwwwww#....#wwww#......",
    "...#wwwwwwwwwwww#...#wwww#......",
    "...#wwwwwwwwwwwww#..#wwww#......",
    "...#wwwwwwwwwwwwww#.#wwww#......",
    "...#wwwwwwwwwwwwwww##wwww#......",
    "...#wwwwwwwwwwwwwwwwwwwww#......",
    "...#wwwwwwwwwwwwwwwwwwwww#......",
    "....#wwwwwwwwwwwwwwwwwwww#......",
    "....#wwwwwwwwwwwwwwwwwwww#......",
    "....#wwwwwwwwwwwwwwwwwww#.......",
    ".....#wwwwwwwwwwwwwwwwww#.......",
    ".....#wwwwwwwwwwwwwwwwww#.......",
    "......#wwwwwwwwwwwwwwww#........",
    "......#wwwwwwwwwwwwwww#.........",
    ".......#wwwwwwwwwwwww#..........",
    ".......#wwwwwwwwwwwww#..........",
    "........#############...........",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
]

PALETTE_ARROW = {
    "#": (12, 14, 20, 255),      # 描边
    "w": (238, 241, 250, 255),   # 主体
}
PALETTE_HAND = {
    "#": (16, 12, 26, 255),
    "w": (214, 205, 255, 255),
}


def main() -> None:
    arrow = grid(ARROW, PALETTE_ARROW)
    # 紫色高光（主体右侧一列）
    px = arrow.load()
    for y in range(1, 24):
        for x in range(2, 20):
            r, g, b, a = px[x, y]
            if a and (r, g, b) == (238, 241, 250):
                px[x, y] = (164, 156, 255, 255) if x > 6 else (238, 241, 250, 255)
    arrow.save(OUT_DIR / "cursor-arrow.png")

    hand = grid(HAND, PALETTE_HAND)
    hand.save(OUT_DIR / "cursor-hand.png")
    print("saved cursors")


if __name__ == "__main__":
    main()
