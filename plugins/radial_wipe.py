import numpy as np
import math

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class RadialWipe(Transition):
    """
    Implements a radial wipe (Iris) transition
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Radial Wipe"

    def reset(self):
        locations = self._app.scene.get_all_pixel_locations()
        locations -= self._app.scene.center_point()
        #locations -= locations[np.random.randint(0, len(locations) - 1)]
        locations = np.square(locations)
        self.distances = locations.T[0] + locations.T[1]
        self.distances /= max(self.distances)

    def get(self, start, end, progress):
        buffer = np.where(self.distances < progress, end.T, start.T)
        buffer[1][np.abs(self.distances - progress) < 0.02] += 0.5 # we can apply effects to transition line here

        return buffer.T