import numpy as np


from lib.transition import Transition


class DissolveTransition(Transition):
    """
    Implements a simple cross dissolve
    """

    def __init__(self):
        Transition.__init__(self)

    def setup(self):
        pass

    def get(self, start, end, progress):
        pass