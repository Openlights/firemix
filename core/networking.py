from __future__ import print_function
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
from lib.buffer_utils import BufferUtils, struct_flat

USE_OPC = True


class Networking:

    def __init__(self, app):
        self.socket = None
        self.context = None
        self._app = app
        self.running = True
        self.open_socket()
        # Maps client type to list of packet buffers
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
            buffer_rgb = hls_to_rgb(buffer)
            buffer_rgb_int = np.int8(struct_flat(buffer_rgb) * 255)

            self._write_legacy(buffer_rgb_int, strand_settings, undimmed_legacy_clients)

        # Now that we've written to clients that don't want dimmed data, apply
        # the global dimmer from the mixer and re-convert to RGB
        if self._app.mixer.global_dimmer < 1.0:
            buffer['light'] *= self._app.mixer.global_dimmer
        buffer_rgb = hls_to_rgb(buffer)
        buffer_rgb_int = np.int8(struct_flat(buffer_rgb) * 255)

        if dimmed_legacy_clients:
            self._write_legacy(buffer_rgb_int, strand_settings, dimmed_legacy_clients)

        if opc_clients:
            self._write_opc(buffer_rgb_int, strand_settings, opc_clients)

    def _write_legacy(self, buf, strand_settings, clients):
        packets = []

        if 'legacy' not in self._packet_cache:
            self._packet_cache['legacy'] = [None] * len(strand_settings)

        for strand in range(len(strand_settings)):
            if not strand_settings[strand]["enabled"]:
                continue

            start, end = BufferUtils.get_strand_extents(strand)
            start *= 3
            end *= 3

            packet_header_size = 4
            packet_size = (end-start) + packet_header_size

            packet = self._packet_cache['legacy'][strand]
            if packet is None:
                packet = np.zeros(packet_size, dtype=np.int8)
                self._packet_cache['legacy'][strand] = packet

            length = packet_size - packet_header_size

            packet[0] = ord('S')
            packet[1] = strand
            packet[2] = length & 0x00FF
            packet[3] = (length & 0xFF00) >> 8

            np.copyto(packet[packet_header_size:], buf[start:end])
            packets.append(packet)

        for client in clients:
            try:
                self.socket.sendto(array.array('B', [ord('B')]), (client["host"], client["port"]))
                for packet in packets:
                    self.socket.sendto(packet, (client["host"], client["port"]))
                self.socket.sendto(array.array('B', [ord('E')]), (client["host"], client["port"]))
            except socket.gaierror:
                print("Bad hostname: ", client["host"])
                continue
            except:
                continue


    def _write_opc(self, buf, strand_settings, clients):
        packet_data_len = len(buf)
        packet_size = packet_data_len + 4

        if 'opc' not in self._packet_cache:
            self._packet_cache['opc'] = [np.empty(packet_size, dtype=np.int8)]

        packet = self._packet_cache['opc'][0]

        # OPC happens to look a lot like our existing protocol.
        # Byte 0 is channel (aka strand).  0 is broadcast address, indexing starts at 1.
        # Byte 1 is command, always 0 for "set pixel colors"
        # Bytes 2 and 3 are big-endian length of the data block.
        #
        # Both LEDScape and the OPC reference implementation actually seem to
        # ignore the strand address and just assume that the data for all
        # strands is sent in a single broadcast packet. So, we do that here.

        packet[0] = 0
        packet[1] = 0
        packet[2] = (packet_data_len & 0xFF00) >> 8
        packet[3] = (packet_data_len & 0xFF)
        np.copyto(packet[4:], buf)

        for client in clients:
            self.socket.sendto(packet, (client["host"], client["port"]))
