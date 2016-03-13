Bead tools
==========

Extracting sprites from sprites maps and quantizing them using a
specified palette.

# Installation

The scripts are written in Python and require the following libraries:
- `schema`
- `PyYAML`
- `Pillow`
- `colormath`
- `functools32`
- `scipy`
- `numpy`
- `cv2`

# Unpacking sprites with `unpackSprites.py`

The script `unpackSprites.py` allows you to extract sprites from a sprite
map. You can specify maximum and minimum size of sprites and resize
the resulting sprites.

## Usage

```bash
unpackSprites.py sprite-map.png
```

Extract sprites from the image file `sprite-map.png`. By default,
extracted sprites are named like `sprite-map-001` and stored in a
subdirectory named `sprite-maps_sprites` but this is configurable
through options `-f` or `--format` and `-d` or `--directory`.

## Features

- Automatic selection of background color
- Select size of extracted sprites
- Rescale the sprites

# Quantize an image with `beadifySprite.py`

The script `beadifySprite.py` converts any input image file into a
corresponding bead image file using some predefined palettes.

## Usage

```bash
beadifySprite.py sprite1.png sprite2.png
```
Quantize list of files `sprite1.png` and `sprite2.png`. The default
configuration file is the file `config.yml` but this can be specified
by option `-c` or `--config`. By default, the script use the palette
specified in the configuration file under the option `default` but
this can be overriden by specifying its name with option `-p`. You can
specify any palette you want under the option `pallettes` in the
configuration file. Currently, 3 palettes are available: `Perler`,
`Hama` and `Nabbi`. Palette can inherit list of colors from other
palettes.

## Features

- Perler, HAMA and Nabbi palettes available
- Easy customization of palettes through configuration file
- 2 color distances implemented so far

## Examples

The sprite map is taken from the [Spriter Resource](http://www.spriters-resource.com/).
First extract the sprites from the map:
```bash
./unpackSprites.py -m 70 examples/ItemsOverworld.png
```
and specify a minimum number of pixels per sprite to avoid false
positives.

Same thing but resize sprites by a factor of 10:
```bash
./unpackSprites.py -m 70 -r 10 --format '{filename}-resized10-{num:0>{length}}.png' examples/ItemsOverworld.png
```

Next, quantize the sprites with the Perler palette and the two
available color distances:
```bash
./beadifySprite.py -m 10 examples/ItemsOverworld_sprites/ItemsOverworld-??.png
./beadifySprite.py -m 10 -d rgb examples/ItemsOverworld_sprites/ItemsOverworld-??.png --format '{filename}-{palette}-rgb.{ext}'
```
and magnify the resulting sprites.

Compare the results:

Extracted sprites:

![ItemsOverworld-resized10-16.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-resized10-16.png)
![ItemsOverworld-resized10-21.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-resized10-21.png)
![ItemsOverworld-resized10-23.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-resized10-23.png)
![ItemsOverworld-resized10-47.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-resized10-47.png)
![ItemsOverworld-resized10-56.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-resized10-56.png)

After quantization with Lab distance:

![ItemsOverworld-16-Perler.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-16-Perler.png)
![ItemsOverworld-21-Perler.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-21-Perler.png)
![ItemsOverworld-23-Perler.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-23-Perler.png)
![ItemsOverworld-47-Perler.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-47-Perler.png)
![ItemsOverworld-56-Perler.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-56-Perler.png)

After quantization with RGB distance:

![ItemsOverworld-16-Perler-rgb.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-16-Perler-rgb.png)
![ItemsOverworld-21-Perler-rgb.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-21-Perler-rgb.png)
![ItemsOverworld-23-Perler-rgb.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-23-Perler-rgb.png)
![ItemsOverworld-47-Perler-rgb.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-47-Perler-rgb.png)
![ItemsOverworld-56-Perler-rgb.png](https://github.com/thisirs/bead-tools/blob/master/examples/ItemsOverworld_sprites/ItemsOverworld-56-Perler-rgb.png)

# Resources

The color codes from Perler, HAMA and Nabbi palettes are taken from
[this spreadsheet](https://docs.google.com/spreadsheets/d/1f988o68HDvk335xXllJD16vxLBuRcmm3vg6U9lVaYpA/edit#gid=0)
but some are still missing.

The script `unpackSprites.py` takes large parts from [this gist](https://gist.github.com/thevtm/89a74520c7189d30eb3c>)
