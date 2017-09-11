# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

from past.utils import old_div
from lib.color_fade import ColorFade
import colorsys
from lib import dtypes

from lib.buffer_utils import struct_flat

import numpy as np


def float_to_uint8(float_color):
    """
    Converts a float color (0 to 1.0) to uint8 (0 to 255)
    """
    return tuple([int(255.0 * x) for x in float_color])

def uint8_to_float(uint8_color):
    """
    Converts a uint8 color (0 to 255) to float (0 to 1.0)
    """
    return tuple([old_div(float(x), 255.0) for x in uint8_color])

def rgb_uint8_to_hsv_float(rgb_color):
    return colorsys.rgb_to_hsv(*uint8_to_float(rgb_color))

def hsv_float_to_rgb_uint8(hsv_color):
    return float_to_uint8(colorsys.hsv_to_rgb(*hsv_color))

def clip(low, input, high):
    return min(max(input, low), high)

def blend_to_buffer(source, destination, progress, mode):
    if mode == 'overwrite':
        not_dark = source['lum'] > 0.0
        destination[not_dark] = source[not_dark]
    else:
        raise NotImplementedError

    return destination


def hls_blend(start, end, out, progress, mode, fade_length=1.0, ease_power=0.5):
    p = abs(progress)

    startPower = old_div((1.0 - p), fade_length)
    startPower = clip(0.0, startPower, 1.0)
    startPower = pow(startPower, ease_power)

    endPower = old_div(p, fade_length)
    endPower = clip(0.0, endPower, 1.0)
    endPower = pow(endPower, ease_power)

    l1clipped = np.empty_like(start['light'])
    l2clipped = np.empty_like(end['light'])
    np.clip(start['light'],0,1,l1clipped)
    np.clip(end['light'],0,1,l2clipped)
    np.clip(start['sat'],0,1,start['sat'])
    np.clip(end['sat'],0,1,end['sat'])

    startWeight = (1.0 - 2 * np.abs(0.5 - l1clipped)) * start['sat']
    endWeight = (1.0 - 2 * np.abs(0.5 - l2clipped)) * end['sat']

    s = (start['sat'] * startPower + end['sat'] * endPower)
    x1 = np.cos(2 * np.pi * start['hue']) * startPower * startWeight
    x2 = np.cos(2 * np.pi * end['hue']) * endPower * endWeight
    y1 = np.sin(2 * np.pi * start['hue']) * startPower * startWeight
    y2 = np.sin(2 * np.pi * end['hue']) * endPower * endWeight
    x = x1 + x2
    y = y1 + y2

    if progress >= 0:
        l = np.maximum(start['light'] * startPower, end['light'] * endPower)
        opposition = np.sqrt(np.square(old_div((x1-x2),2)) + np.square(old_div((y1-y2),2)))
        if mode == 'multiply':
            l = np.minimum(start['light'] * startPower, end['light'] * endPower)
            #l -= opposition
        elif mode == 'add':
            l = np.maximum(l, opposition, l)
    else: # hacky support for old blend
        l = old_div(np.sqrt(np.square(x) + np.square(y)), 2)

    h = old_div(np.arctan2(y, x), (2*np.pi))

    nocolor = (x * y == 0)
    np.where(nocolor, h, 0)
    np.where(nocolor, s, 0)

    np.clip(l, 0, 1, l)

    if out is None:
        out = np.empty_like(start)

    out['hue'] = h
    out['light'] = l
    out['sat'] = s

    return out

def rgb_to_hls(arr):
    """ fast rgb_to_hls using numpy array """
    # XXX: arr is assumed to be an unstructured, multidimensional integer array
    # rather than an array with dtype rgb_color. This is because the only user
    # of this function is ImagePattern and I don't feel like fixing that.

    # adapted from Arnar Flatberg
    # http://www.mail-archive.com/numpy-discussion@scipy.org/msg06147.html

    arr = old_div(arr.astype("float32"), 255.0)
    out = np.empty(arr.shape[0], dtype=dtypes.hls_color)

    arr_max = arr.max(-1)
    delta = arr.ptp(-1)
    arr_min = arr.min(-1)
    total = arr_max + arr_min

    l = old_div(total, 2.0)

    if total.all() > 0:
        s = old_div(delta, total)
        idx = (l > 0.5)
        s[idx] = old_div(delta[idx], (2.0 - total[idx]))

        # red is max
        idx = (arr[:,:,0] == arr_max)
        out['hue'][idx] = (arr[idx, 1] - arr[idx, 2]) / delta[idx]

        # green is max
        idx = (arr[:,:,1] == arr_max)
        out['hue'][idx] = 2. + (arr[idx, 2] - arr[idx, 0] ) / delta[idx]

        # blue is max
        idx = (arr[:,:,2] == arr_max)
        out['hue'][idx] = 4. + (arr[idx, 0] - arr[idx, 1] ) / delta[idx]

        out['hue'] = (out['hue']/6.0) % 1.0
        out['light'] = l
        out['sat'] = s

        idx = (delta==0)
        out['sat'][idx] = 0.0
        out['hue'][idx] = 0.0

        # remove NaN
        flat = struct_flat(out)
        flat[np.isnan(flat)] = 0

    return out

