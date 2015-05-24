# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
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


import sys
import numpy as np
import socket
import array
import struct
import time

from profilehooks import profile

from lib.colors import hls_to_rgb
from lib.buffer_utils import BufferUtils

COMMAND_START_FRAME = 0x01
COMMAND_END_FRAME = 0x02
COMMAND_SET_BGR = 0x10
COMMAND_SET_RGB = 0x20

START_FRAME_PACKET = array.array('B', [COMMAND_START_FRAME, 0, 0, 0, 0])
END_FRAME_PACKET = array.array('B', [COMMAND_END_FRAME, 0, 0, 0, 0])


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
        active_clients = [client for client in self._app.settings['networking']['clients'] if client["enabled"]]

        # Protect against presets or transitions that write float data.
        buffer_rgb = np.int_(hls_to_rgb(buffer) * 255)

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

        packets = []

        for strand in xrange(len(strand_settings)):
            if not strand_settings[strand]["enabled"]:
                continue

            start, end = BufferUtils.get_strand_extents(strand)

            packet_header_size = 4
            packet_size = (end-start) * 3 + packet_header_size

            try:
                packet = self._packet_cache[packet_size]
            except KeyError:
                packet = [0,] * packet_size
                self._packet_cache[packet_size] = packet

            packet[0] = COMMAND_SET_RGB
            packet[1] = strand
            length = packet_size - packet_header_size
            packet[2] = length & 0x00FF
            packet[3] = (length & 0xFF00) >> 8

            fill_packet(buffer_rgb, start, end, packet_header_size, packet, False)
            packets.append(array.array('B', packet))

        def safe_send(packet, client):
            try:
                self._socket.sendto(packet, (client["host"], client["port"]))
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
            except ValueError:
                print "Could not convert data to an integer."
            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise

        for client in active_clients:
            safe_send(START_FRAME_PACKET, client)
            for i in xrange(0, len(packets), 2):
                chunk = packets[i:i+2]
                apacket = array.array('B', [item for sublist in chunk for item in sublist])
                safe_send(apacket, client)
            safe_send(END_FRAME_PACKET, client)
