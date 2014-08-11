import random
import math
import numpy as np
from lib.colors import hls_blend
from PySide.QtGui import QPixmap

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, StringParameter
from lib.colors import rgb_to_hls

class ImagePreset(RawPreset):
    def setup(self):
        self.add_parameter(FloatParameter('speed-rotation', 0.1))
        self.add_parameter(FloatParameter('speed-hue', 0.0))
        self.add_parameter(FloatParameter('center-orbit-distance', 0.0))
        self.add_parameter(FloatParameter('center-orbit-speed', 0.1))
        self.add_parameter(StringParameter('image-file', ""))
        self.add_parameter(StringParameter('edge-mode', "clamp")) # mirror, tile, clamp
        self.add_parameter(FloatParameter('center-x', 0.0))
        self.add_parameter(FloatParameter('center-y', 0.0))
        self.add_parameter(FloatParameter('scale', 1.0))
        self.add_parameter(FloatParameter('ghost', 0.0))
        self.add_parameter(FloatParameter('beat-lum-boost', 0.1))
        self.add_parameter(FloatParameter('beat-lum-time', 0.05))

        self.pixel_locations = self.scene().get_all_pixel_locations()
        self.hue_inner = random.random() + 100
        self._center_rotation = random.random()
        self.angle = 0
        self.lum_boost = 0
        self.hue_offset = 0
        self.imagename = None
        self.image = None
        self._buffer = None

        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        if self.imagename != self.parameter('image-file').get():
            self.pixmap = QPixmap(self.parameter('image-file').get())
            self.imagename = self.parameter('image-file').get()
            image = self.pixmap.toImage()
            if image:
                #image = image.convertToFormat(QImage.Format_ARGB32)
                self.image = np.frombuffer(image.bits(), dtype=np.uint8)
                self.image = self.image.reshape(self.pixmap.height(), self.pixmap.width(), 4).T

                self.image = np.asarray((self.image[2],self.image[1],self.image[0])).T

                self.image = rgb_to_hls(self.image)
                #print self.image

                print "image", self.parameter('image-file').get(), "loaded:", self.image.shape

        self.lastFrame = None

    def reset(self):
        pass

    def draw(self, dt):
        if self.pixmap:
            lum_boost = self.parameter('beat-lum-boost').get()
            if self._mixer.is_onset():
                self.lum_boost += lum_boost

            self.hue_offset += dt * self.parameter('speed-hue').get()
            self._center_rotation += dt * self.parameter('center-orbit-speed').get()
            self.angle += dt * self.parameter('speed-rotation').get()
            orbitx = math.cos(self._center_rotation) * self.parameter('center-orbit-distance').get()
            orbity = math.sin(self._center_rotation) * self.parameter('center-orbit-distance').get()

            locations = np.copy(self.pixel_locations.T)
            cx, cy = self.scene().center_point()
            locations[0] -= cx + orbitx
            locations[1] -= cy + orbity
            rotMatrix = np.array([(math.cos(self.angle), -math.sin(self.angle)), (math.sin(self.angle),  math.cos(self.angle))])
            x,y = rotMatrix.T.dot(locations)
            x /= self.parameter('scale').get()
            y /= self.parameter('scale').get()
            x += self.pixmap.width() / 2 + self.parameter('center-x').get()
            y += self.pixmap.height() / 2 + self.parameter('center-y').get()
            x = np.int_(x)
            y = np.int_(y)

            edge_mode = self.parameter('edge-mode').get()
            if edge_mode == "clamp":
                np.clip(x, 0, self.pixmap.width() - 1, x)
                np.clip(y, 0, self.pixmap.height() - 1, y)
            elif edge_mode == "tile":
                np.mod(np.abs(x), self.pixmap.width(), x)
                np.mod(np.abs(y), self.pixmap.height(), y)
            elif edge_mode == "mirror":
                np.mod(np.abs(x), self.pixmap.width() * 2 - 1, x)
                np.mod(np.abs(y), self.pixmap.height() * 2 - 1, y)
                np.abs(x - (self.pixmap.width() - 1), x)
                np.abs(y - (self.pixmap.height() - 1), y)
            else:
                print "Unknown image preset edge mode (clamp, tile, or mirror)."

            locations = np.asarray([x,y]).T

            colors = self.image[locations.T[1], locations.T[0]]

            colors.T[0] += self.hue_offset
            colors.T[1] += self.lum_boost

            ghost = self.parameter('ghost').get()
            if abs(ghost) > 0:
                if self.lastFrame != None:
                    if self._buffer is None:
                        self._buffer = np.empty_like(self.lastFrame)
                    colors = hls_blend(colors, self.lastFrame, self._buffer, ghost, "add", 1.0, 0.1)
                self.lastFrame = colors

            lum_time = self.parameter('beat-lum-time').get()
            if lum_time and self.lum_boost:
                if self.lum_boost > 0:
                    self.lum_boost = max(0, self.lum_boost - lum_boost * dt / lum_time)
                else:
                    self.lum_boost = min(0, self.lum_boost - lum_boost * dt / lum_time)

            self._pixel_buffer = colors
