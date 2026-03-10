# Weather Station Demo — Test Tool

A multiplatform CLI for testing RS422 communication with the weather station firmware over COBS-framed nanopb packets.

---

## Architecture

```
main.py          CLI entry point, argument parsing, output formatting
client.py        High-level protocol — builds and parses typed packets
transport.py     Low-level — serial port I/O and COBS frame encode/decode
proto/           .proto source (shared with firmware)
myprotocol_pb2   Generated Python protobuf code (not committed, see Setup)
```

### How a request works

```
main.py                client.py              transport.py         firmware
   │                       │                       │                  │
   │  cmd_weather()        │                       │                  │
   │──────────────────────>│                       │                  │
   │                       │  _make_packet()       │                  │
   │                       │  serialize to bytes   │                  │
   │                       │──────────────────────>│                  │
   │                       │                       │  cobs.encode()   │
   │                       │                       │  + \x00          │
   │                       │                       │─────────────────>│
   │                       │                       │                  │  processMessage()
   │                       │                       │  cobs frame      │
   │                       │                       │<─────────────────│
   │                       │                       │  cobs.decode()   │
   │                       │  raw bytes            │                  │
   │                       │<──────────────────────│                  │
   │                       │  ParseFromString()    │                  │
   │  WeatherData          │                       │                  │
   │<──────────────────────│                       │                  │
```

### COBS framing

COBS (Consistent Overhead Byte Stuffing) eliminates `0x00` bytes from the payload so `0x00` can be used unambiguously as a frame delimiter.

```
Wire format:  [ COBS-encoded nanopb bytes ] [ 0x00 ]
```

`transport.py` reads bytes one at a time until `0x00`, then decodes the accumulated buffer with `cobs.decode()`.

### Packet structure

Every message — both requests and responses — is wrapped in a `Packet`:

```proto
message Packet {
  Header header  = 1;   // session_id, seq, message type
  bytes  payload = 2;   // serialized submessage
}
```

The `header.type` tells the firmware (or this tool) how to deserialize `payload`.

---

## Setup

```bash
pip install -r requirements.txt
./generate.sh        # generates myprotocol_pb2.py from proto/myprotocol.proto
```

`generate.sh` uses `grpcio-tools` (bundled `protoc`) to compile the `.proto` to Python. Re-run whenever `proto/myprotocol.proto` changes (keep in sync with firmware).

---

## Usage

```bash
python main.py <port> <command> [options]
```

### Commands

| Command          | Description                                          |
|------------------|------------------------------------------------------|
| `heartbeat`      | Sends a heartbeat, prints device uptime              |
| `weather`        | Requests current weather data                        |
| `conditions`     | Requests extended weather conditions (humidex, dew point, density, …) |
| `profiles`       | Lists all stored ballistic profiles                  |
| `create-profile` | Creates a new ballistic profile                      |
| `edit-profile`   | Edits an existing profile by ID                      |
| `delete-profile` | Deletes a profile by ID                              |
| `targets`        | Lists all stored targets                             |
| `create-target`  | Creates a new target                                 |
| `edit-target`    | Edits an existing target by ID                       |
| `delete-target`  | Deletes a target by ID                               |
| `listen`         | Continuously prints incoming broadcast packets       |

### Options

| Flag                | Applies to                          | Description                       |
|---------------------|-------------------------------------|-----------------------------------|
| `--baud BAUD`       | all                                 | Serial baud rate (default 115200) |
| `--id ID`           | edit-*, delete-*                    | Record ID to edit or delete       |
| `--name NAME`       | create-*, edit-*                    | Name field                        |
| `--muzzle-velocity` | create-profile, edit-profile        | Muzzle velocity (m/s)             |
| `--bc BC`           | create-profile, edit-profile        | Ballistic coefficient             |
| `--drag G1\|G7`     | create-profile, edit-profile        | Drag function                     |
| `--distance M`      | create-target, edit-target          | Distance (m)                      |
| `--bearing DEG`     | create-target, edit-target          | Bearing (°)                       |
| `--speed M/S`       | create-target, edit-target          | Speed (m/s)                       |
| `--group-id ID`     | create-target                       | Group ID (default 0 = new group)  |

