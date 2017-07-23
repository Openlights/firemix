# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

from builtins import range
from builtins import object
import numpy as np

import lib.dtypes as dtypes

def struct_flat(arr):
    """
    Returns a flattened view of a structured array whose structure elements
    are of a homogeneous type
    """
    return arr.view(dtype=arr.dtype[0])


class BufferUtils(object):
    """
    Utilities for working with frame buffers
    """
    _first_time = True
    num_strands = 0
    max_fixtures = 0
    _max_pixels_per_fixture = 0
    _max_pixels_per_strand = 0
    _buffer_length = 0
    _app = None
    _strand_lengths = {}
    _strand_num_fixtures = {}
    _fixture_lengths = {}
    _fixture_extents = {}
    _fixture_pixels = {}
    _pixel_offset_cache = {}
    _pixel_index_cache = {}
    _pixel_logical_cache = {}

    @classmethod
    def set_app(cls, app):
        cls._app = app

    @classmethod
    def init(cls):
        """
        Generates the caches and initializes local storage.  Must be called before any other methods.
        """
        cls.num_strands, cls._max_pixels_per_strand = cls._app.scene.get_matrix_extents()
        cls._buffer_length = cls.num_strands * cls._max_pixels_per_strand
        fh = cls._app.scene.fixture_hierarchy()

        for strand in fh:
            cls._strand_lengths[strand] = sum([fh[strand][f].pixels for f in fh[strand]])

        for strand in fh:
            cls._strand_num_fixtures[strand] = len(fh[strand])
            for fixture in fh[strand]:
                for offset in range(cls._app.scene.fixture(strand, fixture).pixels):
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
            num_pixels = scene.fixture(strand, fixture).pixels
            fixture_end = index + num_pixels

            # (3) Add the offset along the fixture
            index += offset
            if index < 0 or index >= cls._buffer_length:
                raise ValueError("Logical address results in index out of range: "
                                 "%s => %d" % (repr(logical_address), index,))

            cls._pixel_index_cache[logical_address] = index
            cls._pixel_logical_cache[index] = logical_address
            cls._fixture_extents[(strand, fixture)] = (fixture_start, fixture_end)
            cls._fixture_pixels[(strand, fixture)] = num_pixels

        return index

    @classmethod
    def index_to_logical(cls, index):
        """
        Given an index into a 1-dimensional pixel buffer, returns a (strand, fixture, offset) address.
        """
        logical = cls._pixel_logical_cache.get(index, None)
        if logical is None:
            raise ValueError("Index out of range: %s" % repr(index))
        return logical

    @classmethod
    def create_buffer(cls):
        """
        Pixel buffers are numpy arrays of pixel colors, indexed using linear pixel addressing.

        The reference to the app is required to lookup the required dimensions, in order
        to figure out the total y-axis length required.
        """
        return np.zeros(cls._buffer_length, dtype=dtypes.pixel_color)

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

    @classmethod
    def get_strand_extents(cls, strand):
        start = 0
        for i in range(strand):
            start += cls._strand_lengths[i]

        return (start, start + cls._strand_lengths[strand])

    @classmethod
    def strand_num_fixtures(cls, strand):
        return cls._strand_num_fixtures[strand]

    @classmethod
    def fixture_length(cls, strand, fixture):
        return cls._fixture_pixels[(strand, fixture)]
