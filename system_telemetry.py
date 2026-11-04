"""
System Telemetry & Fallback Provider
Collects memory, battery status, disk drives, and platform hardware info.
"""

import psutil
import platform
import subprocess
from typing import Dict, Any, List

def get_system_hardware_info() -> Dict[str, Any]:
    # Memory
    vmem = psutil.virtual_memory()
    mem_info = {
        "total_gb": round(vmem.total / (1024 ** 3), 1),
        "used_gb": round(vmem.used / (1024 ** 3), 1),
        "available_gb": round(vmem.available / (1024 ** 3), 1),
        "percent": vmem.percent
    }

    # Battery
    battery_info = None
    try:
        bat = psutil.sensors_battery()
        if bat:
            battery_info = {
                "percent": bat.percent,
                "power_plugged": bat.power_plugged,
                "secsleft": bat.secsleft
            }
    except Exception:
        pass

    # Disk partitions
    disks: List[Dict[str, Any]] = []
    try:
        partitions = psutil.disk_partitions(all=False)
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                disks.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                    "used_gb": round(usage.used / (1024 ** 3), 1),
                    "free_gb": round(usage.free / (1024 ** 3), 1),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
    except Exception:
        pass

    return {
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "memory": mem_info,
        "battery": battery_info,
        "disks": disks
    }

if __name__ == "__main__":
    import pprint
    pprint.pprint(get_system_hardware_info())
