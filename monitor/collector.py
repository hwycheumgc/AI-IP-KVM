"""
This is my code for reading basic hardware health numbers from the
computer. I want it to work the same way on Mac, Windows, and
Raspberry Pi, so I am using psutil, which already handles those
differences for me.
"""

import psutil
import time


def read_temperature():
    """
    I return a temperature reading in Celsius if the computer makes
    one available. A Mac often does not share this without extra
    drivers, Windows rarely shares it either, and a Raspberry Pi
    usually does. If nothing is available I return None, and the
    rest of my program just skips it.
    """
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        # I just grab the first reading I find
        for name, entries in temps.items():
            if entries:
                return entries[0].current
    except (AttributeError, NotImplementedError):
        return None
    return None


def read_metrics():
    """
    I take one snapshot of the machine's current health and return it
    as a plain dictionary, so it is easy for me to save it, send it,
    or hand it off to the part of my program that watches for
    problems.
    """
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu = psutil.cpu_percent(interval=0.5)

    return {
        "timestamp": time.time(),
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "temperature_c": read_temperature(),
    }


if __name__ == "__main__":
    # a quick manual check that I am reading real numbers
    print(read_metrics())
