


class Preset:
    """Base Preset.  Does nothing."""

    def __init__(self, mixer):
        self._mixer = mixer

    def setup(self):
        """Override this method to run any init code your preset needs."""
        pass

    def tick(self):
        """Override this method to draw the output of your preset.  It will be called each tick."""
        pass

    def tick_rate(self):
        return self._mixer.tick_rate
