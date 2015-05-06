# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

from lib.buffer_utils import BufferUtils
from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, HLSParameter, StringParameter

class CombinePresets(RawPreset):
    """
    Preset that loads two presets and renders both
    Combine requires a transition that will render an arbitrary progress point
    """

    def setup(self):
        self.add_parameter(StringParameter('first-preset', ""))
        self.add_parameter(StringParameter('second-preset', ""))
        self.add_parameter(FloatParameter('transition-progress', 0.5))
        self.add_parameter(StringParameter('transition-mode', "Additive Blend"))
        self.parameter_changed(None)
        self._preset1_buffer = BufferUtils.create_buffer()
        self._preset2_buffer = BufferUtils.create_buffer()

    def parameter_changed(self, parameter):
        self._transition = self._mixer.get_transition_by_name(self.parameter('transition-mode').get())
        if self._transition:
            self._transition.reset()

    def reset(self):
        self.parameter_changed(None)

    def draw(self, dt):

        preset1 = self._mixer._playlist.get_preset_by_name(self.parameter('first-preset').get())
        preset2 = self._mixer._playlist.get_preset_by_name(self.parameter('second-preset').get())

        if preset1 and preset2 and self._transition:
            # this is here because many transitions are set up to only play from start to end :(
            # Combine renders arbitrary transition frames
            self._transition.reset()

            preset1.tick(dt)
            preset2.tick(dt)

            preset1_buffer = preset1.draw_to_buffer(self._preset1_buffer)
            preset2_buffer = preset2.draw_to_buffer(self._preset2_buffer)

            self._pixel_buffer = self._transition.get(
                preset1_buffer, preset2_buffer,
                self.parameter('transition-progress').get())
