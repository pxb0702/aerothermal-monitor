"""
Sensor Manager & History Tracker
Coordinates all hardware sensor providers, tracks Min/Max extremes, and manages history.
"""

import os
import ctypes
from typing import Dict, Any, List, Optional
from collections import deque

from core_temp_api import CoreTempClient
from lhm_api import LibreHardwareClient
import system_telemetry

def is_user_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

class SensorManager:
    def __init__(self, lhm_dll_dir: str):
        self.core_temp_client = CoreTempClient()
        self.lhm_client = LibreHardwareClient(lhm_dll_dir)
        
        # Min/Max Tracking Dictionaries
        self.min_temps: Dict[str, float] = {}
        self.max_temps: Dict[str, float] = {}

        # Historical samples for charting (last 40 data points)
        self.history_package_temp: deque = deque(maxlen=40)
        self.history_max_core_temp: deque = deque(maxlen=40)
        self.history_timestamps: deque = deque(maxlen=40)

        self.sample_count = 0

    def reset_min_max(self):
        self.min_temps.clear()
        self.max_temps.clear()

    def update_min_max(self, sensor_key: str, current_val: float) -> tuple[float, float]:
        if sensor_key not in self.min_temps or current_val < self.min_temps[sensor_key]:
            self.min_temps[sensor_key] = current_val
        if sensor_key not in self.max_temps or current_val > self.max_temps[sensor_key]:
            self.max_temps[sensor_key] = current_val
        return self.min_temps[sensor_key], self.max_temps[sensor_key]

    def poll_all_sensors(self) -> Dict[str, Any]:
        self.sample_count += 1
        
        # 1. Read Core Temp (CPU per-core)
        cpu_telemetry = self.core_temp_client.read_telemetry()
        core_temp_online = cpu_telemetry is not None

        # 2. Read LHM (GPU, Battery, Motherboard, Storage)
        lhm_telemetry = self.lhm_client.read_telemetry()

        # 3. Read System Info (RAM, OS, Disks)
        sys_telemetry = system_telemetry.get_system_hardware_info()

        # Process CPU Min/Max
        cpu_cores_processed: List[Dict[str, Any]] = []
        package_temp = 0.0

        if cpu_telemetry:
            package_temp = cpu_telemetry.get("package_temp", 0.0)
            p_min, p_max = self.update_min_max("cpu_package", package_temp)
            cpu_telemetry["min_package"] = p_min
            cpu_telemetry["max_package"] = p_max

            for core in cpu_telemetry["cores"]:
                c_id = core["id"]
                c_temp = core["temp"]
                c_min, c_max = self.update_min_max(f"cpu_core_{c_id}", c_temp)
                core["min_temp"] = c_min
                core["max_temp"] = c_max
                cpu_cores_processed.append(core)
            cpu_telemetry["cores"] = cpu_cores_processed

        # Update historical rolling window
        if package_temp > 0:
            self.history_package_temp.append(package_temp)
            highest_core = max([c["temp"] for c in cpu_cores_processed]) if cpu_cores_processed else package_temp
            self.history_max_core_temp.append(highest_core)

        # Process Battery
        battery_data = lhm_telemetry.get("battery") or {}
        if not battery_data.get("charge_percent") and sys_telemetry.get("battery"):
            battery_data["charge_percent"] = sys_telemetry["battery"]["percent"]
            battery_data["power_plugged"] = sys_telemetry["battery"]["power_plugged"]

        # Process GPU
        gpu_data = lhm_telemetry.get("gpu") or {}
        if gpu_data.get("temperatures"):
            for gt in gpu_data["temperatures"]:
                g_min, g_max = self.update_min_max(f"gpu_{gt['name']}", gt["value"])
                gt["min"] = g_min
                gt["max"] = g_max

        return {
            "is_admin": is_user_admin(),
            "core_temp_online": core_temp_online,
            "sample_index": self.sample_count,
            "cpu": cpu_telemetry,
            "gpu": gpu_data,
            "battery": battery_data,
            "memory": sys_telemetry.get("memory"),
            "motherboard": lhm_telemetry.get("motherboard"),
            "disks": sys_telemetry.get("disks", []),
            "history_package": list(self.history_package_temp),
            "history_max_core": list(self.history_max_core_temp)
        }

    def close(self):
        self.lhm_client.close()
