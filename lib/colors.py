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