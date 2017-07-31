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

from lib.buffer_utils import BufferUtils
from lib.pattern import Pattern
from lib.parameters import FloatParameter, HLSParameter, StringParameter

class CombinePresets(Pattern):
    """
    Pattern that loads two presets and renders both
    Combine requires a transition that will render an arbitrary progress point
    """

    def setup(self):
        self.add_parameter(StringParameter('first-preset', ""))
        self.add_parameter(StringParameter('second-preset', ""))
        self.add_parameter(FloatParameter('transition-progress', 0.5))
        self.add_parameter(FloatParameter('audio-transition', 0.0))
        self.add_parameter(StringParameter('transition-mode', "Additive Blend"))

    def parameter_changed(self, parameter):
        self._preset1_name = self.parameter('first-preset').get()
        self._preset2_name = self.parameter('second-preset').get()

        self._transition = self._app.mixer.get_transition_by_name(self.parameter('transition-mode').get())
        if self._transition:
            self._transition.reset()

    def reset(self):
        self.parameter_changed(None)
        self._buffer1 = BufferUtils.create_buffer()
        self._buffer2 = BufferUtils.create_buffer()

    def tick(self, dt):
        super(CombinePresets, self).tick(dt)

        # We do this fetching here because at the time the first
        # `parameter_changed` call is made, the Playlist has not yet been
        # completely created and is not yet assigned to mixer.playlist
        self.preset1 = self._app.mixer.playlist.get_preset_by_name(self._preset1_name)
        self.preset2 = self._app.mixer.playlist.get_preset_by_name(self._preset2_name)

        self.preset1.tick(dt)
        self.preset2.tick(dt)

    def render(self, out):
        preset1 = self.preset1
        preset2 = self.preset2

        if preset1 and preset2 and self._transition:
            # this is here because many transitions are set up to only play from start to end :(
            # Combine renders arbitrary transition frames
            self._transition.reset()

            preset1.render(self._buffer1)
            preset2.render(self._buffer2)

            transition_amount = self.parameter('transition-progress').get()

            if self.parameter('audio-transition').get() > 0:
                transition_amount += self.parameter('audio-transition').get() * self._app.mixer.audio.getEnergy()

            self._transition.render(self._buffer1, self._buffer2,
                                    transition_amount, out)
