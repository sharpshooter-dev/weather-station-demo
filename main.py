import argparse
import sys
import myprotocol_pb2 as proto
from rich.console import Console
from rich.table import Table
from transport import SerialCobsTransport
from client import WeatherStationClient

console = Console()


def cmd_heartbeat(client: WeatherStationClient):
    console.print("[cyan]Sending heartbeat...[/cyan]")
    response = client.send_heartbeat()
    if response:
        console.print(f"[green]OK — device uptime: {response.uptime} ms[/green]")
    else:
        console.print("[red]No response[/red]")


def cmd_weather(client: WeatherStationClient):
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


def cmd_profiles(client: WeatherStationClient):
    console.print("[cyan]Requesting profile list...[/cyan]")
    result = client.list_profiles()
    if not result:
        console.print("[red]No response[/red]")
        return

    if not result.profiles:
        console.print("[yellow]No profiles stored[/yellow]")
        return

    table = Table(title="Profiles")
    table.add_column("ID",      style="cyan")
    table.add_column("Name")
    table.add_column("Muzzle Velocity")
    table.add_column("BC")
    table.add_column("Drag")
    for p in result.profiles:
        drag = "G7" if p.drag_function == proto.Profile.G7 else "G1"
        table.add_row(str(p.id), p.name, f"{p.muzzle_velocity:.0f} m/s", f"{p.ballistic_coef:.3f}", drag)
    console.print(table)


def cmd_targets(client: WeatherStationClient):
    console.print("[cyan]Requesting target list...[/cyan]")
    result = client.list_targets()
    if not result:
        console.print("[red]No response[/red]")
        return

    if not result.targets:
        console.print("[yellow]No targets stored[/yellow]")
        return

    table = Table(title="Targets")
    table.add_column("ID",        style="cyan")
    table.add_column("Name")
    table.add_column("Distance")
    table.add_column("Bearing")
    table.add_column("Speed")
    for t in result.targets:
        table.add_row(str(t.id), t.name, f"{t.distance:.0f} m", f"{t.bearing:.1f} °", f"{t.speed:.1f} m/s")
    console.print(table)


def cmd_listen(client: WeatherStationClient):
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
    "heartbeat": cmd_heartbeat,
    "weather":   cmd_weather,
    "profiles":  cmd_profiles,
    "targets":   cmd_targets,
    "listen":    cmd_listen,
}


def main():
    parser = argparse.ArgumentParser(description="Weather Station RS422 Test Tool")
    parser.add_argument("port", help="Serial port e.g. /dev/cu.usbserial-XXX or COM3")
    parser.add_argument("cmd",  choices=COMMANDS.keys())
    parser.add_argument("--baud", default=115200, type=int)
    args = parser.parse_args()

    transport = SerialCobsTransport(args.port, args.baud)
    client = WeatherStationClient(transport)

    try:
        COMMANDS[args.cmd](client)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        transport.close()


if __name__ == "__main__":
    main()
