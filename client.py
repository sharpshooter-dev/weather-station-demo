from typing import Optional, Iterator
import myprotocol_pb2 as proto
from transport import SerialCobsTransport


class WeatherStationClient:
    def __init__(self, transport: SerialCobsTransport):
        self._transport = transport
        self._seq = 0

    def _make_packet(self, msg_type: int, payload: bytes) -> bytes:
        packet = proto.Packet()
        packet.header.session_id = 0
        packet.header.seq = self._seq
        packet.header.type = msg_type
        packet.payload = payload
        self._seq += 1
        return packet.SerializeToString()

    def _parse_response(self, raw: Optional[bytes]) -> Optional[proto.Packet]:
        if not raw:
            return None
        packet = proto.Packet()
        packet.ParseFromString(raw)
        return packet

    def send_heartbeat(self) -> Optional[proto.Heartbeat]:
        req = proto.Heartbeat()
        req.uptime = 0
        self._transport.send(self._make_packet(proto.MSG_HEARTBEAT, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.Heartbeat()
        response.ParseFromString(packet.payload)
        return response

    def get_weather_data(self) -> Optional[proto.WeatherData]:
        req = proto.GetWeatherData()
        self._transport.send(self._make_packet(proto.MSG_GET_WEATHER_DATA, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.WeatherData()
        response.ParseFromString(packet.payload)
        return response

    def list_profiles(self) -> Optional[proto.ProfileList]:
        req = proto.ListProfiles()
        self._transport.send(self._make_packet(proto.MSG_LIST_PROFILES, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.ProfileList()
        response.ParseFromString(packet.payload)
        return response

    def list_targets(self) -> Optional[proto.TargetList]:
        req = proto.ListTargets()
        self._transport.send(self._make_packet(proto.MSG_LIST_TARGETS, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.TargetList()
        response.ParseFromString(packet.payload)
        return response

    def listen(self, timeout_per_packet: float = 0.5) -> Iterator[proto.Packet]:
        while True:
            raw = self._transport.read_packet(timeout=timeout_per_packet)
            if raw:
                packet = self._parse_response(raw)
                if packet:
                    yield packet
