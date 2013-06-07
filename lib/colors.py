import colorsys


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