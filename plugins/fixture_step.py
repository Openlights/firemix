import numpy as np

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class FixtureStep(Transition):
    """
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Fixture Step"

    def reset(self):
        self.fixtures = self._app.scene.fixtures()
        buffer_size = BufferUtils.get_buffer_size()
        self.mask = np.tile(False, (buffer_size, 3))

        np.random.seed()
        self.rand_index = np.arange(len(self.fixtures))
        np.random.shuffle(self.rand_index)

        self.last_idx = 0

    def get(self, start, end, progress):
        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0

        idx = int(progress * len(self.rand_index))
        for i in range(self.last_idx, idx):
            fix = self.fixtures[self.rand_index[i]]
            pix_start, pix_end = BufferUtils.get_fixture_extents(fix.strand, fix.address)
            self.mask[pix_start:pix_end][:] = True
        self.last_idx = idx

        return (start) + (end)