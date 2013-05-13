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

    def setup(self):
        x, y = BufferUtils.get_buffer_size(self._app)
        self.mask = np.tile(False, (x, y, 3))

        self.fixtures = self._app.scene.fixtures()
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
            pix_start, pix_end = BufferUtils.get_fixture_extents(self._app, fix.strand, fix.address)
            for i in range(pix_start, pix_end):
                self.mask[fix.strand][i][:] = True
        self.last_idx = idx

        return (start) + (end)