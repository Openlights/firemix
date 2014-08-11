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


def blend_to_buffer(source, destination, progress, mode):
    h1,l1,s1 = source.T
    h2,l2,s2 = destination.T

    if mode == 'overwrite':
        not_dark = l1 > 0.0
        destination[not_dark] = source[not_dark]
    else:
        raise NotImplementedError

    return destination

def hls_blend(start, end, output_buffer, progress, mode, fade_length=1.0, ease_power=0.5):

    p = abs(progress)

    startPower = (1.0 - p) / fade_length
    startPower = clip(0.0, startPower, 1.0)
    startPower = pow(startPower, ease_power)

    endPower = p / fade_length
    endPower = clip(0.0, endPower, 1.0)
    endPower = pow(endPower, ease_power)

    h1,l1,s1 = start.T
    h2,l2,s2 = end.T

    np.clip(l1,0,1,l1)
    np.clip(l2,0,1,l2)
    np.clip(s1,0,1,s1)
    np.clip(s2,0,1,s2)

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

    if output_buffer is not None:
        frame = output_buffer
        frame[:, 0] = h
        frame[:, 1] = l
        frame[:, 2] = s
    else:
        frame = np.asarray([h, l, s]).T

    return frame

def rgb_to_hls(arr):
    """ fast rgb_to_hls using numpy array """

    # adapted from Arnar Flatberg
    # http://www.mail-archive.com/numpy-discussion@scipy.org/msg06147.html

    arr = arr.astype("float32") / 255.0
    out = np.empty_like(arr)

    arr_max = arr.max(-1)
    delta = arr.ptp(-1)
    arr_min = arr.min(-1)
    total = arr_max + arr_min

    l = total / 2.0

    s = delta / total
    idx = (l > 0.5)
    s[idx] = delta[idx] / (2.0 - total[idx])

    # red is max
    idx = (arr[:,:,0] == arr_max)
    out[idx, 0] = (arr[idx, 1] - arr[idx, 2]) / delta[idx]

    # green is max
    idx = (arr[:,:,1] == arr_max)
    out[idx, 0] = 2. + (arr[idx, 2] - arr[idx, 0] ) / delta[idx]

    # blue is max
    idx = (arr[:,:,2] == arr_max)
    out[idx, 0] = 4. + (arr[idx, 0] - arr[idx, 1] ) / delta[idx]

    out[:,:,0] = (out[:,:,0]/6.0) % 1.0
    out[:,:,1] = l
    out[:,:,2] = s

    idx = (delta==0)
    out[idx, 2] = 0.0
    out[idx, 0] = 0.0

    # remove NaN
    out[np.isnan(out)] = 0

    return out

def hls_to_rgb(hls):
    """
    Converts HLS color array [[H,L,S]] to RGB array.

    http://en.wikipedia.org/wiki/HSL_and_HSV#From_HSL

    Returns [[R,G,B]] in [0..1]

    Adapted from: http://stackoverflow.com/questions/4890373/detecting-thresholds-in-hsv-color-space-from-rgb-using-python-pil/4890878#4890878
    """

    H = hls[:, 0]
    L = hls[:, 1]
    S = hls[:, 2]

    C = (1 - np.absolute(2 * L - 1)) * S

    Hp = H * 6.0
    i = Hp.astype(np.int)
    #f = Hp - i  # |H' mod 2|  ?

    X = C * (1 - np.absolute(np.mod(Hp, 2) - 1))
    #X = C * (1 - f)

    # initialize with zero
    R = np.zeros(H.shape, float)
    G = np.zeros(H.shape, float)
    B = np.zeros(H.shape, float)

    # handle each case:

    #mask = (Hp >= 0) == ( Hp < 1)
    mask = i % 6 == 0
    R[mask] = C[mask]
    G[mask] = X[mask]

    #mask = (Hp >= 1) == ( Hp < 2)
    mask = i == 1
    R[mask] = X[mask]
    G[mask] = C[mask]

    #mask = (Hp >= 2) == ( Hp < 3)
    mask = i == 2
    G[mask] = C[mask]
    B[mask] = X[mask]

    #mask = (Hp >= 3) == ( Hp < 4)
    mask = i == 3
    G[mask] = X[mask]
    B[mask] = C[mask]

    #mask = (Hp >= 4) == ( Hp < 5)
    mask = i == 4
    R[mask] = X[mask]
    B[mask] = C[mask]

    #mask = (Hp >= 5) == ( Hp < 6)
    mask = i == 5
    R[mask] = C[mask]
    B[mask] = X[mask]

    m = L - 0.5*C
    R += m
    G += m
    B += m

    rgb = np.empty_like(hls)
    rgb[:, 0] = R
    rgb[:, 1] = G
    rgb[:, 2] = B
    return rgb
