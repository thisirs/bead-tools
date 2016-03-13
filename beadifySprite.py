#! /usr/bin/env python2
# -*- coding: utf-8 -*-

"""This script converts any input image file in a corresponding bead
image file using some predefined palettes."""

import yaml
import re


def resolve_palette(p_data, p_name):
    return resolve_palette0(p_data, p_name, [p_name])


def resolve_palette0(p_data, p_name, ancestors):
    palette = p_data['palettes'].get(p_name)
    if not palette:
        raise ValueError("Unknown palette `{0}'".format(p_name))

    from_palettes = palette.get('from') or []
    fpr = []
    for p in from_palettes:
        if p in ancestors:
            raise ValueError('Cyclic dependencies')

        rp = resolve_palette0(p_data, p, ancestors + [p])
        fpr.append(rp)

    palette['colors'] = resolve_colors(p_data, palette['colors'], fpr)
    return palette


def resolve_colors(p_data, colors, from_palettes):
    """Resolve all colors from COLORS using FROM_PALETTES if no value is
provided. Ensure there is no duplicate entry."""
    c = [x for c in colors for x in normalize_color_entry(p_data, c, from_palettes)]
    uniq = []
    codes = []
    for e in c:
        code = e['code']
        if code not in codes:
            uniq.append(e)
            codes.append(code)
    return uniq


def iscode(e):
    m = re.match('(H|N|P)(\d\d\d?)', e)
    if m:
        num = int(m.group(2))
        if m.group(1) == 'H':
            return num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                           14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26,
                           27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
                           38, 42, 43, 44, 45, 46, 47, 48, 49, 55, 56,
                           57, 60, 61, 62, 63, 64, 70, 71, 72, 73, 74]
        elif m.group(1) == 'N':
            return 1 <= num <= 30
        else:
            return num in [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 17, 18,
                           20, 21, 35, 38, 47, 48, 49, 50, 52, 53, 54,
                           56, 57, 58, 59, 60, 61, 62, 63, 69, 70, 75,
                           79, 80, 80, 83, 85, 88, 90, 91, 92, 93, 96,
                           97, 98, 100, 101, 102, 103, 104, 105]
    else:
        return None


def get_palette_from_palettes(p_name):
    "Get palette object named P_NAME."
    if p_name not in p_data['palettes']:
        raise ValueError("Unknown palette `{0}'".format(p_name))
    return p_data['palettes'][p_name]


def getvalue(e):
    m = re.match('#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})', e)
    if m:
        return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
    else:
        return None


def normalize_color_entry(p_data, e, from_p):
    "Normalize color E from FROM_P palettes."
    if isinstance(e, list):
        return [{'value': tuple(e)}]
    elif isinstance(e, tuple):
        return [{'value': e}]
    elif isinstance(e, str):
        if iscode(e):
            return [get_color_entry(from_p, code=e)]
        ev = getvalue(e)
        if ev:
            return [{'value': ev}]
        ep = get_palette_from_palettes(e)
        if ep:
            return resolve_palette(p_data, e)['colors']
        else:
            return [get_color_entry(from_p, name=e)]
    elif isinstance(e, dict):
        name = e.get('name')
        code = e.get('code')
        value = e.get('value')
        if value:
            a = {'value': getvalue(value)}
            if name:
                a['name'] = name
            if code:
                a['code'] = code
            return [a]
        elif name or code:
            return [get_color_entry(from_p, name=name, code=code)]
        elif len(e) == 1:
            k = e.keys()[0]
            v = e[k]
            vv = getvalue(v)
            if vv:
                if iscode(k):
                    return [{'code': k, 'value': vv}]
                else:
                    return [{'name': k, 'value': vv}]
            else:
                raise ValueError('Unknown color specification')
        else:
            raise ValueError('Unknown color specification')
    else:
        raise ValueError('Unknown color specification')


def get_color_entry(palettes, name=None, code=None, value=None):
    "Look for color entry in list of palettes PALETTES."
    def color_match(c):
        return (c.get('name') and c.get('name') == name) or \
            (c.get('code') and c.get('code') == code) or \
            (c.get('value') and c.get('value') == value)

    for p in palettes:
        colors = p['colors']
        cn = [c for c in colors if color_match(c)]
        if len(cn) == 1:
            return cn[0]
        elif len(cn) > 1:
            raise ValueError('Too many colors')

    raise ValueError('Not able to resolve color {0}, {1}'.format(name, code))


