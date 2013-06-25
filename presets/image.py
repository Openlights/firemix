import colorsys
import random
import math
import numpy as np
from PySide.QtGui import QPixmap

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, IntParameter, StringParameter

class ImagePreset(RawPreset):
    _fader = None
    
    def setup(self):
        self.add_parameter(FloatParameter('speed-rotation', 0.1))
        self.add_parameter(FloatParameter('speed-hue', 0.0))
        self.add_parameter(FloatParameter('center-orbit-distance', 0.0))
        self.add_parameter(FloatParameter('center-orbit-speed', 0.1))
        self.add_parameter(StringParameter('image-file', "data/images/sunflower.png"))
        self.add_parameter(FloatParameter('center-x', 0))
        self.add_parameter(FloatParameter('center-y', 0))
        self.add_parameter(FloatParameter('scale', 1.0))
        self.add_parameter(FloatParameter('ghost', 0.0))
        self.add_parameter(FloatParameter('beat-lum-boost', 0.5))
        self.add_parameter(FloatParameter('beat-lum-time', 0.2))

        self.hue_inner = random.random() + 100
        self._center_rotation = random.random()
        self.angle = 0
        self.lum_boost = 0
        self.hue_offset = 0

        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        self.pixmap = QPixmap(self.parameter('image-file').get())
        self.pixel_locations = np.asarray(self.scene().get_all_pixel_locations())
        self.lastFrame = None

    def reset(self):
        pass

    def draw(self, dt):
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
        np.clip(x, 0, self.pixmap.width() - 1, x)
        np.clip(y, 0, self.pixmap.height() - 1, y)
        locations = np.asarray([x,y]).T

        # this can be much faster:
        colors = np.asarray([self.pixmap.toImage().pixel(*location) for location in locations])
        r = np.float_((colors / 0x00010000) % 0x100) / 0x100
        g = np.float_((colors / 0x00000100) % 0x100) / 0x100
        b = np.float_(colors % 0x100) / 0x100
        colors = np.asarray([r,g,b]).T
        ghost = self.parameter('ghost').get()
        if ghost != 0.0:
            if self.lastFrame != None:
                colors = (colors * (1.0 - ghost) + self.lastFrame * (ghost))
            self.lastFrame = colors
        colors = np.asarray([colorsys.rgb_to_hls(*color) for color in colors])
        colors.T[0] += self.hue_offset
        colors.T[1] += self.lum_boost

        self.lum_boost = max(0, self.lum_boost - lum_boost * dt / self.parameter('beat-lum-time').get())

        self._pixel_buffer = colors
