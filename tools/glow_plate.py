"""Genera el fondo de marca de Ryson: aro rojo de pincelada grunge sobre
transparente, al estilo de la imagen de referencia (1254x1254 RGBA)."""
import math

import numpy as np
from PIL import Image, ImageFilter


def _noise(shape, res, rng, octaves=4):
    """Ruido fractal simple (valor) por sobremuestreo bicubico."""
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        r = max(2, int(res * (2 ** o)))
        base = rng.random((r, r)).astype(np.float32)
        layer = np.asarray(
            Image.fromarray((base * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
            np.float32,
        ) / 255.0
        out += amp * layer
        total += amp
        amp *= 0.5
    return out / total


def _angular_smear(a, strength=9):
    """Difumina a lo largo del arco para que la textura parezca pincelada."""
    S = a.shape[0]
    NR, NA = 512, 1440
    cx = cy = (S - 1) / 2.0
    rs = np.linspace(0, S / 2.0, NR)
    ths = np.linspace(0, 2 * math.pi, NA, endpoint=False)
    RR, TT = np.meshgrid(rs, ths, indexing="ij")
    X = np.clip((cx + RR * np.cos(TT)).round().astype(int), 0, S - 1)
    Y = np.clip((cy + RR * np.sin(TT)).round().astype(int), 0, S - 1)
    polar = a[Y, X]
    k = np.ones(strength, np.float32) / strength
    pad = np.concatenate([polar[:, -strength:], polar, polar[:, :strength]], axis=1)
    sm = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, pad)
    polar = sm[:, strength:strength + NA]
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy)
    th = np.mod(np.arctan2(dy, dx), 2 * math.pi)
    ri = np.clip((r / rs[-1] * (NR - 1)).round().astype(int), 0, NR - 1)
    ti = np.mod((th / (2 * math.pi) * NA).round().astype(int), NA)
    return polar[ri, ti]


def make_plate(size=1254, seed=7):
    rng = np.random.default_rng(seed)
    S = size
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    cx = cy = (S - 1) / 2.0
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy) / (S / 2.0)          # 0..~1.41
    th = np.mod(np.arctan2(dy, dx), 2 * math.pi)

    # --- grosor y radio del aro modulados por angulo (pincelada irregular)
    nang = 720
    ang = np.linspace(0, 2 * math.pi, nang, endpoint=False)
    wob = np.zeros(nang, np.float32)
    for k, a in ((2, 0.012), (3, 0.010), (5, 0.008), (7, 0.005), (11, 0.004)):
        wob += a * np.sin(k * ang + rng.random() * 6.28)
    thick = 0.105 + np.zeros(nang, np.float32)
    for k, a in ((1, 0.022), (2, 0.018), (4, 0.014), (6, 0.010), (9, 0.008)):
        thick += a * np.sin(k * ang + rng.random() * 6.28)
    idx = np.clip((th / (2 * math.pi) * nang).astype(int), 0, nang - 1)
    r_mid = 0.870 + wob[idx]
    half = np.clip(thick[idx], 0.03, None)

    d = np.abs(r - r_mid) / half
    band = np.clip(1.0 - d * d, 0.0, 1.0) ** 0.75          # perfil suave del aro

    # --- textura grunge
    grain = _noise((S, S), 6, rng, octaves=5)
    streak = _noise((S, S), 3, rng, octaves=3)
    streak = np.asarray(
        Image.fromarray((streak * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(1.5)
        ),
        np.float32,
    ) / 255.0
    tex = np.clip(0.45 + 1.25 * (0.55 * grain + 0.45 * streak) - 0.35, 0.0, 1.4)

    a = band * tex

    # --- salpicaduras / manchas sueltas alrededor del aro
    splat = np.zeros((S, S), np.float32)
    for _ in range(260):
        t = rng.random() * 2 * math.pi
        rr = r_mid.mean() + rng.normal(0, 0.085)
        px = cx + rr * (S / 2) * math.cos(t)
        py = cy + rr * (S / 2) * math.sin(t)
        rad = rng.uniform(3, 26)
        y0, y1 = int(max(0, py - rad)), int(min(S, py + rad + 1))
        x0, x1 = int(max(0, px - rad)), int(min(S, px + rad + 1))
        if y1 <= y0 or x1 <= x0:
            continue
        sy, sx = np.mgrid[y0:y1, x0:x1]
        dd = ((sx - px) ** 2 + (sy - py) ** 2) / (rad * rad)
        splat[y0:y1, x0:x1] = np.maximum(
            splat[y0:y1, x0:x1], np.clip(1 - dd, 0, 1) * rng.uniform(0.25, 0.9)
        )
    a = np.clip(a + splat * 0.55 * tex, 0, 1.2)

    # halo interior tenue para que el producto no quede "flotando"
    halo = np.clip(1 - (r / (r_mid.mean() * 0.95)) ** 2, 0, 1) ** 2 * 0.10
    a = np.clip(a + halo, 0, 1)
    a = _angular_smear(a, strength=13)
    # apaga los restos de textura fuera del aro (evita rayas hacia las esquinas)
    a *= np.clip((1.15 - r) / 0.18, 0, 1)

    a = np.asarray(
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(1.2)
        ),
        np.float32,
    ) / 255.0
    a = np.clip(a * 0.80, 0, 1)          # el aro es translucido, como la referencia

    # --- color: rojo intenso que se oscurece hacia los bordes de la pincelada
    warm = np.clip(band * 1.1 + splat * 0.4, 0, 1)
    R = 150 + 105 * warm
    G = 6 + 34 * np.clip(warm - 0.55, 0, 1) / 0.45
    B = 4 + 26 * np.clip(warm - 0.65, 0, 1) / 0.35

    rgba = np.dstack([R, G, B, a * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


if __name__ == "__main__":
    import sys

    out = sys.argv[1] if len(sys.argv) > 1 else "assets/plate_glow.png"
    make_plate().save(out)
    print("plate ->", out)