if __name__ == '__main__':
    import os
    import argparse
    from PIL import Image

    import numpy as np
    from scipy import ndimage

    from colormath.color_objects import LabColor, sRGBColor
    from colormath.color_conversions import convert_color
    from colormath.color_diff import delta_e_cie1976

    # Caching color_distance results
    from functools32 import lru_cache

    # File configuration validation
    from schema import Schema, And, Optional, Or

    # Multiline help line
    from argparse import RawTextHelpFormatter

    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description=__doc__)
    parser.add_argument('files',
                        nargs='+',
                        help="name of image files")
    parser.add_argument('-D',
                        '--directory',
                        type=str,
                        help="directory to store image files")
    parser.add_argument("-c",
                        "--config",
                        type=str,
                        default='config.yml',
                        help="use specific configuration file (default: %(default)s)")
    parser.add_argument("-f",
                        "--format",
                        type=str,
                        default='{filename}-{palette}.{ext}',
                        help="format of resulting image file (default: %(default)s)")
    parser.add_argument("-m",
                        "--magnify",
                        type=int,
                        default=1,
                        help="scale parameter of the resulting image (default: %(default)s)")
    parser.add_argument("-s",
                        "--subsample",
                        type=int,
                        default=1,
                        help="subsampling rate of input image (default: %(default)s)")
    parser.add_argument("-p",
                        "--palette",
                        type=str,
                        help="name of the palette to use to convert input image")

    def distance_lab(c1, c2):
        "Color distance in the Lab colorimetric space."
        color1 = sRGBColor(*c1[:3], is_upscaled=True)
        color1_lab = convert_color(color1, LabColor)
        color2 = sRGBColor(*c2[:3], is_upscaled=True)
        color2_lab = convert_color(color2, LabColor)
        return delta_e_cie1976(color1_lab, color2_lab)

    def distance_rgb(c1, c2):
        "Classic Euclidean distance between colors in the RGB space."
        return np.linalg.norm(np.array(c1)-np.array(c2))

    COLOR_DISTANCES = {"cie76": distance_lab, "rgb": distance_rgb}

    help_string = "color distance to use: (default: %(default)s)\n"
    help_string += '\n'.join(['  {0}: {1}'.format(k, v.__doc__) for k, v in COLOR_DISTANCES.items()])

    parser.add_argument("-d",
                        "--distance",
                        type=str,
                        choices=COLOR_DISTANCES.keys(),
                        default="cie76",
                        help=help_string)
    args = parser.parse_args()

    schema = Schema({'palettes': {And(str, len): {'description': Or(str, unicode),
                                                  'colors': [Or({str: str}, str)],
                                                  Optional('from'): Or(str, [str])}},
                     'default': str,
                     'locale': str,
                     'locales': {str: {str: Or(unicode, str)}}})

    config_file = args.config

    if not os.path.exists(config_file):
        raise SystemError("Configuration file '{0}' not found".format(config_file))

    stream = open(config_file, "r")
    p_data = yaml.load(stream)

    Schema(schema).validate(p_data)

    color_distance = COLOR_DISTANCES[args.distance]

    palette_name = args.palette or p_data.get('default')
    if palette_name:
        palette = resolve_palette(p_data, palette_name)
        colors = palette['colors']
    else:
        raise ValueError('No palette name specified')

    print("Using palette `{0}' with {1} colors".format(palette_name, len(colors)))

    @lru_cache(maxsize=None)
    def get_closest_color(r, g, b, a):
        delta_min = np.inf
        for cd in colors:
            color = cd['value']
            delta = color_distance((r, g, b), color)

            if delta < delta_min:
                closest_color = cd
                delta_min = delta

        return closest_color

    for k, file in enumerate(args.files):
        print('Processing file {0} {1}/{2}'.format(file, k+1, len(args.files)))

        s_dir, s_name = os.path.split(file)
        s_name, s_ext = os.path.splitext(s_name)
        s_ext = s_ext[1:]

        if args.directory:
            directory = args.directory
        else:
            directory = s_dir

        format = args.format

        try:
            image = Image.open(file)
            image = np.asarray(image)
        except Exception as e:
            print("Unable to load image `{0}', skipping".format(file))
            print(e)
            continue

        if len(image.shape) == 2:  # Grayscale image
            (nrows, ncols) = image.shape
            nbands = 1
            nimage = np.ones((nrows, ncols, 4))
            nimage[:, :, 0] = image
            nimage[:, :, 1] = image
            nimage[:, :, 2] = image
            image = nimage
        elif len(image.shape) == 3:
            (nrows, ncols, nbands) = image.shape
            if nbands == 3:
                nimage = np.ones((nrows, ncols, 4))
                nimage[:, :, :3] = image
                image = nimage
            elif nbands != 4:
                print("Not enough numbers of bands, skipping")
                continue

        # Subsample
        fact = args.subsample
        if fact != 1:
            sx, sy = image.shape
            X, Y = np.ogrid[0:sx, 0:sy]
            regions = sy/fact * (X/fact) + Y/fact
            image = ndimage.mean(image, labels=regions, index=np.arange(regions.max() + 1))
            (nrows, ncols, nbands) = image.shape

        # Final image
        magnify = args.magnify
        image_beads = np.zeros((magnify*nrows, magnify*ncols, 4), dtype=np.uint8)

        beads = {}
        for i in range(nrows):
            for j in range(ncols):
                pixel = image[i, j, :]

                # Skip transparent pixels
                if pixel[3] == 0:
                    continue

                closest_color = get_closest_color(*pixel)
                (r, g, b) = closest_color['value']

                if closest_color['code'] in beads:
                    beads[closest_color['code']] += 1
                else:
                    beads[closest_color['code']] = 1

                for ii in range(magnify):
                    for jj in range(magnify):
                        image_beads[ii+magnify*i, jj+magnify*j, :] = (r, g, b, 255)

        name = format.format(filename=s_name, ext=s_ext, palette=palette_name)
        path = os.path.join(directory, name)
        image = Image.fromarray(image_beads)
        image.save(path)

        print('Wrote {0}'.format(name))

        total = 0
        for c in colors:
            code = c['code']
            if code in beads:
                print('{0}: {1}'.format(code, beads[code]))
                total += beads[code]
        print('Total: {0}'.format(total))
