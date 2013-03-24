def constant(lights, color):
    """
    lights: see Preset.add_ticker
    color: (r,g,b) tuple
    """
    def ret(ticks, time):
        yield(lights, color)

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

def flash(light, color, on, off):
    """
    flashes color for [on] seconds, then off for [off] seconds, repeating.
    """

    def ret(ticks, elapsed_time):
        if (elapsed_time % (on+off)) < on:
            yield(light, color)

    return ret

def offset(ticker, offset):
    """
    given a ticker, offsets it by the given number of seconds
    """
    def ret(ticks, elapsed_time):
        for output in ticker(ticks, elapsed_time+offset):
            yield(output)

    return ret

def speed(ticker, multiple):
    """
    given a ticker, speeds/slows it by multiple. e.g. if multiple=5, it will
    run 5 times as fast.
    """
    def ret(ticks, elapsed_time):
        for output in ticker(ticks, elapsed_time*multiple):
            yield(output)

    return ret