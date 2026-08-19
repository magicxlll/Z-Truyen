"""Configure platformio.ini for crosspoint simulator."""

from pathlib import Path

ini_path = Path("/root/crosspoint-reader/platformio.ini")
if ini_path.is_file():
    text = ini_path.read_text(encoding="utf-8")
    
    if "[env:simulator_x3]" in text:
        idx = text.find("[env:simulator_x3]")
        next_env = text.find("[env:", idx + 1)
        if next_env != -1:
            text = text[:idx] + text[next_env:]
        else:
            text = text[:idx]

    sim_section = """
[env:simulator_x3]
platform = native
build_type = release
lib_ldf_mode = deep+
lib_compat_mode = off
lib_deps =
  FreeInkUI=symlink://freeink-sdk/libs/ui/FreeInkUI
  Icons=symlink://freeink-sdk/libs/assets/Icons
  bblanchon/ArduinoJson @ 7.4.2
  ricmoo/QRCode @ 0.0.1
  bitbank2/AnimatedGIF @ 2.2.0
  https://github.com/crosspoint-reader/crosspoint-simulator.git
build_flags =
  -std=gnu++2a
  -Wno-narrowing
  -DSIMULATOR=1
  -DFREEINK_DEVICE_X3=1
  -DSIMULATOR_DEVICE_X3=1
  -DCROSSPOINT_VERSION=\\"1.1.2-simulator\\"
  -DENABLE_SERIAL_LOG
  -DLOG_LEVEL=3
  -I src/
"""
    text += sim_section
    ini_path.write_text(text, encoding="utf-8")
    print("Configured [env:simulator_x3] in platformio.ini")
