import unittest

from lib.fixture import Fixture


class Scene:
    """
    Basic model for a scene.
    """

    def __init__(self, data):
        self._data = data
        self._fixtures = None
        self._fixture_hierarchy = None
        self._colliding_fixtures_cache = {}
        self._pixel_neighbors_cache = {}
        self._pixel_locations_cache = {}

    def extents(self):
        """
        Returns the (x, y) extents of the scene.  Useful for determining
        relative position of fixtures to some reference point.
        """
        return tuple(self._data.get("extents", (0, 0)))

    def name(self):
        return self._data.get("name", "")

    def fixtures(self):
        """
        Returns a flat list of all fixtures in the scene.
        """
        if self._fixtures is None:
            self._fixtures = [Fixture(fd) for fd in self._data["fixtures"]]
        return self._fixtures

    def fixture(self, strand, address):
        """
        Returns a reference to a given fixture
        """
        for f in self.fixtures():
            if f.strand() == strand and f.address() == address:
                return f
        return None

    def fixture_hierarchy(self):
        """
        Returns a dict of all strands, containing dicts of all fixtures on the strand.
        """
        if self._fixture_hierarchy is None:
            self._fixture_hierarchy = dict()
            for f in self.fixtures():
                if not self._fixture_hierarchy.get(f.strand(), None):
                    self._fixture_hierarchy[f.strand()] = dict()
                self._fixture_hierarchy[f.strand()][f.address()] = f
        return self._fixture_hierarchy

    def get_matrix_extents(self):
        """
        Returns a tuple of (strands, fixtures, pixels) indicating the maximum extents needed
        for a regular 3D matrix of pixels.
        """
        fh = self.fixture_hierarchy()
        strands = len(fh)
        fixtures = 0
        pixels = 0
        for strand in fh:
            if len(fh[strand]) > fixtures:
                fixtures = len(fh[strand])
            for fixture in fh[strand]:
                if fh[strand][fixture].pixels() > pixels:
                    pixels = fh[strand][fixture].pixels()

        return (strands, fixtures, pixels)

    def get_colliding_fixtures(self, strand, address, loc='start', radius=50):
        """
        Returns a list of (strand, fixture, pixel) tuples containing the addresses of any fixtures that collide with the
        input fixture.  Pixel is set to the closest pixel to the target location (generally either the first or last
        pixel).  The collision bound is a circle given by the radius input, centered on the specified fixture endpoint.

        Location to collide: 'start' == pos1, 'end' == pos2, 'midpoint' == midpoint
        """
        f = self.fixture(strand, address)

        if loc == 'start':
            center = f.pos1()
        elif loc == 'end':
            center = f.pos2()
        elif loc == 'midpoint':
            center = f.midpoint()
        else:
            raise ValueError("loc must be one of 'start', 'end', 'midpoint'")

        colliding = self._colliding_fixtures_cache.get((strand, address, loc), None)

        if colliding is None:
            colliding = []
            r2 = pow(radius, 2)
            x1, y1 = center
            for tf in self.fixtures():
                # Match start point
                x2, y2 = tf.pos1()
                if pow(x2 - x1, 2) + pow(y2 - y1, 2) <= r2:
                    #print tf, "collides with", strand, address
                    colliding.append((tf.strand(), tf.address(), 0))
                    continue
                    # Match end point
                x2, y2 = tf.pos2()
                if pow(x2 - x1, 2) + pow(y2 - y1, 2) <= r2:
                    #print tf, "collides with", strand, address, "backwards"
                    colliding.append((tf.strand(), tf.address(), tf.pixels() - 1))

            self._colliding_fixtures_cache[(strand, address, loc)] = colliding

        return colliding

    def get_pixel_neighbors(self, addr):
        """
        Returns a list of pixel addresses that are adjacent to the given address.
        An address is a tuple of (strand, fixture, pixel).
        """

        neighbors = self._pixel_neighbors_cache.get(addr, None)

        if neighbors is None:
            neighbors = []
            strand, address, pixel = addr
            f = self.fixture(strand, address)
            neighbors = [(strand, address, p) for p in f.pixel_neighbors(pixel)]

            if (pixel == 0) or (pixel == f.pixels() - 1):
                # If this pixel is on the end of a fixture, consider the neighboring fixtures
                loc = 'end'
                if pixel == 0:
                    loc = 'start'

                neighbors += self.get_colliding_fixtures(strand, address, loc)

            self._pixel_neighbors_cache[addr] = neighbors

        return neighbors

    def get_pixel_location(self, addr):
        """
        Returns a given pixel's location in scene coordinates.
        """
        loc = self._pixel_locations_cache.get(addr, None)

        if loc is None:
            strand, address, pixel = addr
            f = self.fixture(strand, address)

            if pixel == 0:
                loc = f.pos1()
            elif pixel == (f.pixels() - 1):
                loc = f.pos2()
            else:
                x1, y1 = f.pos1()
                x2, y2 = f.pos2()
                scale = float(pixel) / f.pixels()
                relx, rely = ((x2 - x1) * scale, (y2 - y1) * scale)
                loc = (x1 + relx, y1 + rely)

            self._pixel_locations_cache[addr] = loc

        return loc