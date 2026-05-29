# conky-grapes

## Fork

Forked from [popi's original](https://gitlab.nomagic.uk/popi/conky-grapes). Free to use under GPLv3.

## What is it

A Python/Lua config generator for [Conky](https://github.com/brndnmtthws/conky) that auto-detects your system hardware and builds a grape-shaped overlay with:

- CPU usage per thread (up to 6 threads), frequency, and temperature
- Disk I/O wait (top 3 processes)
- Memory (RAM and swap, top 3 processes)
- Filesystems (up to 3 mount points)
- Network (auto-detects Ethernet or Wi-Fi, shows up/down speed, totals, local and public IP)
- Battery (when present)
- Clock (hours, minutes, seconds as rings)
- Visual alerts: orange = warning, red = critical (temperature, disk space, battery)

Colours are configurable at generation time. The rings, title text, and body text each take an independent colour.

## Requirements

- Python 3.13+
- Conky (install `conky-all` / `conky-full` depending on your distro)
- `curl` (for public IP lookup)
- Fonts: `Play-Regular.ttf`, `Play-Bold.ttf`, `Michroma.ttf` (included in this repo - install to `~/.local/share/fonts/` or `/usr/share/fonts/`)

## Setup

```bash
# Clone to the expected path
git clone <repo-url> ~/.conky/conky-grapes
cd ~/.conky/conky-grapes

# Install fonts
cp *.ttf ~/.local/share/fonts/
fc-cache -f

# Generate config (auto-detects your hardware)
python3 create_config.py

# Start conky
conky -q -d -c ~/.conky/conky-grapes/conky_gen.conkyrc
```

If you use [uv](https://docs.astral.sh/uv/):

```bash
uv run create_config.py
```

## Usage

```
python3 create_config.py [-h] [-ri COLOR_RINGS] [-ti COLOR_TITLE] [-te COLOR_TEXT] [--old] [-v] [-r]
```

| Flag | Default | Description |
|---|---|---|
| `-ri` / `--color_rings` | `blue` | Ring and section title colour |
| `-ti` / `--color_title` | `skyblue` | Title text colour |
| `-te` / `--color_text` | `oldgold` | Body text colour |
| `--old` | off | Freetype < 2.8 compatibility mode (fixes font alignment on older systems) |
| `-r` / `--reload` | off | Refresh hardware detection only, keep existing colours |
| `-v` / `--verbose` | off | Verbose output |

Available colours: `yellow`, `lightyellow`, `oldgold`, `orange`, `lightorange`, `red`, `lightred`, `green`, `lightgreen`, `pink`, `lightpink`, `brown`, `lightbrown`, `blue`, `iceblue`, `skyblue`, `white`, `grey`, `lightgrey`, `black`, `violet`, `lightviolet`

## Network ring max speed

The network speed rings default to `max=12500 KiB/s` (~100 Mbps). Adjust `speed_configs` in `write_netconf_lua()` in `create_config.py` to match your connection:

| Connection | KiB/s |
|---|---|
| 100 Mbps | 12500 |
| 250 Mbps | 32000 |
| 1 Gbps | 128000 |

## Display position

`conky_tpl` contains `xinerama_head` (which monitor to use, 0-indexed) and `gap_x`/`gap_y` (pixel offset from the corner). Edit these before running the config generator if you need to place the overlay on a specific monitor.

## Re-running after hardware changes

If you add/remove disks, change your network interface, or move to a new machine, re-run `create_config.py`. If conky is already running, the updated config takes effect immediately (conky watches the file).

```
 -----------------------------
< ALL GLORY TO THE HYPNOTOAD! >
 -----------------------------
        \   ^__^
         \  (@@)\_______
            (__)\       )\/\
             U ||----w |
                ||     ||
```
