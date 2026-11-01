"""Tiện ích màu và tô màu ảnh."""

import colorsys
import math

from PIL import Image


def tint_image(im, color):
    """Đổi phần có màu của ảnh sang màu đã chọn, giữ nguyên phần trắng/đen/xám."""
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    th, ts, tv = colorsys.rgb_to_hsv(r, g, b)
    alpha = im.getchannel("A")
    rgb = im.convert("RGB")
    h, s, v = rgb.convert("HSV").split()
    mask = s.point(lambda x: 255 if x > 70 else 0)          # chỉ đổi pixel có màu
    nh = Image.new("L", im.size, int(th * 255))
    ns = s.point(lambda x: int(x * ts))
    nv = v.point(lambda x: int(x * tv))
    colored = Image.merge("HSV", (nh, ns, nv)).convert("RGB")
    out = Image.composite(colored, rgb, mask)
    out.putalpha(alpha)
    return out


def mix(c1, c2, t):
    """Trộn màu c1 với c2 theo tỉ lệ t (0 = c1, 1 = c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def _rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def luminance(c):
    r, g, b = _rgb(c)
    return 0.299 * r + 0.587 * g + 0.114 * b


def low_contrast(bg, fg, was_on):
    """Nền bg (r, g, b) có gần trùng màu con trỏ fg (#rrggbb) không (khoảng cách màu "redmean", gần mắt người).
    Hai ngưỡng: bật khi < 90, chỉ tắt khi > 130, để rê qua vùng ranh giới con trỏ không nhấp nháy."""
    r1, g1, b1 = bg
    r2, g2, b2 = _rgb(fg)
    rm = (r1 + r2) / 2
    d = math.sqrt((2 + rm / 256) * (r1 - r2) ** 2 + 4 * (g1 - g2) ** 2 + (2 + (255 - rm) / 256) * (b1 - b2) ** 2)
    return d < (130 if was_on else 90)


def contrast_outline(c):
    """Màu viền nổi trên cả con trỏ màu c lẫn nền cùng màu: đen cho màu sáng, trắng cho màu tối."""
    return "#101010" if luminance(c) > 128 else "#FFFFFF"
