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

    def get_weather_conditions(self) -> Optional[proto.WeatherConditions]:
        req = proto.GetWeatherConditions()
        self._transport.send(self._make_packet(proto.MSG_GET_WEATHER_CONDITIONS, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.WeatherConditions()
        response.ParseFromString(packet.payload)
        return response

    # ── Profiles ──────────────────────────────────────────────────────────────

    def list_profiles(self) -> Optional[proto.ProfileList]:
        req = proto.ListProfiles()
        self._transport.send(self._make_packet(proto.MSG_LIST_PROFILES, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.ProfileList()
        response.ParseFromString(packet.payload)
        return response

    def create_profile(self, profile: proto.Profile) -> Optional[proto.CreateProfileAck]:
        req = proto.CreateProfile()
        req.profile.CopyFrom(profile)
        self._transport.send(self._make_packet(proto.MSG_CREATE_PROFILE, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.CreateProfileAck()
        response.ParseFromString(packet.payload)
        return response

    def edit_profile(self, profile: proto.Profile) -> Optional[proto.EditProfileAck]:
        req = proto.EditProfile()
        req.profile.CopyFrom(profile)
        self._transport.send(self._make_packet(proto.MSG_EDIT_PROFILE, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.EditProfileAck()
        response.ParseFromString(packet.payload)
        return response

    def delete_profile(self, profile_id: int) -> Optional[proto.DeleteProfileAck]:
        req = proto.DeleteProfile()
        req.profile_id = profile_id
        self._transport.send(self._make_packet(proto.MSG_DELETE_PROFILE, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.DeleteProfileAck()
        response.ParseFromString(packet.payload)
        return response

    # ── Targets ───────────────────────────────────────────────────────────────

    def list_targets(self) -> Optional[proto.TargetList]:
        req = proto.ListTargets()
        self._transport.send(self._make_packet(proto.MSG_LIST_TARGETS, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.TargetList()
        response.ParseFromString(packet.payload)
        return response

    def create_target(self, target: proto.Target, group_id: int = 0) -> Optional[proto.CreateTargetAck]:
        req = proto.CreateTarget()
        req.group_id = group_id
        req.target.CopyFrom(target)
        self._transport.send(self._make_packet(proto.MSG_CREATE_TARGET, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.CreateTargetAck()
        response.ParseFromString(packet.payload)
        return response

    def edit_target(self, target: proto.Target) -> Optional[proto.EditTargetAck]:
        req = proto.EditTarget()
        req.target.CopyFrom(target)
        self._transport.send(self._make_packet(proto.MSG_EDIT_TARGET, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.EditTargetAck()
        response.ParseFromString(packet.payload)
        return response

    def delete_target(self, target_id: int) -> Optional[proto.DeleteTargetAck]:
        req = proto.DeleteTarget()
        req.target_id = target_id
        self._transport.send(self._make_packet(proto.MSG_DELETE_TARGET, req.SerializeToString()))

        packet = self._parse_response(self._transport.read_packet())
        if not packet:
            return None
        response = proto.DeleteTargetAck()
        response.ParseFromString(packet.payload)
        return response

    def listen(self, timeout_per_packet: float = 0.5) -> Iterator[proto.Packet]:
        while True:
            raw = self._transport.read_packet(timeout=timeout_per_packet)
            if raw:
                packet = self._parse_response(raw)
                if packet:
                    yield packet
