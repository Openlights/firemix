import colorsys
import numpy as np

def float_to_uint8(float_color):
    """
    Converts a float color (0 to 1.0) to uint8 (0 to 255)
    """
    return tuple(map(lambda x: int(255.0 * x), float_color))

def uint8_to_float(uint8_color):
    """
    Converts a uint8 color (0 to 255) to float (0 to 1.0)
    """
    return tuple(map(lambda x: float(x) / 255.0, uint8_color))

def rgb_uint8_to_hsv_float(rgb_color):
    return colorsys.rgb_to_hsv(*uint8_to_float(rgb_color))

def hsv_float_to_rgb_uint8(hsv_color):
    return float_to_uint8(colorsys.hsv_to_rgb(*hsv_color))

def clip(low, input, high):
    return min(max(input, low), high)

def hsl_blend(start, end, progress, mode, fade_length=0.5):

    ease_power = 2.0

    p = abs(progress)
    startPower = (1.0 - p) / fade_length if p >= (1 - fade_length) else 1.0
    startPower = 1.0 - pow(1.0 - startPower, ease_power)

    endPower = (p / fade_length) if p <= fade_length else 1.0
    endPower = 1.0 - pow(1.0 - endPower, ease_power)

    h1,l1,s1 = start.T
    h2,l2,s2 = end.T

    np.clip(l1,0,1,l1)
    np.clip(l2,0,1,l2)
    np.clip(s1,0,1,s1)
    np.clip(s2,0,1,s2)
    h1 = np.mod(h1, 1.0)
    h2 = np.mod(h2, 1.0)

    startWeight = (1.0 - 2 * np.abs(0.5 - l1)) * s1
    endWeight = (1.0 - 2 * np.abs(0.5 - l2)) * s2

    s = (s1 * startPower + s2 * endPower)
    x1 = np.cos(2 * np.pi * h1) * startPower * startWeight
    x2 = np.cos(2 * np.pi * h2) * endPower * endWeight
    y1 = np.sin(2 * np.pi * h1) * startPower * startWeight
    y2 = np.sin(2 * np.pi * h2) * endPower * endWeight
    x = x1 + x2
    y = y1 + y2

    if progress >= 0:
        l = np.maximum(l1 * startPower, l2 * endPower)
        opposition = np.sqrt(np.square((x1-x2)/2) + np.square((y1-y2)/2))
        if mode == 'multiply':
            l -= opposition
        elif mode == 'add':
            l = np.maximum(l, opposition, l)
    else: # hacky support for old blend
        l = np.sqrt(np.square(x) + np.square(y)) / 2

    h = np.arctan2(y, x) / (2*np.pi)

    nocolor = (x * y == 0)
    np.where(nocolor, h, 0)
    np.where(nocolor, s, 0)

    np.clip(l, 0, 1, l)

    frame = np.asarray([h, l, s]).T

    return frame