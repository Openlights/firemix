from lib.colors import hsl_blend
from lib.transition import Transition

class Dissolve(Transition):

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Dissolve"

    def get(self, start, end, progress, fade_length = 1.0):

        return hsl_blend(start, end, progress, 'multiply', fade_length)