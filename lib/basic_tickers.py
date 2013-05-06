from lib.parameters import Parameter


def constant(lights, color):
    """
    lights: see Preset.add_ticker
    color: (r,g,b) tuple
    """
    def ret(ticks, time):
        if isinstance(color, Parameter):
            c = color.get()
        else:
            c = color
        yield(lights, c)

    return ret

def fade(lights, colorfade):
    """
    fades along the colorfade with a total duration of 1 second (use speed() to
    alter time)

    lights: see Preset.add_ticker
    colorfade: a ColorFade
    """

    def ret(ticks, elapsed_time):
        yield(lights, colorfade.get_color(elapsed_time % 1))

    return ret

def flash(light, color, p_on, p_off):
    """
    flashes color for [on] seconds, then off for [off] seconds, repeating.
    """

    def ret(ticks, elapsed_time):
        if isinstance(p_on, Parameter):
            on = p_on.get()
        else:
            on = p_on
        if isinstance(p_off, Parameter):
            off = p_off.get()
        else:
            off = p_off
        if (elapsed_time % (on + off)) < on:
            yield(light, color)

    return ret

def offset(ticker, offset):
    """
    given a ticker, offsets it by the given number of seconds
    """
    def ret(ticks, elapsed_time):
        if isinstance(offset, Parameter):
            o = offset.get()
        else:
            o = offset
        for output in ticker(ticks, elapsed_time + o):
            yield(output)

    return ret

def speed(ticker, multiple):
    """
    given a ticker, speeds/slows it by multiple. e.g. if multiple=5, it will
    run 5 times as fast.
    """
    def ret(ticks, elapsed_time):
        if isinstance(multiple, Parameter):
            m = multiple.get()
        else:
            m = multiple
        for output in ticker(ticks, elapsed_time * m):
            yield(output)

    return ret

def callback(fn, interval):
    """
    Registers a callback in your preset to be called at a given rate (in seconds).
    This can be useful for presets that change behaviors over time.
    """
    def ret(ticks, time):
        if isinstance(interval, Parameter):
            i = interval.get()
        else:
            i = interval
        if (time > 0 and (time - ret.last_time > i)):
            fn()
            ret.last_time = time
        yield(None, None)

    ret.last_time = 0.0

    return ret