lookup_entries = 4096

max_r = 0.9
max_g = 0.7
max_b = 1.0
max_y = 0.9

hue_lookup = ColorFade(
    [
        (max_r,     0,          0),
        (max_r,     max_y/2,    0),
        (max_r,     max_y,      0),
        (0,         max_g,      0),
        (0,         max_g,      max_b),
        (0,         0,          max_b),
        (max_r*0.5, 0,          max_b),
        (max_r*0.7, 0,          max_b),
        (max_r,     0,          0),
    ], lookup_entries)

def hls_to_rgb_perceptual(arr, out=None):

    # uncorrected/spectral RGB values don't produce a nice color space
    # this function attempts to produce something that has:
    #   * even brightness across hues
    #   * a hue curve closer to human concepts of rainbows

    # use lookup table based on hue
    hues = arr['hue']

    lookup_index = ((hues - hues.astype(np.int)) * lookup_entries).astype(np.int)

    out = hue_lookup.color_cache[lookup_index]
    outview = out.view(np.float64).reshape(out.shape + (-1,))

    # adjust L and S ...

    luminances = np.clip(arr['light'], 0, 1).reshape((3600,1))
    shades = np.clip(luminances * 2, 0, 1)
    outview *= shades
    pastels = np.clip(luminances * 2 - 1, 0, 1)
    outview += pastels
    grays = np.tile(np.clip(arr['light'], 0, 1),(3,1)).T
    saturations = np.clip(arr['sat'], 0, 1).reshape((3600,1))
    final = saturations*outview + (1-saturations)*grays

    return final.view(dtypes.rgb_color).reshape(arr.shape)







def hls_to_rgb(arr, out=None):
    """
    Converts HLS color array [[H,L,S]] to RGB array.

    http://en.wikipedia.org/wiki/HSL_and_HSV#From_HSL

    Returns [[R,G,B]] in [0..1]

    Adapted from: http://stackoverflow.com/questions/4890373/detecting-thresholds-in-hsv-color-space-from-rgb-using-python-pil/4890878#4890878
    """

    if out is None:
        out = np.zeros_like(arr, dtype=dtypes.rgb_color)
    else:
        assert "I believe there is a bug here. if an array is passed in, it needs to get zeroed"

    C = (1 - np.absolute(2 * arr['light'] - 1)) * arr['sat']

    Hp = arr['hue'] * 6.0
    i = Hp.astype(np.int)
    #f = Hp - i  # |H' mod 2|  ?

    X = C * (1 - np.absolute(np.mod(Hp, 2) - 1))
    #X = C * (1 - f)

    # handle each case:

    #mask = (Hp >= 0) == ( Hp < 1)
    mask = i % 6 == 0
    out['r'][mask] = C[mask]
    out['g'][mask] = X[mask]

    #mask = (Hp >= 1) == ( Hp < 2)
    mask = i == 1
    out['r'][mask] = X[mask]
    out['g'][mask] = C[mask]

    #mask = (Hp >= 2) == ( Hp < 3)
    mask = i == 2
    out['g'][mask] = C[mask]
    out['b'][mask] = X[mask]

    #mask = (Hp >= 3) == ( Hp < 4)
    mask = i == 3
    out['g'][mask] = X[mask]
    out['b'][mask] = C[mask]

    #mask = (Hp >= 4) == ( Hp < 5)
    mask = i == 4
    out['r'][mask] = X[mask]
    out['b'][mask] = C[mask]

    #mask = (Hp >= 5) == ( Hp < 6)
    mask = i == 5
    out['r'][mask] = C[mask]
    out['b'][mask] = X[mask]

    m = arr['light'] - 0.5*C
    out['r'] += m
    out['g'] += m
    out['b'] += m

    return out
