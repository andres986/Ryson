"""Genera las piezas publicitarias de Ryson (fondo negro, producto, marca y descripción).

Uso: python3 generar.py <jetfuel.png> <bcaa.png> <creatina.png>
"""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
OUT = Path(__file__).parent
FONTS = "/usr/share/fonts/opentype/inter/"


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def quitar_fondo_blanco(im, umbral=238, croma_max=255):
    """Elimina el fondo blanco conectado a los bordes y suaviza el contorno."""
    im = im.convert("RGBA")
    rgb = np.array(im.convert("RGB")).astype(int)
    casi_blanco = (rgb.min(axis=2) >= umbral) & (rgb.max(axis=2) - rgb.min(axis=2) <= croma_max) & (np.array(im)[:, :, 3] > 0)
    h, w = casi_blanco.shape
    fondo = np.zeros_like(casi_blanco)
    cola = deque((y, x) for y in range(h) for x in (0, w - 1)) + deque((y, x) for x in range(w) for y in (0, h - 1))
    while cola:
        y, x = cola.popleft()
        if 0 <= y < h and 0 <= x < w and casi_blanco[y, x] and not fondo[y, x]:
            fondo[y, x] = True
            cola.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    alpha = Image.fromarray(np.where(fondo, 0, 255).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    alpha = Image.fromarray(np.minimum(np.array(alpha), np.array(im)[:, :, 3]), "L")
    im.putalpha(alpha)
    return im


def recortar(im):
    return im.crop(im.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox())


def texto_espaciado(draw, xy, texto, f, fill, tracking=0, anchor_centro=False):
    anchos = [draw.textlength(c, font=f) for c in texto]
    total = sum(anchos) + tracking * (len(texto) - 1)
    x, y = xy
    if anchor_centro:
        x -= total / 2
    for c, a in zip(texto, anchos):
        draw.text((x, y), c, font=f, fill=fill)
        x += a + tracking
    return total


def envolver(draw, texto, f, ancho_max):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if draw.textlength(prueba, font=f) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def resplandor(color, centro, radio, intensidad):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    cx, cy = centro
    d.ellipse((cx - radio, cy - radio, cx + radio, cy + radio), fill=color + (intensidad,))
    return capa.filter(ImageFilter.GaussianBlur(radio * 0.55))


def componer(producto, p):
    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    acento = p["acento"]

    # Halo sutil detrás del producto
    centro_y = 520
    lienzo.alpha_composite(resplandor(acento, (W // 2, centro_y), 330, 70))
    lienzo.alpha_composite(resplandor((255, 255, 255), (W // 2, centro_y - 40), 180, 18))

    # Producto
    producto = recortar(producto)
    alto_obj = p.get("alto", 640)
    esc = min(alto_obj / producto.height, 620 / producto.width)
    producto = producto.resize((round(producto.width * esc), round(producto.height * esc)), Image.LANCZOS)
    px = (W - producto.width) // 2
    suelo = 860
    py = suelo - producto.height

    # Sombra de contacto
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).ellipse(
        (W // 2 - producto.width * 0.48, suelo - 14, W // 2 + producto.width * 0.48, suelo + 14),
        fill=acento + (90,),
    )
    lienzo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(14)))

    # Reflejo en el suelo
    reflejo = producto.transpose(Image.FLIP_TOP_BOTTOM)
    alto_ref = int(reflejo.height * 0.25)
    reflejo = reflejo.crop((0, 0, reflejo.width, alto_ref))
    grad = np.linspace(55, 0, alto_ref).astype(np.uint8)[:, None] * np.ones((1, reflejo.width), np.uint8)
    a = np.array(reflejo.getchannel("A")).astype(int) * grad // 255
    reflejo.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    lienzo.alpha_composite(reflejo, (px, suelo + 2))

    lienzo.alpha_composite(producto, (px, py))

    d = ImageDraw.Draw(lienzo)

    # Marca en pequeño (arriba izquierda) y línea de acento
    texto_espaciado(d, (64, 58), "RYSON", font("InterDisplay-Black.otf", 30), (255, 255, 255), tracking=9)
    d.rectangle((64, 102, 104, 105), fill=acento)
    texto_espaciado(d, (W - 64 - 170, 66), "SUPLEMENTOS", font("Inter-SemiBold.otf", 16),
                    (150, 150, 150), tracking=3.2)

    # Bloque de texto inferior
    y = 930
    texto_espaciado(d, (W // 2, y), p["categoria"], font("Inter-Bold.otf", 22), acento,
                    tracking=6, anchor_centro=True)
    y += 44
    f_titulo = font("InterDisplay-Black.otf", 74)
    d.text((W // 2, y), p["nombre"], font=f_titulo, fill=(255, 255, 255), anchor="ma")
    y += 92
    f_desc = font("Inter-Regular.otf", 27)
    for linea in envolver(d, p["descripcion"], f_desc, 820):
        d.text((W // 2, y), linea, font=f_desc, fill=(200, 200, 200), anchor="ma")
        y += 40

    # Etiquetas
    y += 24
    f_tag = font("Inter-SemiBold.otf", 19)
    anchos = [d.textlength(t, font=f_tag) + 40 for t in p["etiquetas"]]
    sep = 14
    x = (W - sum(anchos) - sep * (len(anchos) - 1)) / 2
    for t, a in zip(p["etiquetas"], anchos):
        d.rounded_rectangle((x, y, x + a, y + 44), radius=22, outline=acento, width=2)
        d.text((x + a / 2, y + 22), t, font=f_tag, fill=(255, 255, 255), anchor="mm")
        x += a + sep

    # Marca de agua inferior
    d.text((W // 2, H - 40), "ryson · tienda de suplementos", font=font("Inter-Medium.otf", 17),
           fill=(95, 95, 95), anchor="ms")
    return lienzo.convert("RGB")


PRODUCTOS = [
    {
        "archivo": "ryson-jetfuel-black-series.png",
        "acento": (205, 214, 224),
        "categoria": "TERMOGÉNICO PREMIUM",
        "nombre": "JETFUEL BLACK",
        "descripcion": "Apoya un metabolismo más activo, con adaptógenos para ayudar a "
                       "manejar el estrés y cafeína de liberación prolongada.",
        "etiquetas": ["GAT SPORT", "90 CÁPSULAS"],
        "alto": 660,
        "fondo_blanco": True,
    },
    {
        "archivo": "ryson-bcaa-defender.png",
        "acento": (212, 175, 90),
        "categoria": "RECUPERACIÓN MUSCULAR",
        "nombre": "BCAA DEFENDER",
        "descripcion": "Aminoácidos ramificados en proporción 8:1:1, extra cargados de "
                       "leucina y con vitaminas añadidas.",
        "etiquetas": ["KEVIN LEVRONE", "225 G"],
        "alto": 600,
        "fondo_blanco": False,
    },
    {
        "archivo": "ryson-creatina-hardcore.png",
        "acento": (230, 38, 43),
        "categoria": "FUERZA Y RENDIMIENTO",
        "nombre": "CREATINA HARDCORE",
        "descripcion": "Creatina monohidratada 100% pura. Sin sodio y sin aditivos "
                       "artificiales, para entrenar con más fuerza.",
        "etiquetas": ["INTEGRALMEDICA", "300 G"],
        "alto": 600,
        "fondo_blanco": True,
        "umbral": 175,
        "croma_max": 25,
    },
]

if __name__ == "__main__":
    for ruta, p in zip(sys.argv[1:4], PRODUCTOS):
        im = Image.open(ruta)
        im = quitar_fondo_blanco(im, p.get("umbral", 238), p.get("croma_max", 255)) if p["fondo_blanco"] else im.convert("RGBA")
        componer(im, p).save(OUT / p["archivo"], optimize=True)
        print("ok", p["archivo"])
