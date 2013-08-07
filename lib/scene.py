import os
import math
import logging
import numpy as np

from lib.json_dict import JSONDict
from lib.fixture import Fixture
from lib.buffer_utils import BufferUtils

log = logging.getLogger("firemix.lib.scene")

class Scene(JSONDict):
    """
    Basic model for a scene.
    """

    def __init__(self, app):
        self._app = app
        self._name = app.args.scene
        self._filepath = os.path.join(os.getcwd(), "data", "scenes", "".join([self._name, ".json"]))
        JSONDict.__init__(self, 'scene', self._filepath, False)

        self._fixtures = None
        self._fixture_dict = {}
        self._fixture_hierarchy = None
        self._colliding_fixtures_cache = {}
        self._pixel_neighbors_cache = {}
        self._pixel_locations_cache = {}
        self._pixel_distance_cache = {}
        self._intersection_points = None
        self._all_pixels = None
        self._all_pixel_locations = None
        self._all_pixels_raw = None

    def warmup(self):
        """
        Warms up caches
        """
        log.info("Warming up scene caches...")
        fh = self.fixture_hierarchy()
        for strand in fh:
            for fixture in fh[strand]:
                self.get_colliding_fixtures(strand, fixture)
                for pixel in range(self.fixture(strand, fixture).pixels):
                    index = BufferUtils.logical_to_index((strand, fixture, pixel))
                    neighbors = self.get_pixel_neighbors(index)
                    self.get_pixel_location(index)
                    for neighbor in neighbors:
                        self.get_pixel_distance(index, neighbor)
        self.get_fixture_bounding_box()
        self.get_intersection_points()
        self.get_all_pixels_logical()
        #self.get_all_pixels()
        #self.get_all_pixel_locations()
        log.info("Done")

    def extents(self):
        """
        Returns the (x, y) extents of the scene.  Useful for determining
        relative position of fixtures to some reference point.
        """
        return tuple(self.data.get("extents", (0, 0)))

    def center_point(self):
        """
        Returns the (x, y) centroid of all fixtures in the scene
        """
        center = self.data.get("center", None)
        if center is None:
            bb = self.get_fixture_bounding_box()
            center = ((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0)
        else:
            center = tuple(center)
        return center

    def name(self):
        return self.data.get("name", "")

    def get_strand_settings(self):
        return self.data.get("strand-settings", [])

    def set_strand_settings(self, settings):
        self.data["strand-settings"] = settings

    def fixtures(self):
        """
        Returns a flat list of all fixtures in the scene.
        """
        if self._fixtures is None:
            self._fixtures = [Fixture(fd) for fd in self.data["fixtures"]]
        return self._fixtures

    def fixture(self, strand, address):
        """
        Returns a reference to a given fixture
        """
        fix = self._fixture_dict.get((strand, address), None)
        if fix is None:
            for f in self.fixtures():
                if f.strand == strand and f.address == address:
                    fix = f
                    self._fixture_dict[(strand, address)] = f
        return fix

    def fixture_hierarchy(self):
        """
        Returns a dict of all strands, containing dicts of all fixtures on the strand.
        """
        if self._fixture_hierarchy is None:
            self._fixture_hierarchy = dict()
            for f in self.fixtures():
                if not self._fixture_hierarchy.get(f.strand, None):
                    self._fixture_hierarchy[f.strand] = dict()
                self._fixture_hierarchy[f.strand][f.address] = f
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
                if fh[strand][fixture].pixels > pixels:
                    pixels = fh[strand][fixture].pixels

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
            center = f.pos1
        elif loc == 'end':
            center = f.pos2
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
                x2, y2 = tf.pos1
                if pow(x2 - x1, 2) + pow(y2 - y1, 2) <= r2:
                    #print tf, "collides with", strand, address
                    colliding.append((tf.strand, tf.address, 0))
                    continue
                    # Match end point
                x2, y2 = tf.pos2
                if pow(x2 - x1, 2) + pow(y2 - y1, 2) <= r2:
                    #print tf, "collides with", strand, address, "backwards"
                    colliding.append((tf.strand, tf.address, tf.pixels - 1))

            self._colliding_fixtures_cache[(strand, address, loc)] = colliding

        return colliding

    def get_pixel_neighbors(self, index):
        """
        Returns a list of pixel addresses that are adjacent to the given address.
        """

        neighbors = self._pixel_neighbors_cache.get(index, None)

        if neighbors is None:
            neighbors = []
            strand, address, pixel = BufferUtils.index_to_logical(index)
            f = self.fixture(strand, address)
            neighbors = [BufferUtils.logical_to_index((strand, address, p)) for p in f.pixel_neighbors(pixel)]

            if (pixel == 0) or (pixel == f.pixels - 1):
                # If this pixel is on the end of a fixture, consider the neighboring fixtures
                loc = 'end'
                if pixel == 0:
                    loc = 'start'

                logical_neighbors = self.get_colliding_fixtures(strand, address, loc)
                neighbors += [BufferUtils.logical_to_index(n) for n in logical_neighbors]

            self._pixel_neighbors_cache[index] = neighbors

        return neighbors

    def get_pixel_location(self, index):
        """
        Returns a given pixel's location in scene coordinates.
        """
        loc = self._pixel_locations_cache.get(index, None)

        if loc is None:

            strand, address, pixel = BufferUtils.index_to_logical(index)
            f = self.fixture(strand, address)

            if pixel == 0:
                loc = f.pos1
            elif pixel == (f.pixels - 1):
                loc = f.pos2
            else:
                x1, y1 = f.pos1
                x2, y2 = f.pos2
                scale = float(pixel) / f.pixels
                relx, rely = ((x2 - x1) * scale, (y2 - y1) * scale)
                loc = (x1 + relx, y1 + rely)

            self._pixel_locations_cache[index] = loc

        return loc

    def get_pixel_distance(self, first, second):
        """
        Calculates the distance (in scene coordinate units) between two pixels
        """
        dist = self._pixel_distance_cache.get((first, second), None)
        if dist is None:
            first_loc = self.get_pixel_location(first)
            second_loc = self.get_pixel_location(second)
            dist = self.get_point_distance(first_loc, second_loc)
            self._pixel_distance_cache[(first, second)] = dist
            self._pixel_distance_cache[(second, first)] = dist
        return dist

    def get_point_distance(self, first, second):
        return math.fabs(math.sqrt(math.pow(second[0] - first[0], 2) + math.pow(second[1] - first[1], 2)))

    def get_all_pixels_logical(self):
        """
        Returns all the pixel addresses in the scene (in logical strand, fixture, offset tuples)
        """
        if self._all_pixels is None:
            addresses = []
            for f in self.fixtures():
                for pixel in xrange(f.pixels):
                    addresses.append((f.strand, f.address, pixel))
            self._all_pixels = addresses
        return self._all_pixels

    def get_all_pixels(self):
        """
        Returns a list of all pixels in buffer address format (strand, offset)
        """
        if self._all_pixels_raw is None:
            all_pixels = []
            for s, a, p in self.get_all_pixels_logical():
                #pxs.append(BufferUtils.get_buffer_address((s, a, p), scene=self))
                all_pixels.append(BufferUtils.logical_to_index((s, a, p), scene=self))
            all_pixels = sorted(all_pixels)
            self._all_pixels_raw = all_pixels

        return self._all_pixels_raw

    def get_all_pixel_locations(self):
        """
        Returns a numpy array of (x, y) pairs.
        """
        if self._all_pixel_locations is None:
            pixels = self.get_all_pixels()
            pixel_location_list = []
            for pixel in pixels:
                pixel_location_list.append(self.get_pixel_location(pixel))

            self._all_pixel_locations = np.asarray(pixel_location_list)
        return np.copy(self._all_pixel_locations)


    def get_fixture_bounding_box(self):
        """
        Returns the bounding box containing all fixtures in the scene
        Return value is a tuple of (xmin, ymin, xmax, ymax)
        """
        xmin = 999999
        xmax = -999999
        ymin = 999999
        ymax = -999999

        fh = self.fixture_hierarchy()
        for strand in fh:
            for fixture in fh[strand]:
                for pixel in range(self.fixture(strand, fixture).pixels):
                    x, y = self.get_pixel_location(BufferUtils.logical_to_index((strand, fixture, pixel)))
                    if x < xmin:
                        xmin = x
                    if x > xmax:
                        xmax = x
                    if y < ymin:
                        ymin = y
                    if y > ymax:
                        ymax = y

        return (xmin, ymin, xmax, ymax)

    def get_intersection_points(self, threshold=50):
        """
        Returns a list of points in scene coordinates that represent the average location of
        each intersection of two or more fixture endpoints.

        For each fixture endpoint, all other endpoints are compared to see if they fall within a certain distance
        of the given endpoint.  This loop generates a list of groups.  Then, the average location of each
        group is calculated and returned.
        """
        if self._intersection_points is None:

            endpoints = []
            for f in self.fixtures():
                endpoints.append(f.pos1)
                endpoints.append(f.pos2)

            groups = []
            while len(endpoints) > 0:
                endpoint = endpoints.pop()
                group = [endpoint]
                to_remove = []
                for other in endpoints:
                    dx, dy = (other[0] - endpoint[0], other[1] - endpoint[1])
                    dist = math.fabs(math.sqrt(math.pow(dx, 2) + math.pow(dy, 2)))
                    if (dist < threshold):
                        group.append(other)
                        to_remove.append(other)
                endpoints = [e for e in endpoints if e not in to_remove]
                groups.append(group)

            centroids = []
            for group in groups:
                num_points = len(group)
                tx = 0
                ty = 0
                for point in group:
                    tx += point[0]
                    ty += point[1]
                centroids.append((tx / num_points, ty / num_points))
            self._intersection_points = centroids

        return self._intersection_points