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


import sys
import numpy as np
import socket
import array
import struct
from copy import deepcopy
import time

from collections import defaultdict

from lib.colors import hls_to_rgb
from lib.buffer_utils import BufferUtils

USE_OPC = True


def _fill_packet(intbuffer, start, end, offset, packet, swap_order=False):
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


class Networking:

    def __init__(self, app):
        self.socket = None
        self.context = None
        self._app = app
        self.running = True
        self.open_socket()
        self._packet_cache = {}
        self.port = 3020
        self.opc_port = 7890

    def open_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def write_buffer(self, buffer):
        """
        Performs a bulk strand write.
        Decodes the HLS-Float data according to client settings
        """
        strand_settings = self._app.scene.get_strand_settings()
        clients = [client for client in self._app.settings['networking']['clients'] if client["enabled"]]

        clients_by_type = defaultdict(list)
        have_non_dimmed = False
        for c in clients:
            clients_by_type[c.get("protocol", "Legacy")].append(c)

        dimmed_legacy_clients = [c for c in clients_by_type["Legacy"] if not c.get('ignore-dimming')]
        undimmed_legacy_clients = [c for c in clients_by_type["Legacy"] if c.get('ignore-dimming')]
        opc_clients = clients_by_type["OPC"]

        if undimmed_legacy_clients:
            # Protect against presets or transitions that write float data.
            buffer_rgb = np.int_(hls_to_rgb(buffer) * 255)
            np.clip(buffer_rgb, 0, 255, buffer_rgb)

            self._write_legacy(buffer_rgb, strand_settings, undimmed_legacy_clients)

        # Now that we've written to clients that don't want dimmed data, apply
        # the global dimmer from the mixer and re-convert to RGB
        if self._app.mixer.global_dimmer < 1.0:
            buffer.T[1] *= self._app.mixer.global_dimmer
        buffer_rgb = np.int_(hls_to_rgb(buffer) * 255)
        np.clip(buffer_rgb, 0, 255, buffer_rgb)

        if dimmed_legacy_clients:
            self._write_legacy(buffer_rgb, strand_settings, dimmed_legacy_clients)

        if opc_clients:
            self._write_opc(buffer_rgb, strand_settings, opc_clients)

    def _write_legacy(self, buf, strand_settings, clients):
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

            length = packet_size - packet_header_size

            packet[0] = ord('S')
            packet[1] = strand
            packet[2] = length & 0x00FF
            packet[3] = (length & 0xFF00) >> 8

            _fill_packet(buf, start, end, packet_header_size, packet, False)
            packets.append(array.array('B', packet))

        for client in clients:
            self.socket.sendto(array.array('B', [ord('B')]), (client["host"], client["port"]))
            for packet in packets:
                self.socket.sendto(packet, (client["host"], client["port"]))
            self.socket.sendto(array.array('B', [ord('E')]), (client["host"], client["port"]))

    def _write_opc(self, buf, strand_settings, clients):
        # XXX: FIXME: BROKEN
        for client in clients:
            # TODO: This is hacky, but for now we re-write the packet for OPC here...
            # Fortunately, OPC happens to look a lot like our existing protocol...
            # Byte 0 is channel (aka strand).  0 is broadcast address, indexing starts at 1.
            # Byte 1 is command, always 0 for "set pixel colors"
            # Bytes 2 and 3 are big-endian length of the data block.
            # Note: LEDScape needs the strands all concatenated together which is annoying
            packet[0] = packet[1] + 1
            tpacket = [0x00, 0x00, 0x00, 0x00]
            for packet in packets:
                tpacket += packet[4:]
            tlen = len(tpacket) - 4
            tpacket[2] = (tlen & 0xFF00) >> 8
            tpacket[3] = (tlen & 0xFF)
            tpacket = array.array('B', tpacket)
            self.socket.sendto(tpacket, (client["host"], client["port"]))
