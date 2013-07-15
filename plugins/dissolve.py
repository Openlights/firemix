from lib.colors import hls_blend
from lib.transition import Transition

class Dissolve(Transition):

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Dissolve"

    def get(self, start, end, progress, fade_length = 1.0):

        return hls_blend(start, end, progress, 'add', fade_length, 1.0)