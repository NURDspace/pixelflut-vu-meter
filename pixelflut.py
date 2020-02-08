import socket
import struct

from PIL import Image

class PixelClient():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    buffer = []

    def __init__(self, host: str, port=5004):
        self.host = host
        self.port = port
        self.verModeString = self.SetVersionBit(1) + self.SetRGBAMode(0)

    def _send(self, data: bytes):
        """ Send data to the server"""
        self.sock.sendto(data, (self.host, self.port))

    def flush(self):
        """ Send everything that is inside the buffer to the server"""
        self._send(self.verModeString + b"".join(self.buffer))
        self.buffer = []

    def RGBPixel(self, x: int, y: int, r: int, g: int, b: int, a=None):
        """Generates the packed data for a pixel"""
        if a:
            self.buffer.append(bytes(struct.pack("<2H4B", x, y, r, g, b, a)))
        self.buffer.append(bytes(struct.pack("<2H3B", x, y, r, g, b)))

    @staticmethod
    def SetRGBAMode(mode: int) -> bytes:
        """
            Generate the rgb/rgba bit
            0 for RGB and 1 for RGBA
        """
        return struct.pack("<?", mode)

    @staticmethod
    def SetVersionBit(protocol=1) -> bytes:
        """Generate the Version bit"""
        return struct.pack("<B", protocol)

