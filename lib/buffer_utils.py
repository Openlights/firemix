import numpy as np


class BufferUtils:
    """
    Utilities for working with frame buffers
    """
    _first_time = True
    _num_strands = 0
    _max_fixtures = 0
    _max_pixels = 0
    _strand_lengths = []
    _fixture_pixels = {}
    _pixel_offset_cache = {}

    @classmethod
    def warmup(cls, app):
        """
        Generates the caches
        """
        fh = app.scene.fixture_hierarchy()
        for strand in fh:
            for fixture in fh[strand]:
                for pixel in range(app.scene.fixture(strand, fixture).pixels):
                    cls.get_buffer_address(app, (strand, fixture, pixel))

    @classmethod
    def create_buffer(cls, app):
        """
        Pixel buffers are 3D numpy arrays.  The axes are strand, pixel, and color.
        The "y" axis (pixel) uses expanded pixel addressing, "flattening" the fixture addresses.
        So, the address [1:2:0] (strand 1, fixture 2, pixel 0) is decoded to [1:64] assuming the
        fixtures all have 32 pixels.

        The reference to the app is required to lookup the required dimensions, in order
        to figure out the total y-axis length required.
        """
        if cls._first_time:
            cls._num_strands, cls._max_fixtures, cls._max_pixels = app.scene.get_matrix_extents()

        return np.zeros((cls._num_strands, cls._max_fixtures * cls._max_pixels, 3), dtype=np.float32)

    @classmethod
    def get_buffer_size(cls, app):
        if cls._first_time:
            cls._num_strands, cls._max_fixtures, cls._max_pixels = app.scene.get_matrix_extents()

        return (cls._num_strands, cls._max_fixtures * cls._max_pixels)

    @classmethod
    def get_buffer_address(cls, app, location):
        """
        Calculates the in-buffer address for a given [s:f:p] address (see above)
        """

        pixel_offset = cls._pixel_offset_cache.get(location, None)
        if pixel_offset is None:
            strand, fixture, pixel = location
            pixel_offset = pixel
            for fixture_id in range(fixture):
                num_fixture_pixels = cls._fixture_pixels.get((strand, fixture), None)
                if num_fixture_pixels is None:
                    num_fixture_pixels = app.scene.fixture(strand, fixture).pixels
                    cls._fixture_pixels[(strand, fixture)] = num_fixture_pixels
                pixel_offset += num_fixture_pixels
            cls._pixel_offset_cache[location] = pixel_offset

        return (location[0], pixel_offset)

    @classmethod
    def get_fixture_extents(cls, app, strand, fixture):
        """
        Returns a tuple of (start, end) containing the buffer pixel addresses on a given fixtures
        """
        _, start_offset = cls.get_buffer_address(app, (strand, fixture, 0))
        num_pixels = app.scene.fixture(strand, fixture).pixels
        return (start_offset, start_offset + num_pixels)

    @classmethod
    def get_strand_length(cls, app, strand):
        """
        Returns the length of a strand (in pixels)
        """
        fixtures = [f for f in app.scene.fixtures() if f.strand == strand]

        num_pixels = 0
        for f in fixtures:
            num_pixels += f.pixels

        return num_pixels
