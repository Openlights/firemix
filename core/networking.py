import socket
import array
import struct


class Networking:

    def __init__(self, ip="127.0.0.1", port=3020):
        self._socket = None
        self._ip = ip
        self._port = port
        self.open_socket()

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, data):
        data = [item for sublist in data for item in sublist]
        self._socket.sendto(array.array('B', data), (self._ip, self._port))

    def write_strand(self, strand_data):
        """
        Performs a bulk strand write.
        The expected input format is a dictionary of strand addresses and strand data.
        The input strand data is a flat list of pixel values for all fixtures in the strand.
        Example: {0: [255, 127, 50, 255, 100, 70, ...]}
        """

        # TODO: Split into smaller packets so that less-than-ideal networks will be OK

        for strand in strand_data.keys():
            #print "strand %d len %d" % (strand, len(strand_data[strand]))
            #print strand_data[strand]
            length = len(strand_data[strand]) + 1
            packet = array.array('B', [0x27, (length & 0xFF00) >> 8, (length & 0xFF), strand] + strand_data[strand])
            self._socket.sendto(packet, (self._ip, self._port))


