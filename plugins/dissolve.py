from lib.transition import Transition


class Dissolve(Transition):
    """
    Implements a simple cross dissolve
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Dissolve"

    def get(self, start, end, progress):
        """
        Simple dissolve
        """
        return (start * (1.0 - progress)) + (end * progress)