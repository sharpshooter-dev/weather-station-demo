import time
import serial
from cobs import cobs
from typing import Optional


class SerialCobsTransport:
    def __init__(self, port: str, baudrate: int = 115200):
        self._serial = serial.Serial(port, baudrate, timeout=0.1)

    def send(self, data: bytes):
        frame = cobs.encode(data) + b'\x00'
        self._serial.write(frame)

    def read_packet(self, timeout: float = 2.0) -> Optional[bytes]:
        deadline = time.time() + timeout
        buf = bytearray()

        while time.time() < deadline:
            byte = self._serial.read(1)
            if not byte:
                continue
            if byte == b'\x00':
                if buf:
                    try:
                        return bytes(cobs.decode(bytes(buf)))
                    except Exception:
                        buf.clear()
                        continue
                buf.clear()
            else:
                buf.extend(byte)

        return None

    def close(self):
        self._serial.close()
