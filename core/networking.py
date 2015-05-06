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


import sys
import numpy as np
import socket
import array
import struct
import time

from profilehooks import profile

from lib.colors import hls_to_rgb
from lib.buffer_utils import BufferUtils

COMMAND_SET_BGR = 0x10
COMMAND_SET_RGB = 0x20

class Networking:

    def __init__(self, app):
        self._socket = None
        self._app = app
        self.open_socket()
        self._packet_cache = {}

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @profile
    def write_buffer(self, buffer):
        """
        Performs a bulk strand write.
        Decodes the HLS-Float data according to client settings
        """
        strand_settings = self._app.scene.get_strand_settings()

        # Protect against presets or transitions that write float data.
        buffer_rgb = np.int_(hls_to_rgb(buffer) * 255)

        for client in [client for client in self._app.settings['networking']['clients'] if client["enabled"]]:
            # TODO: Split into smaller packets so that less-than-ideal networks will be OK
            #packet = array.array('B', [])
            client_color_mode = client["color-mode"]

            for strand in range(len(strand_settings)):
                packet = array.array('B', [])
                if not strand_settings[strand]["enabled"]:
                    continue
                color_mode = strand_settings[strand]["color-mode"]

                start, end = BufferUtils.get_strand_extents(strand)
                #print strand, start, end

                #if client_color_mode == "RGB8":
                 #   data = array.array('B', alldata[start*3:end*3])

        def fill_packet(intbuffer, start, end, offset, packet, swap_order=False):
            for pixel_index, pixel in enumerate(intbuffer[start:end]):
                buffer_index = offset + pixel_index * 3
                if swap_order:
                    packet[buffer_index] = pixel[2]
                    packet[buffer_index + 1] = pixel[1]
                    packet[buffer_index + 2] = pixel[0]
                else:
                    packet[buffer_index] = pixel[0]
                    packet[buffer_index + 1] = pixel[1]
                    packet[buffer_index + 2] = pixel[2]

        clients = [client for client in self._app.settings['networking']['clients']
                   if client["enabled"]]

        if not clients:
            return

        for strand in xrange(len(strand_settings)):
            if not strand_settings[strand]["enabled"]:
                continue
            packet = array.array('B', [])

            color_mode = strand_settings[strand]["color-mode"]
            start, end = BufferUtils.get_strand_extents(strand)

            packet_header_size = 4
            packet_size = (end-start) * 3 + packet_header_size

            packet = self._packet_cache.get(packet_size, None)
            if packet is None:
                packet = [0,] * packet_size
                self._packet_cache[packet_size] = packet

            command = COMMAND_SET_RGB if color_mode == "RGB8" else COMMAND_SET_BGR
            packet[0] = strand
            packet[1] = command
            length = packet_size - packet_header_size
            packet[2] = length & 0x00FF
            packet[3] = (length & 0xFF00) >> 8

            rgb8_packet = None
            bgr8_packet = None

            for client in clients:
                # TODO: Split into smaller packets so that less-than-ideal networks will be OK
                client_color_mode = client["color-mode"]
                if client_color_mode == 'RGB8':
                    if rgb8_packet is None:
                        fill_packet(buffer_rgb, start, end, packet_header_size, packet, False)
                        rgb8_packet = array.array('B', packet)
                    packet = rgb8_packet
                elif client_color_mode == 'BGR8':
                    if bgr8_packet is None:
                        fill_packet(buffer_rgb, start, end, packet_header_size, packet, True)
                        bgr8_packet = array.array('B', packet)
                    packet = rgb8_packet
                else:
                    raise NotImplementedError('Unknown color mode: %s' % client_color_mode)

                try:
                    #print "Sending packet of length %i for strand %i", (len(packet), strand)
                    self._socket.sendto(packet, (client["host"], client["port"]))
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    #print "On strand %i with length %i" % (strand, len(packet))
                except ValueError:
                    print "Could not convert data to an integer."
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
