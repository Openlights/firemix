import numpy as np
import math

from lib.transition import Transition

class Wipe(Transition):
    """
    Implements a simple wipe
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Wipe"

    def reset(self):
        angle = np.random.random() * np.pi * 2.0
        self.wipe_vector = np.zeros((2))

        self.wipe_vector[0] = math.cos(angle)
        self.wipe_vector[1] = math.sin(angle)

        self.locations = self._app.scene.get_all_pixel_locations()

        self.dots = np.dot(self.locations, self.wipe_vector)
        maxDot = max(self.dots)
        minDot = min(self.dots)
        self.dots -= minDot
        self.dots /= maxDot - minDot

    def get(self, start, end, progress):
        buffer = np.where(self.dots < progress, end.T, start.T)
        buffer[1][np.abs(self.dots - progress) < 0.02] += 0.5 # we can apply effects to transition line here
        buffer = buffer.T

        return buffer
