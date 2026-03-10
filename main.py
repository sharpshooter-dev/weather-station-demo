import argparse
import sys
import myprotocol_pb2 as proto
from rich.console import Console
from rich.table import Table
from transport import SerialCobsTransport
from client import WeatherStationClient

console = Console()


def cmd_heartbeat(client: WeatherStationClient, args: argparse.Namespace):
    console.print("[cyan]Sending heartbeat...[/cyan]")
    response = client.send_heartbeat()
    if response:
        console.print(f"[green]OK — device uptime: {response.uptime} ms[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_weather(client: WeatherStationClient, args: argparse.Namespace):
    console.print("[cyan]Requesting weather data...[/cyan]")
    weather = client.get_weather_data()
    if not weather:
        console.print("[red]No response[/red]")
        return

    table = Table(title="Weather Data")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("Temperature",    f"{weather.temperature:.1f} °C")
    table.add_row("Pressure",       f"{weather.pressure:.1f} hPa")
    table.add_row("Humidity",       f"{weather.humidity:.1f} %")
    table.add_row("Wind Speed",     f"{weather.wind_speed:.1f} m/s")
    table.add_row("Wind Direction", f"{weather.wind_direction:.0f} °")
    table.add_row("Timestamp",      f"{weather.timestamp} ms")
    console.print(table)


def cmd_conditions(client: WeatherStationClient, args: argparse.Namespace):
    console.print("[cyan]Requesting weather conditions...[/cyan]")
    conditions = client.get_weather_conditions()
    if not conditions:
        console.print("[red]No response[/red]")
        return

    table = Table(title="Weather Conditions")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("Temperature", f"{conditions.temperature:.1f} °C")
    table.add_row("Humidity",    f"{conditions.humidity:.1f} %")
    table.add_row("Humidex",     f"{conditions.humidex:.1f}")
    table.add_row("Dew Point",   f"{conditions.dew_point:.1f} °C")
    table.add_row("Wind Speed",  f"{conditions.wind_speed:.1f} m/s")
    table.add_row("Pressure",    f"{conditions.pressure:.1f} hPa")
    table.add_row("Density",     f"{conditions.density:.4f} kg/m³")
    console.print(table)


# ── Profiles ──────────────────────────────────────────────────────────────────

def cmd_profiles(client: WeatherStationClient, args: argparse.Namespace):
    console.print("[cyan]Requesting profile list...[/cyan]")
    result = client.list_profiles()
    if not result:
        console.print("[red]No response[/red]")
        return

    if not result.profiles:
        console.print("[yellow]No profiles stored[/yellow]")
        return

    table = Table(title="Profiles")
    table.add_column("ID",             style="cyan")
    table.add_column("Name")
    table.add_column("Muzzle Velocity")
    table.add_column("BC")
    table.add_column("Drag")
    for p in result.profiles:
        drag = "G7" if p.drag_function == proto.Profile.G7 else "G1"
        table.add_row(str(p.id), p.name, f"{p.muzzle_velocity:.0f} m/s", f"{p.ballistic_coef:.3f}", drag)
    console.print(table)


def cmd_create_profile(client: WeatherStationClient, args: argparse.Namespace):
    profile = proto.Profile()
    profile.name            = args.name
    profile.muzzle_velocity = args.muzzle_velocity
    profile.ballistic_coef  = args.bc
    profile.drag_function   = proto.Profile.G7 if args.drag == "G7" else proto.Profile.G1

    console.print(f"[cyan]Creating profile '{profile.name}'...[/cyan]")
    ack = client.create_profile(profile)
    if ack:
        console.print(f"[green]Created — profile_id={ack.profile_id}[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_edit_profile(client: WeatherStationClient, args: argparse.Namespace):
    profile = proto.Profile()
    profile.id = args.id
    if args.name is not None:
        profile.name = args.name
    if args.muzzle_velocity is not None:
        profile.muzzle_velocity = args.muzzle_velocity
    if args.bc is not None:
        profile.ballistic_coef = args.bc
    if args.drag is not None:
        profile.drag_function = proto.Profile.G7 if args.drag == "G7" else proto.Profile.G1

    console.print(f"[cyan]Editing profile id={args.id}...[/cyan]")
    ack = client.edit_profile(profile)
    if ack:
        console.print(f"[green]Updated — profile_id={ack.profile_id}[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_delete_profile(client: WeatherStationClient, args: argparse.Namespace):
    console.print(f"[cyan]Deleting profile id={args.id}...[/cyan]")
    ack = client.delete_profile(args.id)
    if ack:
        console.print(f"[green]Deleted — profile_id={ack.profile_id}[/green]")
    else:
        console.print("[red]No response[/red]")


# ── Targets ───────────────────────────────────────────────────────────────────

def cmd_targets(client: WeatherStationClient, args: argparse.Namespace):
    console.print("[cyan]Requesting target list...[/cyan]")
    result = client.list_targets()
    if not result:
        console.print("[red]No response[/red]")
        return

    if not result.targets:
        console.print("[yellow]No targets stored[/yellow]")
        return

    table = Table(title="Targets")
    table.add_column("ID",       style="cyan")
    table.add_column("Name")
    table.add_column("Distance")
    table.add_column("Bearing")
    table.add_column("Speed")
    for t in result.targets:
        table.add_row(str(t.id), t.name, f"{t.distance:.0f} m", f"{t.bearing:.1f} °", f"{t.speed:.1f} m/s")
    console.print(table)


def cmd_create_target(client: WeatherStationClient, args: argparse.Namespace):
    target = proto.Target()
    target.name     = args.name
    target.distance = args.distance
    target.bearing  = args.bearing
    target.speed    = args.speed

    console.print(f"[cyan]Creating target '{target.name}'...[/cyan]")
    ack = client.create_target(target, group_id=args.group_id)
    if ack:
        console.print(f"[green]Created — target_id={ack.target_id} group_id={ack.group_id}[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_edit_target(client: WeatherStationClient, args: argparse.Namespace):
    target = proto.Target()
    target.id = args.id
    if args.name is not None:
        target.name = args.name
    if args.distance is not None:
        target.distance = args.distance
    if args.bearing is not None:
        target.bearing = args.bearing
    if args.speed is not None:
        target.speed = args.speed

    console.print(f"[cyan]Editing target id={args.id}...[/cyan]")
    ack = client.edit_target(target)
    if ack:
        console.print(f"[green]Updated — target_id={ack.target_id}[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_delete_target(client: WeatherStationClient, args: argparse.Namespace):
    console.print(f"[cyan]Deleting target id={args.id}...[/cyan]")
    ack = client.delete_target(args.id)
    if ack:
        console.print(f"[green]Deleted — target_id={ack.target_id}[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_listen(client: WeatherStationClient, args: argparse.Namespace):
    console.print("[cyan]Listening for broadcasts — Ctrl+C to stop...[/cyan]")
    try:
        for packet in client.listen():
            if packet.header.type == proto.MSG_WEATHER_DATA:
                weather = proto.WeatherData()
                weather.ParseFromString(packet.payload)
                console.print(
                    f"[green]seq={packet.header.seq:4d}[/green] "
                    f"temp={weather.temperature:.1f}°C  "
                    f"wind={weather.wind_speed:.1f}m/s @ {weather.wind_direction:.0f}°  "
                    f"pressure={weather.pressure:.1f}hPa"
                )
            else:
                console.print(f"[yellow]type={packet.header.type} seq={packet.header.seq}[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped[/yellow]")


COMMANDS = {
    "heartbeat":      cmd_heartbeat,
    "weather":        cmd_weather,
    "conditions":     cmd_conditions,
    # profiles
    "profiles":       cmd_profiles,
    "create-profile": cmd_create_profile,
    "edit-profile":   cmd_edit_profile,
    "delete-profile": cmd_delete_profile,
    # targets
    "targets":        cmd_targets,
    "create-target":  cmd_create_target,
    "edit-target":    cmd_edit_target,
    "delete-target":  cmd_delete_target,
    "listen":         cmd_listen,
}


def main():
    parser = argparse.ArgumentParser(description="Weather Station RS422 Test Tool")
    parser.add_argument("port", help="Serial port e.g. /dev/cu.usbserial-XXX or COM3")
    parser.add_argument("cmd",  choices=COMMANDS.keys())
    parser.add_argument("--baud", default=115200, type=int)

    # shared CRUD args
    parser.add_argument("--id",   type=int,   help="Record ID (edit/delete)")
    parser.add_argument("--name", type=str,   help="Name")

    # profile-specific
    parser.add_argument("--muzzle-velocity", dest="muzzle_velocity", type=float, default=None, help="Muzzle velocity (m/s)")
    parser.add_argument("--bc",              type=float, default=None, help="Ballistic coefficient")
    parser.add_argument("--drag",            choices=["G1", "G7"], default=None, help="Drag function")

    # target-specific
    parser.add_argument("--distance",  type=float, default=None, help="Distance (m)")
    parser.add_argument("--bearing",   type=float, default=None, help="Bearing (°)")
    parser.add_argument("--speed",     type=float, default=None, help="Speed (m/s)")
    parser.add_argument("--group-id",  dest="group_id", type=int, default=0, help="Group ID for create-target")

    args = parser.parse_args()

    transport = SerialCobsTransport(args.port, args.baud)
    client = WeatherStationClient(transport)

    try:
        COMMANDS[args.cmd](client, args)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        transport.close()


if __name__ == "__main__":
    main()
