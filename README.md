# Ryson
Tienda de suplementos

## Imágenes de producto (estilo aro rojo)

Herramientas para generar las fichas cuadradas de producto con el aro rojo
grunge sobre fondo transparente (1254 × 1254 PNG), igual que la imagen de
referencia en `assets/referencia.png`.

```
assets/plate_glow.png     fondo reutilizable (aro rojo, transparente)
tools/glow_plate.py       regenera el fondo (cambia el seed para otra textura)
tools/make_hero.py        recorta el producto y lo monta sobre el fondo
output/                   imágenes finales
```

### Uso

```bash
pip install pillow numpy

# 1) pre entreno Shaaboom Pump Shot, 4 tomas en abanico
python3 tools/make_hero.py --out output/preentreno-shaaboom-4-tomas.png \
    --layout fan --angulo 0 --solape 0.32 --alto 0.58 --fill 0.72 \
    fotos/shaaboom-pump-shot.jpg fotos/shaaboom-pump-shot.jpg \
    fotos/shaaboom-pump-shot.jpg fotos/shaaboom-pump-shot.jpg

# 2) bebidas Maximum proteína + Hidralife, en fila
python3 tools/make_hero.py --out output/maximum-hidralife.png \
    --layout row --hero 1.08 --alto 0.55 --fill 0.82 \
    fotos/hidralife-manzana.png fotos/hidralife-ponche.png \
    fotos/maximum-frutos-tropicales.jpg \
    fotos/hidralife-blueberry.png fotos/hidralife-uva.png
```

Opciones: `--layout fan|row`, `--fill` (cuánto ocupa el producto dentro del aro),
`--alto`, `--solape` y `--angulo` (abanico), `--hero` (cuánto más grande va el
producto del centro en la fila), `--plate` (otro fondo).

Las fotos pueden tener fondo blanco o liso (se recorta automáticamente con
flood fill desde las esquinas) o venir ya en PNG con transparencia, que se
respeta tal cual. Para fondos complejos conviene recortar antes en Photoshop /
remove.bg y pasar el PNG ya limpio.
