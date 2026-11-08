"""生成速查窗用的「附魔书」图标（64×64）。"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(r"Z:\Vein Launche\assets\palette_book.png")
SIZE = 64
SCALE = 8  # 先大图再缩小，边缘更顺

img = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
s = SCALE
W = SIZE * SCALE


def box(x0, y0, x1, y1, color, radius=0):
    if radius:
        d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=radius * s, fill=color)
    else:
        d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=color)


# 阴影
box(10, 14, 56, 56, (0, 0, 0, 90), radius=6)
# 封面（附魔紫）
box(8, 10, 54, 54, (86, 62, 138, 255), radius=5)
# 封面高光
box(10, 12, 52, 20, (128, 100, 190, 255), radius=3)
# 书页
box(52, 13, 58, 52, (233, 226, 205, 255), radius=2)
box(54, 16, 57, 49, (214, 204, 178, 255), radius=1)
# 书脊
box(8, 10, 14, 54, (66, 46, 110, 255), radius=3)
# 金角
box(14, 14, 20, 20, (232, 194, 92, 255), radius=2)
box(42, 44, 48, 50, (232, 194, 92, 255), radius=2)
# 附魔纹路
box(24, 26, 42, 30, (176, 148, 236, 230), radius=2)
box(24, 34, 38, 38, (176, 148, 236, 200), radius=2)
box(24, 42, 34, 46, (176, 148, 236, 170), radius=2)

# 星光
def star(cx, cy, r, color):
    d.polygon(
        [
            (cx * s, (cy - r) * s),
            ((cx + r * 0.35) * s, (cy - r * 0.35) * s),
            ((cx + r) * s, cy * s),
            ((cx + r * 0.35) * s, (cy + r * 0.35) * s),
            (cx * s, (cy + r) * s),
            ((cx - r * 0.35) * s, (cy + r * 0.35) * s),
            ((cx - r) * s, cy * s),
            ((cx - r * 0.35) * s, (cy - r * 0.35) * s),
        ],
        fill=color,
    )


star(46, 12, 4, (255, 246, 200, 235))
star(20, 50, 3, (214, 198, 255, 210))
star(50, 40, 2, (255, 255, 255, 190))

img = img.resize((SIZE, SIZE), Image.LANCZOS)
img.save(OUT)
print("saved", OUT, OUT.stat().st_size, "bytes")
