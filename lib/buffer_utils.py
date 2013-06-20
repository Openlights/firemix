import numpy as np


class BufferUtils:
    """
    Utilities for working with frame buffers
    """
    _first_time = True
    _num_strands = 0
    _max_fixtures = 0
    _max_pixels_per_fixture = 0
    _max_pixels_per_strand = 0
    _buffer_length = 0
    _app = None
    _strand_lengths = {}
    _fixture_lengths = {}
    _fixture_extents = {}
    _fixture_pixels = {}
    _pixel_offset_cache = {}
    _pixel_index_cache = {}
    _pixel_logical_cache = {}

    @classmethod
    def init(cls, app):
        """
        Generates the caches and initializes local storage.  Must be called before any other methods.
        """
        cls._app = app
        cls._num_strands, cls._max_fixtures, cls._max_pixels_per_fixture = app.scene.get_matrix_extents()
        cls._max_pixels_per_strand = cls._max_fixtures * cls._max_pixels_per_fixture
        cls._buffer_length = cls._num_strands * cls._max_pixels_per_strand
        fh = app.scene.fixture_hierarchy()

        for strand in fh:
            cls._strand_lengths[strand] = 0
            for fixture in fh[strand]:
                fixture_length = app.scene.fixture(strand, fixture).pixels
                cls._strand_lengths[strand] += fixture_length
                cls._fixture_lengths[(strand, fixture)] = fixture_length

        for strand in fh:
            for fixture in fh[strand]:
                for offset in range(app.scene.fixture(strand, fixture).pixels):
                    cls.logical_to_index((strand, fixture, offset))

    @classmethod
    def logical_to_index(cls, logical_address, scene=None):
        """
        Given a logical (strand, fixture, offset) pixel address, returns the index
        into a 1-dimensional pixel list (the storage type for frames, locations, etc).
        """
        index = cls._pixel_index_cache.get(logical_address, None)

        if index is None:

            if scene is None:
                scene = cls._app.scene

            strand, fixture, offset = logical_address
            fh = scene.fixture_hierarchy()
            index = 0

            # (1) Skip to the start of the strand
            for i in range(strand):
                index += cls._strand_lengths[i]

            # (2) Skip to the fixture in question
            for i in range(fixture):
                index += scene.fixture(strand, i).pixels

            fixture_start = index
            fixture_end = index + scene.fixture(strand, fixture).pixels

            # (3) Add the offset along the fixture
            index += offset

            cls._pixel_index_cache[logical_address] = index
            cls._pixel_logical_cache[index] = logical_address
            cls._fixture_extents[(strand, fixture)] = (fixture_start, fixture_end)

            print logical_address, index

        return index

    @classmethod
    def index_to_logical(cls, index):
        """
        Given an index into a 1-dimensional pixel buffer, returns a (strand, fixture, offset) address.
        """
        logical = cls._pixel_logical_cache.get(index, None)
        if logical is None:
            raise ValueError("Index out of range")
        return logical

    @classmethod
    def create_buffer(cls):
        """
        Pixel buffers are 3D numpy arrays.  The axes are strand, pixel, and color.
        The "y" axis (pixel) uses expanded pixel addressing, "flattening" the fixture addresses.
        So, the address [1:2:0] (strand 1, fixture 2, pixel 0) is decoded to [1:64] assuming the
        fixtures all have 32 pixels.

        The reference to the app is required to lookup the required dimensions, in order
        to figure out the total y-axis length required.
        """
        return np.zeros((cls._buffer_length, 3), dtype=np.float32)

    @classmethod
    def get_buffer_size(cls):
        """
        Returns the length of a pixel index buffer
        """
        return (cls._buffer_length)

    @classmethod
    def get_buffer_address(cls, location, scene=None):
        """
        Calculates the in-buffer address for a given [s:f:p] address (see above)
        """
        if scene is None:
            scene = cls._app.scene

        pixel_offset = cls._pixel_offset_cache.get(location, None)
        if pixel_offset is None:
            strand, fixture, pixel = location
            pixel_offset = pixel
            for fixture_id in range(fixture):
                num_fixture_pixels = cls._fixture_pixels.get((strand, fixture), None)
                if num_fixture_pixels is None:
                    num_fixture_pixels = scene.fixture(strand, fixture).pixels
                    cls._fixture_pixels[(strand, fixture)] = num_fixture_pixels
                pixel_offset += num_fixture_pixels
            cls._pixel_offset_cache[location] = pixel_offset

        raise DeprecationWarning
        return (location[0], pixel_offset)

    @classmethod
    def get_fixture_extents(cls, strand, fixture):
        """
        Returns a tuple of (start, end) containing the buffer pixel addresses on a given fixtures
        """
        return cls._fixture_extents[(strand, fixture)]

    @classmethod
    def get_strand_length(cls, strand):
        """
        Returns the length of a strand (in pixels)
        """
        return cls._strand_lengths[strand]
