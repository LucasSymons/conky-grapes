#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    This script creates configuration files for conky and lua based on
#    your machines's current resources.

##############################################################################

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see ihttp://www.gnu.org/licenses/gpl.html.
##############################################################################

import argparse
import re
from collections import OrderedDict
import sys
import os
import logging as log
from pathlib import Path, PurePath

# Initiating variables
home = os.path.expanduser("~")
working_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
src_lua = working_dir + "rings-v2_tpl"
dest_lua = working_dir + "rings-v2_gen.lua"
src_conky = working_dir + "conky_tpl"
dest_conky = working_dir + "conky_gen.conkyrc"

# Defaults is blue metrics and white font
## blue     | 34cdff
## white    | efefef

# for LUA config, this should not be changed.
default_fg_color = "0x34cdff"

couleurs = {
    "yellow": "fffd1d",
    "lightyellow": "e7dc64",
    "oldgold": "cab135",
    "orange": "ff8523",
    "lightorange": "e79064",
    "red": "ff1d2b",
    "lightred": "e7646a",
    "green": "1dff22",
    "lightgreen": "64e766",
    "pink": "d70751",
    "lightpink": "e78cb7",
    "brown": "b57131",
    "lightbrown": "ceab8a",
    "blue": "165cc4",
    "iceblue": "43d2e5",
    "skyblue": "8fd3ff",
    "white": "efefef",
    "grey": "323232",
    "lightgrey": "323232",
    "black": "000000",
    "violet": "bb07d7",
    "lightviolet": "a992e6",
    "ASSE": "006a32",
}


def init(
    rings: str, title: str, text: str, old: bool, reload: bool
) -> tuple[str, str, str, str, bool]:
    """Initialise display colours, optionally reloading from existing config."""
    if reload:
        with open(dest_conky, "r", encoding="utf-8") as f:
            filedata = f.read()
            matchconky = re.findall("^ +color[01] = '#([0-9a-f]{6})", filedata, re.M)
            log.info("colors were: {}".format(matchconky))

        with open(dest_lua, "r", encoding="utf-8") as f:
            filedata = f.read()
            matchlua = re.findall('^normal="0x([0-9a-f]{6})"', filedata, re.M)
            log.info("colors were: {}".format(matchlua))
            crings = "0x" + matchlua[0]
            ctitle = "#" + matchconky[0]
            ctext = "#" + matchconky[1]
    else:
        crings = "0x" + couleurs[rings]
        ctitle = "#" + couleurs[title]
        ctext = "#" + couleurs[text]
    ctextsize = "8"

    return crings, ctitle, ctext, ctextsize, old