### Examples

```bash
# macOS / Linux
python main.py /dev/cu.usbserial-XXX heartbeat
python main.py /dev/cu.usbserial-XXX weather
python main.py /dev/cu.usbserial-XXX conditions
python main.py /dev/cu.usbserial-XXX listen

# Profile CRUD
python main.py /dev/cu.usbserial-XXX create-profile --name "M118LR" --muzzle-velocity 853 --bc 0.243 --drag G7
python main.py /dev/cu.usbserial-XXX profiles
python main.py /dev/cu.usbserial-XXX edit-profile   --id 1 --muzzle-velocity 860
python main.py /dev/cu.usbserial-XXX delete-profile --id 1

# Target CRUD
python main.py /dev/cu.usbserial-XXX create-target --name "Alpha" --distance 800 --bearing 45 --speed 0
python main.py /dev/cu.usbserial-XXX targets
python main.py /dev/cu.usbserial-XXX edit-target   --id 2 --distance 850
python main.py /dev/cu.usbserial-XXX delete-target --id 2

# Windows
python main.py COM3 profiles --baud 115200
```

---

## File reference

### `transport.py` — `SerialCobsTransport`

| Method | Description |
|--------|-------------|
| `__init__(port, baudrate)` | Opens serial port with 0.1s read timeout |
| `send(data: bytes)` | COBS-encodes `data`, appends `\x00`, writes to serial |
| `read_packet(timeout)` | Reads bytes until `\x00`, returns COBS-decoded payload. Returns `None` on timeout or decode error |
| `close()` | Closes serial port |

`read_packet` is blocking. It loops reading single bytes until either a `\x00` frame delimiter arrives or the deadline expires.

### `client.py` — `WeatherStationClient`

| Method | Returns |
|--------|---------|
| `send_heartbeat()` | `proto.Heartbeat` or `None` |
| `get_weather_data()` | `proto.WeatherData` or `None` |
| `get_weather_conditions()` | `proto.WeatherConditions` or `None` |
| `list_profiles()` | `proto.ProfileList` or `None` |
| `create_profile(profile)` | `proto.CreateProfileAck` or `None` |
| `edit_profile(profile)` | `proto.EditProfileAck` or `None` |
| `delete_profile(profile_id)` | `proto.DeleteProfileAck` or `None` |
| `list_targets()` | `proto.TargetList` or `None` |
| `create_target(target, group_id)` | `proto.CreateTargetAck` or `None` |
| `edit_target(target)` | `proto.EditTargetAck` or `None` |
| `delete_target(target_id)` | `proto.DeleteTargetAck` or `None` |
| `listen()` | Generator yielding `proto.Packet` indefinitely |

Each request-response method:
1. Serializes the request into a `Packet` with an incrementing `seq`
2. Sends via transport
3. Waits up to 2s for a response packet
4. Deserializes the payload into the expected message type

`listen()` is an infinite generator — it yields every packet received. Stop it with `Ctrl+C`.

### `main.py`

Parses CLI arguments, constructs `SerialCobsTransport` and `WeatherStationClient`, dispatches to the relevant command function. Uses `rich` for colored tables and output. Always calls `transport.close()` in a `finally` block.

---

## Known limitations

**Broadcast/response interleaving**

The firmware broadcasts `WeatherData` every 100ms unsolicited. When a request-response command (`weather`, `profiles`, etc.) is used while broadcasting is active, `read_packet()` may return a broadcast packet instead of the response to the request — the response would then be silently dropped. In practice: use `listen` to observe broadcasts, and temporarily disable broadcasting in firmware when testing request-response commands.

**Byte-by-byte reads**

`read_packet` reads one byte at a time. This is simple and correct but inefficient for high-throughput scenarios. Acceptable for a testing tool.

**No session handling**

`session_id` is always 0. The firmware does not enforce sessions in the current implementation so this has no practical effect.
