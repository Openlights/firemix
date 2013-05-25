import numpy as np

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class Fuzz(Transition):
    """
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Fuzz"

    def setup(self):
        self.reset()

    def reset(self):
        x, y = BufferUtils.get_buffer_size(self._app)
        self.mask = np.tile(False, (x, y, 3))

        num_elements = np.ndarray.flatten(self.mask).size
        np.random.seed()
        self.rand_index = np.arange(num_elements)
        np.random.shuffle(self.rand_index)

        self.last_idx = 0


    def get(self, start, end, progress):
        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0

        idx = int(progress * len(self.rand_index))
        for i in range(self.last_idx, idx):
            self.mask.flat[self.rand_index[i]] = True
        self.last_idx = idx

        return (start) + (end)