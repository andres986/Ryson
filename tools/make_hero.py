#!/usr/bin/env python3
"""Arma una imagen de producto al estilo Ryson: recorta el/los productos y los
monta sobre el aro rojo grunge, en PNG cuadrado con fondo transparente.

Uso:
    python3 tools/make_hero.py --out output/preentreno.png fotos/shaaboom.png
    python3 tools/make_hero.py --out output/bebidas.png --layout row \
        fotos/maximum1.jpg fotos/maximum2.jpg fotos/hidralife.jpg

Las fotos pueden venir con fondo blanco/liso (se recorta solo) o ya en PNG
con transparencia (se respeta su canal alfa).
"""
import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1254
SENTINEL = (1, 254, 3)


def cutout(path, tol=32):
    """Devuelve el producto recortado en RGBA, sin fondo y ajustado a su bbox."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or "transparency" in im.info:
        im = im.convert("RGBA")
        if np.asarray(im)[..., 3].min() < 250:
            return _trim(im)
    im = im.convert("RGB")
    w, h = im.size
    work = im.copy()
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(work, seed, SENTINEL, thresh=tol)
    arr = np.asarray(work)
    bg = np.all(np.abs(arr.astype(int) - np.array(SENTINEL)) < 3, axis=-1)
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha = np.asarray(
        Image.fromarray(alpha).filter(ImageFilter.MinFilter(3)).filter(
            ImageFilter.GaussianBlur(0.8)
        )
    )
    out = np.dstack([np.asarray(im), alpha])
    return _trim(Image.fromarray(out, "RGBA"))


def _trim(im):
    bbox = im.split()[3].getbbox()
    return im.crop(bbox) if bbox else im


def _scaled(im, height):
    """Reescala manteniendo proporcion; si hay que ampliar, reenfoca un poco."""
    w, h = im.size
    k = height / h
    out = im.resize((max(1, round(w * k)), height), Image.LANCZOS)
    if k > 1.4:
        rgb = out.convert("RGB").filter(
            ImageFilter.UnsharpMask(radius=1.6, percent=int(min(140, 55 * k)), threshold=3)
        )
        out = Image.merge("RGBA", rgb.split() + (out.split()[3],))
    return out


def layout_fan(items, height, angle=-7.0, overlap=0.42, rise=0.035):
    """Productos alargados (barras, sobres) en abanico, como la referencia."""
    tiles = []
    for i, im in enumerate(items):
        t = _scaled(im, height).rotate(
            angle * (1 + 0.12 * (i - (len(items) - 1) / 2)),
            Image.BICUBIC, expand=True,
        )
        tiles.append(t)
    step = int(max(t.size[0] for t in tiles) * (1 - overlap))
    total = step * (len(tiles) - 1) + tiles[-1].size[0]
    canvas = Image.new("RGBA", (total, max(t.size[1] for t in tiles) + int(height * rise * len(tiles))), (0, 0, 0, 0))
    for i, t in enumerate(tiles):
        y = int(height * rise * (len(tiles) - 1 - i))
        canvas.alpha_composite(t, (step * i, y))
    return _trim(canvas)


def layout_row(items, height, gap=0.05, hero=1.0, arc=0.0):
    """Botellas/latas en fila, la del centro al frente y algo mas grande."""
    n = len(items)
    mid = (n - 1) / 2
    tiles = []
    for i, im in enumerate(items):
        f = hero if abs(i - mid) < 0.5 else 1.0 - 0.07 * abs(i - mid)
        tiles.append(_scaled(im, int(height * f)))
    g = int(height * gap)
    total = sum(t.size[0] for t in tiles) + g * (n - 1)
    top = int(height * arc * n)
    canvas = Image.new("RGBA", (total, max(t.size[1] for t in tiles) + top), (0, 0, 0, 0))
    x = 0
    order = sorted(range(n), key=lambda i: -abs(i - mid))  # centro al frente
    xs = []
    for t in tiles:
        xs.append(x)
        x += t.size[0] + g
    base = canvas.size[1]
    for i in order:
        t = tiles[i]
        canvas.alpha_composite(t, (xs[i], base - t.size[1] - int(height * arc * (mid - abs(i - mid)) * 0.5)))
    return _trim(canvas)


def shadow(group, blur=16, offset=(0, 18), opacity=0.45, spread=1.0):
    a = group.split()[3].resize(
        (int(group.size[0] * spread), int(group.size[1] * spread)), Image.LANCZOS
    ).filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", a.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * opacity)))
    return sh, offset


def build(paths, out, layout="fan", fill=0.78, height_frac=0.74,
          plate="assets/plate_glow.png", angle=-7.0, overlap=0.42, hero=1.0):
    items = [cutout(p) for p in paths]
    h = int(SIZE * height_frac)
    group = (layout_fan(items, h, angle=angle, overlap=overlap)
             if layout == "fan" else layout_row(items, h, hero=hero))

    max_w, max_h = SIZE * fill, SIZE * 0.86
    k = min(max_w / group.size[0], max_h / group.size[1])
    group = group.resize((round(group.size[0] * k), round(group.size[1] * k)), Image.LANCZOS)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    if os.path.exists(plate):
        canvas.alpha_composite(Image.open(plate).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS))
    gx = (SIZE - group.size[0]) // 2
    gy = (SIZE - group.size[1]) // 2
    sh, (ox, oy) = shadow(group)
    canvas.alpha_composite(sh, (gx - (sh.size[0] - group.size[0]) // 2 + ox,
                                gy - (sh.size[1] - group.size[1]) // 2 + oy))
    canvas.alpha_composite(group, (gx, gy))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    canvas.save(out)
    print("->", out, canvas.size)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fotos", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--layout", choices=["fan", "row"], default="fan")
    ap.add_argument("--fill", type=float, default=0.78)
    ap.add_argument("--alto", type=float, default=0.74, dest="height_frac")
    ap.add_argument("--plate", default="assets/plate_glow.png")
    ap.add_argument("--angulo", type=float, default=-7.0, dest="angle")
    ap.add_argument("--solape", type=float, default=0.42, dest="overlap")
    ap.add_argument("--hero", type=float, default=1.0)
    a = ap.parse_args()
    build(a.fotos, a.out, a.layout, a.fill, a.height_frac, a.plate,
          a.angle, a.overlap, a.hero)
