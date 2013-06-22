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

    def reset(self):
        self.buffer_size = BufferUtils.get_buffer_size()
        self.mask = np.tile(False, (self.buffer_size, 3))

        num_elements = np.ndarray.flatten(self.mask).size / 3
        np.random.seed()
        self.rand_index = np.arange(num_elements)
        np.random.shuffle(self.rand_index)

        self.last_idx = 0


    def get(self, start, end, progress):
        idx = int(progress * len(self.rand_index))
        for i in range(self.last_idx, idx):
            offset = self.rand_index[i] * 3
            self.mask.flat[offset] = True
            self.mask.flat[offset + 1] = True
            self.mask.flat[offset + 2] = True
        self.last_idx = idx

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0

        return (start) + (end)