def read_conf(filename: str) -> str | int:
    """Read file into a string and return it."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            filedata = f.read()
    except IOError:
        log.error("[Error] Could not open {}".format(filename))
        return 1
    return filedata


def write_conf(filedata: str, dest: str) -> None | int:
    """Write config string to destination file."""
    try:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(filedata)
    except IOError:
        log.error("[Error] Could not open {}".format(dest))
        return 1


def write_color_lua() -> None:
    """Replace the default ring colour in the generated Lua file."""
    datain = read_conf(dest_lua)
    filedata = datain.replace(default_fg_color, crings)
    write_conf(filedata, dest_lua)


def write_conf_blank(src: str, dest: str) -> None:
    """Render colour and font placeholders from template into dest."""
    filedata = read_conf(src)
    log.info("Overwriting config file {}".format(dest))
    filedata = filedata.replace("--{{ COLOR0 }}", "    color0 = '{}',".format(ctitle))
    filedata = filedata.replace("--{{ COLOR1 }}", "    color1 = '{}',".format(ctext))
    filedata = filedata.replace(
        "--{{ FONTTEXT }}", "    font = 'Play:normal:size={}',".format(ctextsize)
    )
    # conky does not expand ~ in lua_load; substitute the absolute path.
    filedata = filedata.replace("'~/", "'" + home + "/")

    write_conf(filedata, dest)


def hwmon_cpu_check(file: Path) -> bool | None:
    """Return True if the hwmon entry at file is a known CPU temperature driver."""
    kernel_driver_list = ["coretemp", "k10temp", "k8temp"]
    file_path = Path(PurePath(file, "name"))
    try:
        if file_path.exists():
            with file_path.open(encoding="ascii") as f:
                driver_name = f.read()
            if driver_name.strip().lower() in (
                item.lower() for item in kernel_driver_list
            ):
                return True
    except Exception as e:
        log.error("failed to find hwmon path. {0}".format(e))


def cpu_temperature() -> dict[str, str]:
    """Return hwmon index and temp input number for the CPU temperature sensor."""
    cpu_temp: dict[str, str] = {}
    hwmon_path = Path("/sys/class/hwmon")
    temp_candidates = [dirs for dirs in hwmon_path.iterdir() if dirs.is_dir()]
    try:
        for i in temp_candidates:
            if hwmon_cpu_check(i):
                p = Path(i)
                pp = PurePath(i, "temp1_input")
                log.info("Path is {}".format(p))
                if p.exists():
                    cpu_temp["number_hwmon"] = re.search(r"\d+$", pp.parent.name).group(
                        0
                    )
                    cpu_temp["number_temp"] = re.sub(r".*(\d+).*$", r"\1", pp.name)
                    break
    except Exception as e:
        log.error("failed to find cpu temperature. {0}".format(e))

    log.info("Temperature for cpu: {0}".format(cpu_temp))
    return cpu_temp


def cpu_number() -> int:
    """Return the number of CPU threads to display (capped at 6)."""
    # beyond 6 it gets ugly
    max_cpu_display = 6

    with open("/proc/cpuinfo", encoding="utf-8") as f:
        nbcpu = 0
        for line in f:
            if line.strip():
                if line.rstrip("\n").startswith("cpu MHz"):
                    nbcpu += 1

    if nbcpu >= max_cpu_display:
        nbcpu = max_cpu_display

    log.info("Number of CPU(s) kept: {0}".format(nbcpu))
    return nbcpu


def interface_up(interface: str) -> bool:
    """Return True if the given network interface reports operstate 'up'."""
    path = f"/sys/class/net/{interface}/operstate"
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if "up" in line:
                    return True
    return False


def route_interface() -> list[str | bool]:
    """Return [interface_name, is_wifi] for the default gateway interface."""
    gwinterface = "no_gateway_interface"
    with open("/proc/net/route", encoding="utf-8") as f:
        for line in f:
            routeinfo = line.split("\t")
            if routeinfo[1] == "00000000" and interface_up(routeinfo[0]):
                gwinterface = routeinfo[0]

    log.info("Gateway interface: {0}".format(gwinterface))

    iswifi = False
    if os.path.isfile("/proc/net/wireless"):
        with open("/proc/net/wireless", encoding="utf-8") as f:
            for line in f:
                wifi = line.split(":")
                if len(wifi) > 1:
                    log.info("wifi interface: {0}".format(wifi[0].strip()))
                    if wifi[0].strip() == gwinterface:
                        iswifi = True
    return [gwinterface, iswifi]


def disk_select() -> list[str]:
    """Return up to 3 locally mounted filesystem mount points to monitor."""
    disks: list[str] = []
    with open("/proc/mounts", encoding="utf-8") as f:
        for line in f:
            diskinfo = line.split(" ")
            match1 = re.search(r"^/[a-zA-Z-_]+.", diskinfo[0], re.M | re.I)
            match2 = re.search(
                r"^(fuse|bind|nfs|tmpfs|efi|boot|boot/efi)", diskinfo[2], re.M | re.I
            )
            match3 = re.search(
                r"^\/(fuse|bind|nfs|tmpfs|efi|boot)", diskinfo[1], re.M | re.I
            )
            if match2 or match3:
                continue
            elif match1:
                disks.append(diskinfo[1])
    disks.sort()

    if len(disks) > 3:
        diskKeep = disks[:3]
        log.info(
            "Keeping 3 first locally mounted filesystem identified: {0}".format(
                diskKeep
            )
        )
    else:
        diskKeep = disks
    return diskKeep


def meminfo() -> OrderedDict:
    """Return the contents of /proc/meminfo as an ordered dictionary."""
    mem: OrderedDict = OrderedDict()

    with open("/proc/meminfo", encoding="utf-8") as f:
        for line in f:
            mem[line.split(":")[0]] = line.split(":")[1].strip()

    log.info("Total memory: {0}".format(mem["MemTotal"]))
    log.info("Free memory: {0}".format(mem["MemFree"]))
    return mem


def write_batconf() -> None:
    """Detect battery presence and write battery Lua and conky config blocks."""
    BAT = None
    log.info("Looking for battery info")
    for i in range(2):
        if Path("/sys/class/power_supply/BAT{}/uevent".format(i)).exists():
            BAT = i
        elif Path("/proc/acpi/battery/BAT{}/state".format(i)).exists():
            BAT = i

    if BAT is not None:
        log.info("Found battery info!")
        batconf_lua = []
        batconf_conky = []
        alpha = 0.6
        radius = 18
        thickness = 10
        log.info("- Calculating index for battery in lua watch_battery")
        # 9 => lua starts at 0 | 2 for mem, 2 for network, 1 for temp, 3 for time
        index = cpunb + len(disks) + 9
        log.info("  Battery index = {}".format(index))
        data = {
            "arg": "BAT{}".format(BAT),
            "bg_alpha": alpha,
            "radius": radius,
            "thickness": thickness,
        }

        log.info("Writing lua BATTERY config in config file")
        new_block = """    {{
        name='battery_percent',
        arg='{arg}', max=100,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=274, y=464,
        radius={radius},
        thickness={thickness},
        start_angle=180,
        end_angle=420
    }},""".format(**data)

        batconf_lua.append(new_block)
        filedata = read_conf(dest_lua)
        filedata = filedata.replace("--{{ BATTERY }}", "".join(batconf_lua))
        filedata = filedata.replace(
            "--{{ BATTERY_WATCH }}",
            'index={}\n    battery=tonumber(conky_parse("${{battery_percent {arg} }}"))'.format(
                index, **data
            ),
        )
        filedata = filedata.replace("--{{ BATTERY_ACTIVATE }}", "battery_watch()")
        write_conf(filedata, dest_lua)

        log.info("Writing conky BATTERY config in config file")
        if old:
            new_block = (
                "${font Michroma:size=10}${color0}${goto 296}${voffset 22}BATTERY"
            )
            new_block += "\n${{font}}${{color0}}${{goto 280}}${{voffset 1}}${{color1}}${{battery_percent {arg}}}%".format(
                **data
            )
        else:
            new_block = (
                "${font Michroma:size=10}${color0}${goto 296}${voffset 28}BATTERY"
            )
            new_block += "\n${{font}}${{color0}}${{goto 280}}${{voffset -4}}${{color1}}${{battery_percent {arg}}}%".format(
                **data
            )

        batconf_conky.append(new_block)
        filedata = read_conf(dest_conky)
        filedata = filedata.replace("#{{ BATTERY }}", "".join(batconf_conky))
        filedata = filedata.replace(
            "#{{ OS }}",
            "${font Michroma:bold:size=11}${color0}${voffset 50}${alignc}${execi 3600 awk -F '=' '/PRETTY_NAME/ { print $2 }' /etc/os-release | tr -d '\"'}",
        )
        write_conf(filedata, dest_conky)
    else:
        new_block = "${font Michroma:bold:size=11}${color0}${voffset 90}${alignc}${execi 3600 awk -F '=' '/PRETTY_NAME/ { print $2 }' /etc/os-release | tr -d '\"'}"
        filedata = read_conf(dest_conky)
        filedata = filedata.replace("#{{ BATTERY }}", "")
        filedata = filedata.replace("#{{ OS }}", new_block)
        write_conf(filedata, dest_conky)


def write_fsconf_lua(disk: list[str], cpunb: int) -> None:
    """Write filesystem ring definitions into the Lua config."""
    fsconf_lua = []
    fsconf_watch = []
    alpha = 0.8
    radius = 40
    alpha_scale = 0.2
    thickness = 10
    index_start = cpunb + 4
    log.info("index_start is {}".format(index_start))

    for cpt in range(len(disk)):
        data = {
            "arg": disk[cpt],
            "bg_alpha": alpha,
            "radius": radius,
            "thickness": thickness,
        }

        new_block = """\n    {{
        name='fs_used_perc',
        arg='{arg}',
        max=100,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=220, y=280,
        radius={radius},
        thickness={thickness},
        start_angle=0,
        end_angle=240
    }},""".format(**data)

        fsconf_lua.append(new_block)
        index = index_start + cpt
        with open(working_dir + "fs_watch", encoding="utf-8") as f:
            for line in f:
                test = re.sub(r"FILESYS", data["arg"], line)
                fsconf_watch.append(re.sub(r"INDEX", format(index), test))

        alpha -= alpha_scale
        radius -= thickness + 1
        thickness -= 1

    log.info("Writing FILESYSTEM LUA config in config file")
    filedata = read_conf(dest_lua)
    filedata = filedata.replace("--{{ FILESYSTEM }}", "".join(fsconf_lua))
    write_conf(filedata, dest_lua)

    log.info("Writing DISK_WATCH lua config in config file")
    filedata = read_conf(dest_lua)
    filedata = filedata.replace("--{{ DISK_WATCH }}", "".join(fsconf_watch))
    write_conf(filedata, dest_lua)


def write_fsconf_conky(fs: list[str]) -> None:
    """Write filesystem usage text rows into the conky config."""
    conf = []
    if old:
        voffset = -80
    else:
        voffset = -81
    fs_max = 3

    for cpt in range(len(fs)):
        if cpt > 0:
            voffset = -1
        data = {"voffset": voffset, "filesys": "{}".format(fs[cpt])}

        new_block = "${{goto 70}}${{voffset {voffset}}}{filesys}${{color1}}${{alignr 310}}${{fs_used {filesys}}} / ${{fs_size {filesys}}}\n".format(
            **data
        )
        conf.append(new_block)

    log.info("adjusting voffset for FS...")
    if old:
        adjust = 12 + ((fs_max - len(fs)) * 10)
    else:
        adjust = 8 + ((fs_max - len(fs)) * 10)
    new_block = "${{font Michroma:size=10}}${{color0}}${{goto 68}}${{voffset {0}}}FILESYSTEM".format(
        adjust
    )
    conf.append(new_block)

    log.info("Writing FS conky config in config file")
    filedata = read_conf(dest_conky)
    filedata = filedata.replace("#{{ FILESYSTEM }}", "".join(conf))
    write_conf(filedata, dest_conky)


def write_cpuconf_lua(cpunb: int) -> None:
    """Write CPU ring definitions into the Lua config."""
    cpuconf_lua = []
    radius = 86
    thickness_max = 13
    alpha = 0.7
    alpha_scale = 0.4 / cpunb
    log.info("We have {} CPUs".format(cpunb))

    if cpunb > 4:
        thickness_max -= cpunb - 3
        radius = 88
    thickness = thickness_max

    for cpt in range(cpunb):
        data = {
            "arg": "cpu{}".format(cpt + 1),
            "bg_alpha": alpha,
            "radius": radius,
            "thickness": thickness,
        }

        new_block = """\n    {{
        name='cpu',
        arg='{arg}',
        max=100,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=200, y=120,
        radius={radius},
        thickness={thickness},
        start_angle=0,
        end_angle=240
    }},""".format(**data)

        cpuconf_lua.append(new_block)
        alpha -= alpha_scale
        radius -= thickness + 1
        thickness -= 0.5

    log.info("Writing CPU LUA config in config file")
    filedata = read_conf(dest_lua)
    filedata = filedata.replace("--{{ CPU }}", "".join(cpuconf_lua))
    write_conf(filedata, dest_lua)


def write_cpuconf_conky(cpunb: int) -> None:
    """Write CPU usage text rows into the conky config."""
    cpuconf = []
    if old:
        voffset = 2
    else:
        voffset = 1

    if cpunb > 4:
        if cpunb >= 6:
            voffset = -3
        else:
            if old:
                voffset = 0.5
            else:
                voffset = -1

    log.info("voffest is set to {}".format(voffset))

    for cpt in range(cpunb):
        data = {"voffset": voffset, "cpu": "{}".format(cpt + 1)}

        new_block = "${{voffset {voffset}}}${{goto 120}}${{color1}}CPU {cpu}${{alignr 330}}${{color1}}${{cpu cpu{cpu}}}%\n".format(
            **data
        )
        cpuconf.append(new_block)

    log.info("adjusting voffset for top cpu processes...")
    if cpunb > 4:
        adjust = 12 - (voffset * cpunb)
    else:
        adjust = 28 - (voffset * cpunb)

    if old:
        new_block = "${{goto 50}}${{voffset {0}}}${{color1}}${{top name 1}}${{alignr 306}}${{top cpu 1}}%".format(
            adjust
        )
    else:
        new_block = "${{goto 49}}${{voffset {0}}}${{color1}}${{top name 1}}${{alignr 306}}${{top cpu 1}}%".format(
            adjust
        )

    cpuconf.append(new_block)

    log.info("Writing CPU conky config in config file")
    filedata = read_conf(dest_conky)
    filedata = filedata.replace("#{{ CPU }}", "".join(cpuconf))
    write_conf(filedata, dest_conky)


def write_diskioconf_conky() -> None:
    """Write disk I/O wait text rows into the conky config."""
    ioconf = []
    if old:
        voffset = 2
    else:
        if cpunb > 4:
            voffset = -1
        else:
            voffset = 1

    log.info("voffest is set to {}".format(voffset))

    new_block = "${voffset -130}${goto 378}${font}${color1}${top_io name 1}${alignr 30}${top_io io_write 1}%\n"
    ioconf.append(new_block)

    for cpt in range(2, 4):
        data = {"voffset": voffset, "io": "{}".format(cpt)}
        new_block = "${{goto 378}}${{voffset {voffset}}}${{color1}}${{top_io name {io}}}${{alignr 30}}${{top_io io_write {io}}}%\n".format(
            **data
        )
        ioconf.append(new_block)

    if old:
        new_block = "${goto 370}${voffset 8}${color1}disk writes${alignr 30}${diskio_write}%\n${goto 370}${color1}disk reads${alignr 30}${diskio_read}%\n${font Michroma:size=10}${color0}${goto 418}${voffset 2}IO WAIT"
    else:
        new_block = "${goto 370}${voffset 4}${color1}disk writes${alignr 30}${diskio_write}%\n${goto 370}${color1}disk reads${alignr 30}${diskio_read}%\n${font Michroma:size=10}${color0}${goto 418}${voffset 1}IO WAIT\n"
    ioconf.append(new_block)

    log.info("Writing IO conky config in config file")
    filedata = read_conf(dest_conky)
    filedata = filedata.replace("#{{ DISKIO }}", "".join(ioconf))
    write_conf(filedata, dest_conky)


def write_tempconf_conky(temperature: dict[str, str]) -> None:
    """Write CPU frequency and temperature text into the conky config."""
    tempconf = []

    log.info("Starting Temperature config")
    new_block = (
        "${voffset 12}${color1}${goto 106}${freq_g cpu0} Ghz${alignr 330}${hwmon "
        + temperature["number_hwmon"]
        + " temp "
        + temperature["number_temp"]
        + "} °C"
    )
    tempconf.append(new_block)
    log.info("temperature = {}".format(tempconf))

    log.info("Writing TEMPERATURE conky config in config file")
    filedata = read_conf(dest_conky)
    filedata = filedata.replace("#{{ TEMPERATURE }}", "".join(tempconf))
    write_conf(filedata, dest_conky)


def write_tempconf_lua(temperature: dict[str, str]) -> None:
    """Write CPU temperature ring definition into the Lua config."""
    tempconf_lua = []
    data = {
        "arg": "{} temp {}".format(
            temperature["number_hwmon"], temperature["number_temp"]
        )
    }

    new_block = """\n    {{
        name='hwmon',
        arg='{arg}',
        max=110,
        bg_colour=0x3b3b3b,
        bg_alpha=0.8,
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=200, y=120,
        radius=97,
        thickness=4,
        start_angle=0,
        end_angle=240
    }},""".format(**data)

    tempconf_lua.append(new_block)
    tempconf_watch = 'temperature=tonumber(conky_parse("${hwmon ' + data["arg"] + '}"))'

    log.info("Writing TEMPERATURE LUA config in config file")
    filedata = read_conf(dest_lua)
    filedata = filedata.replace("--{{ TEMPERATURE }}", "".join(tempconf_lua))
    write_conf(filedata, dest_lua)

    log.info("Writing TEMPERATURE_WATCH lua config in config file")
    filedata = read_conf(dest_lua)
    filedata = filedata.replace("--{{ TEMPERATURE_WATCH }}", "".join(tempconf_watch))
    write_conf(filedata, dest_lua)


def write_memconf_conky() -> None:
    """Write memory usage text rows into the conky config."""
    memconf = []

    log.info("Starting Memory config")
    if old:
        new_block = "${font Michroma:size=10}${color0}${goto 394}${voffset 79}MEMORY\n${font}${goto 324}${voffset -4}${color1}${top_mem name 1}${alignr 40}${top_mem mem 1}%\n"
    else:
        new_block = "${font Michroma:size=10}${color0}${goto 394}${voffset 59}MEMORY\n${font}${goto 324}${voffset -4}${color1}${top_mem name 1}${alignr 40}${top_mem mem 1}%\n"

    memconf.append(new_block)

    for cpt in range(2, 4):
        data = {"mem": "{}".format(cpt)}
        new_block = "${{goto 324}}${{color1}}${{top_mem name {mem}}}${{alignr 40}}${{top_mem mem {mem}}}%\n".format(
            **data
        )
        memconf.append(new_block)

    if old:
        new_block = "${voffset 14}${goto 348}${color1}SWAP${alignr 40}${color1}${swap} / ${color1}${swapmax}\n${voffset 3}${goto 348}${color1}RAM ${alignr 40}${color1}${mem} / ${color1}${memmax}\n"
    else:
        new_block = "${voffset 8}${goto 348}${color1}SWAP${alignr 40}${color1}${swap} / ${color1}${swapmax}\n${voffset 1}${goto 348}${color1}RAM ${alignr 40}${color1}${mem} / ${color1}${memmax}\n"
    memconf.append(new_block)
    log.info("memconf = {}".format(memconf))

    log.info("Writing MEMORY conky config in config file")
    filedata = read_conf(dest_conky)
    filedata = filedata.replace("#{{ MEMORY }}", "".join(memconf))
    write_conf(filedata, dest_conky)


def write_netconf_lua(interface: list[str | bool]) -> None:
    """Write network speed ring definitions into the Lua config.

    Ring max values are in KiB/s. Adjust these to match your connection speed:
    100 Mbps = 12500 KiB/s, 250 Mbps = 32000 KiB/s, 1 Gbps = 128000 KiB/s.
    """
    netconf_lua = []
    alpha = 0.8
    radius = 30
    alpha_scale = 0.2
    thickness = 12

    # Separate max for down/up; tune to your connection speed in KiB/s.
    speed_configs = [
        ("downspeedf", 128000),  # 128000 KiB/s ≈ 1 Gbps down
        ("upspeedf", 128000),  # 128000 KiB/s ≈ 1 Gbps up
    ]

    for speed, max_speed in speed_configs:
        data = {
            "name": speed,
            "arg": interface[0],
            "max": max_speed,
            "bg_alpha": alpha,
            "radius": radius,
            "thickness": thickness,
        }

        new_block = """\n    {{
        name='{name}',
        arg='{arg}',
        max={max},
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=290, y=345,
        radius={radius},
        thickness={thickness},
        start_angle=180,
        end_angle=420
    }},""".format(**data)

        netconf_lua.append(new_block)
        alpha -= alpha_scale
        radius -= thickness + 1
        thickness -= 1

    log.info("Writing NETWORK LUA config in config file")
    filedata = read_conf(dest_lua)
    filedata = filedata.replace("--{{ NETWORK }}", "".join(netconf_lua))
    write_conf(filedata, dest_lua)


def write_netconf_conky(interface: list[str | bool]) -> None:
    """Write network interface text block into the conky config."""
    netconf = []
    if interface[0] == "no_gateway_interface":
        log.warning("No default route on the system! Tachikoma, what is happening?!")

        with open(working_dir + "nonetconf", encoding="utf-8") as f:
            for line in f:
                netconf.append(line)
        log.info("Writing NETWORK conky config in config file")
        filedata = read_conf(dest_conky)
        filedata = filedata.replace("#{{ NETWORK }}", "".join(netconf))
        write_conf(filedata, dest_conky)

    elif interface[1] is True:
        log.info("Setting up Wifi as main interface")
        if old:
            with open(working_dir + "wificonf_old", encoding="utf-8") as f:
                for line in f:
                    netconf.append(re.sub(r"INTERFACE", interface[0], line))
        else:
            with open(working_dir + "wificonf", encoding="utf-8") as f:
                for line in f:
                    netconf.append(re.sub(r"INTERFACE", interface[0], line))

        log.info("Writing NETWORK conky config in config file")
        filedata = read_conf(dest_conky)
        filedata = filedata.replace("#{{ NETWORK }}", "".join(netconf))
        write_conf(filedata, dest_conky)
    else:
        log.info("Setting up NIC as main interface")
        if old:
            with open(working_dir + "ethconf_old", encoding="utf-8") as f:
                for line in f:
                    netconf.append(re.sub(r"INTERFACE", interface[0], line))
        else:
            with open(working_dir + "ethconf", encoding="utf-8") as f:
                for line in f:
                    netconf.append(re.sub(r"INTERFACE", interface[0], line))

        log.info("Writing NETWORK conky config in config file")
        filedata = read_conf(dest_conky)
        filedata = filedata.replace("#{{ NETWORK }}", "".join(netconf))
        write_conf(filedata, dest_conky)


def write_timeconf_conky() -> None:
    """Write time and date text block into the conky config."""
    timeconf = []

    log.info("Starting Time config")
    if old:
        new_block = "${font Michroma:size=10}${alignr 300}${voffset -40}${color0}${time %a} ${color0}${time %x}\n${font Michroma:size=18}${alignr 318}${color1}${voffset -4}${time %H}:${time %M}"
    else:
        new_block = "${font Michroma:size=10}${alignr 300}${voffset -50}${color0}${time %a} ${color0}${time %x}\n${font Michroma:size=18}${alignr 318}${color1}${voffset -4}${time %H}:${time %M}"

    timeconf.append(new_block)

    log.info("Writing TIME conky config in config file")
    filedata = read_conf(dest_conky)
    filedata = filedata.replace("#{{ TIME }}", "".join(timeconf))
    write_conf(filedata, dest_conky)


# main
if __name__ == "__main__":
    print("Digging in the system to gather info...\n")

    parser = argparse.ArgumentParser(
        description="Creates/overwrites conky and lua configuration for conky-grapes adjustments to your system."
    )
    parser.add_argument(
        "-ri",
        "--color_rings",
        dest="rings",
        metavar="COLOR_RINGS",
        default="blue",
        choices=couleurs,
        help="the textual color for the rings and titles, among: {0}".format(
            " ".join(couleurs.keys())
        ),
    )
    parser.add_argument(
        "-ti",
        "--color_title",
        dest="title",
        metavar="COLOR_TITLE",
        default="skyblue",
        choices=couleurs,
        help="the textual color for the title display, see COLOR_RINGS \
                            for accepted values."
        "",
    )
    parser.add_argument(
        "-te",
        "--color_text",
        dest="text",
        metavar="COLOR_TEXT",
        default="oldgold",
        choices=couleurs,
        help="the textual color for the text display, see COLOR_RINGS \
                            for accepted values.",
    )
    parser.add_argument(
        "--old_freetype",
        "--old",
        dest="old",
        action="store_true",
        help='small adjustments for systems using older version of freetype (< 2.8). Most notably the font size decimal delimiter is changed from "." to ",". This is worth a try if you notice bad alignment of bad font display.',
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="verbose mode, displays gathered info as we found it.",
    )
    parser.add_argument(
        "-r",
        "--reload",
        dest="reload",
        action="store_true",
        help="Only refresh configuration resource-wise. Colors will stay the same as previously.",
    )

    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    log.info("Arguments received: {}".format(args))

    crings, ctitle, ctext, ctextsize, old = init(
        args.rings, args.title, args.text, args.old, args.reload
    )
    write_conf_blank(src_lua, dest_lua)
    write_conf_blank(src_conky, dest_conky)

    temperature = cpu_temperature()
    cpunb = cpu_number()
    mem = meminfo()
    interface = route_interface()
    disks = disk_select()

    write_tempconf_lua(temperature)
    write_cpuconf_lua(cpunb)
    write_fsconf_lua(disks, cpunb)
    write_netconf_lua(interface)

    write_tempconf_conky(temperature)
    write_cpuconf_conky(cpunb)
    write_diskioconf_conky()
    write_memconf_conky()
    write_fsconf_conky(disks)
    write_netconf_conky(interface)
    write_timeconf_conky()

    write_batconf()
    write_color_lua()

    msg_ok = (
        "\n    *** Success! ***\n\nNew config files have been created:"
        "\n- {}\n- {} \n\nIf you add a previous conky-grapes running,"
        " the update should be instantaneous. If conky-grapes is not"
        " running, you can activate it with following command:\n"
        "conky -q -d -c ~/.conky/conky-grapes/conky_gen.conkyrc\n\n"
        "If it runs but text is not aligned or font is horribly wrong"
        " (and you installed required fonts), chances are you are using an"
        " old version of freetype2 (< 2.8). The '--old' option when creating"
        " your conky configuration file should address this."
    )
    print(msg_ok.format(dest_conky, dest_lua))
