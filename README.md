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

# 1) pre entreno Shaaboom, 4 sobres en abanico
python3 tools/make_hero.py --out output/preentreno-shaaboom-4-tomas.png \
    fotos/shaaboom1.jpg fotos/shaaboom2.jpg fotos/shaaboom3.jpg fotos/shaaboom4.jpg

# 2) bebidas Maximum proteína + Hidralife, en fila
python3 tools/make_hero.py --out output/maximum-hidralife.png --layout row \
    fotos/maximum-frutos-rojos.jpg fotos/maximum-vainilla.jpg fotos/hidralife-uva.jpg
```

Opciones: `--layout fan|row`, `--fill` (cuánto ocupa el producto dentro del aro,
0.78 por defecto), `--alto`, `--plate` (otro fondo).

Las fotos pueden tener fondo blanco o liso (se recorta automáticamente con
flood fill desde las esquinas) o venir ya en PNG con transparencia, que se
respeta tal cual. Para fondos complejos conviene recortar antes en Photoshop /
remove.bg y pasar el PNG ya limpio.
