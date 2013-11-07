import sys
import numpy as np
import socket
import array
import struct
import colorsys
import time

from profilehooks import profile

from lib.colors import clip
from lib.buffer_utils import BufferUtils


COMMAND_SET_BGR = 0x10
COMMAND_SET_RGB = 0x20

cache = {}
cache_steps = 256

def getRGB(h,l,s):
    """
    Hacking some color conversion here for Firefly
    This wraps colorsys's conversion with some type conversion and caching
    It's not nice enough to keep.
    """
    color = cache.get((h,l,s), None)

    if color == None:
        color = colorsys.hls_to_rgb(float(h) / cache_steps, float(l) / cache_steps, float(s) / cache_steps)
        color = (clip(0, int(color[0]*255), 255), clip(0, int(color[1]*255), 255), clip(0, int(color[2]*255), 255))
        cache[(h,l,s)] = color
        #print "cache miss", h,l,s,color

    return color


class Networking:

    def __init__(self, app):
        self._socket = None
        self._app = app
        self.open_socket()

#        for h in range(cache_steps + 1):
#            for l in range(cache_steps + 1):
#                for s in range(cache_steps + 1):
#                    getRGB(h,l,s)

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @profile
    def write(self, buffer):
        """
        Performs a bulk strand write.
        Decodes the HLS-Float data according to client settings
        """
        strand_settings = self._app.scene.get_strand_settings()

        # Hack: assume that at least one client will be RGB mode
        intbuffer = np.int_(buffer * cache_steps)
        alldata = [getRGB(*pixel) for pixel in intbuffer]
        alldata = [item for sublist in alldata for item in sublist]

        for client in (client for client in self._app.settings['networking']['clients'] if client["enabled"]):
            # TODO: Split into smaller packets so that less-than-ideal networks will be OK
            client_color_mode = client["color-mode"]
            client_host_port = (client["host"], client["port"])

            for strand in xrange(len(strand_settings)):
                if not strand_settings[strand]["enabled"]:
                    continue
                packet = array.array('B', [])

                color_mode = strand_settings[strand]["color-mode"]
                start, end = BufferUtils.get_strand_extents(strand)

                if client_color_mode == "RGB8":
                    data = array.array('B', alldata[start*3:end*3])
                else:
                    data = [channel for pixel in buffer[start:end] for channel in pixel]
                    data = array.array('B', struct.pack('%sf' % len(data), *data))

                length = len(data)
                command = COMMAND_SET_RGB if color_mode == "RGB8" else COMMAND_SET_BGR
                packet.extend(array.array('B', [strand, command, (length & 0xFF), (length & 0xFF00) >> 8]))
                packet.extend(data)

# Is the strand packing above slow? I wonder...
# Does it mean anything if this is faster?
#            length = len(alldata)
#            packet.extend(array.array('B', [0, 0, (length & 0xFF), (length & 0xFF00) >> 8]))
#            packet.extend(array.array('B', alldata))
                try:
                    self._socket.sendto(packet, client_host_port)
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    #print "On strand %i with length %i" % (strand, len(packet))
                except ValueError:
                    print "Could not convert data to an integer."
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
