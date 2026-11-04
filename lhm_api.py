"""
LibreHardwareMonitorLib Wrapper
Provides full system telemetry for Motherboard, Memory, GPU, Storage, and Battery.
"""

import os
import sys
import clr
from typing import Dict, Any, Optional, List

class LibreHardwareClient:
    def __init__(self, dll_dir: str):
        self.dll_dir = os.path.abspath(dll_dir)
        self.is_loaded = False
        self.computer = None
        self._initialize()

    def _initialize(self):
        try:
            sys.path.append(self.dll_dir)
            dll_path = os.path.join(self.dll_dir, "LibreHardwareMonitorLib.dll")
            if not os.path.exists(dll_path):
                print(f"[LHM] DLL not found at {dll_path}")
                return

            clr.AddReference(dll_path)
            from LibreHardwareMonitor.Hardware import Computer

            c = Computer()
            c.IsCpuEnabled = True
            c.IsGpuEnabled = True
            c.IsBatteryEnabled = True
            c.IsStorageEnabled = True
            c.IsMotherboardEnabled = True
            c.IsMemoryEnabled = True
            c.IsNetworkEnabled = False
            c.Open()

            self.computer = c
            self.is_loaded = True
        except Exception as e:
            print(f"[LHM] Error initializing: {e}")
            self.is_loaded = False

    def read_telemetry(self) -> Dict[str, Any]:
        result = {
            "gpu": None,
            "battery": None,
            "memory": None,
            "motherboard": None,
            "storage": [],
            "cpu_fallback": None
        }

        if not self.is_loaded or not self.computer:
            return result

        try:
            from LibreHardwareMonitor.Hardware import SensorType

            for h in self.computer.Hardware:
                h.Update()
                htype = str(h.HardwareType)

                # Motherboard
                if htype == "Motherboard":
                    mb_temps = []
                    for s in h.Sensors:
                        if s.SensorType == SensorType.Temperature and s.Value is not None:
                            mb_temps.append({"name": s.Name, "value": round(float(s.Value), 1)})
                    result["motherboard"] = {
                        "name": h.Name,
                        "temperatures": mb_temps
                    }

                # GPU
                elif "Gpu" in htype:
                    gpu_data = {
                        "name": h.Name,
                        "type": htype,
                        "temperatures": [],
                        "clock_mhz": None,
                        "power_w": None,
                        "load_3d": None,
                        "memory_used_mb": None,
                        "memory_total_mb": None
                    }
                    for s in h.Sensors:
                        val = s.Value
                        if val is None:
                            continue
                        stype = str(s.SensorType)
                        sname = str(s.Name)

                        if stype == "Temperature":
                            gpu_data["temperatures"].append({
                                "name": sname,
                                "value": round(float(val), 1)
                            })
                        elif stype == "Clock" and "Core" in sname:
                            gpu_data["clock_mhz"] = round(float(val), 0)
                        elif stype == "Power":
                            gpu_data["power_w"] = round(float(val), 1)
                        elif stype == "Load" and "3D" in sname:
                            gpu_data["load_3d"] = round(float(val), 1)
                        elif "Memory Used" in sname:
                            gpu_data["memory_used_mb"] = round(float(val), 0)
                        elif "Memory Total" in sname:
                            gpu_data["memory_total_mb"] = round(float(val), 0)
                    result["gpu"] = gpu_data

                # Battery
                elif htype == "Battery":
                    bat_data = {
                        "name": h.Name,
                        "charge_percent": None,
                        "voltage_v": None,
                        "degradation_percent": None,
                        "remaining_mwh": None,
                        "designed_mwh": None,
                        "full_mwh": None,
                        "power_w": None
                    }
                    for s in h.Sensors:
                        val = s.Value
                        if val is None:
                            continue
                        sname = str(s.Name)
                        if "Charge Level" in sname:
                            bat_data["charge_percent"] = round(float(val), 1)
                        elif "Voltage" in sname:
                            bat_data["voltage_v"] = round(float(val), 2)
                        elif "Degradation" in sname:
                            bat_data["degradation_percent"] = round(float(val), 1)
                        elif "Remaining Capacity" in sname:
                            bat_data["remaining_mwh"] = round(float(val), 0)
                        elif "Designed Capacity" in sname:
                            bat_data["designed_mwh"] = round(float(val), 0)
                        elif "Fully-Charged" in sname:
                            bat_data["full_mwh"] = round(float(val), 0)
                        elif "Rate" in sname:
                            bat_data["power_w"] = round(float(val), 1)
                    result["battery"] = bat_data

                # Storage / SSD
                elif htype == "Storage":
                    disk_temps = []
                    for s in h.Sensors:
                        if s.SensorType == SensorType.Temperature and s.Value is not None:
                            disk_temps.append({"name": s.Name, "value": round(float(s.Value), 1)})
                    result["storage"].append({
                        "name": h.Name,
                        "temperatures": disk_temps
                    })

                # CPU (when elevated, LHM has CPU temps directly)
                elif htype == "Cpu":
                    cpu_temps = []
                    for s in h.Sensors:
                        if s.SensorType == SensorType.Temperature and s.Value is not None:
                            cpu_temps.append({"name": s.Name, "value": round(float(s.Value), 1)})
                    if cpu_temps:
                        result["cpu_fallback"] = {
                            "name": h.Name,
                            "temperatures": cpu_temps
                        }

        except Exception as e:
            print(f"[LHM] Read error: {e}")

        return result

    def close(self):
        if self.computer:
            try:
                self.computer.Close()
            except:
                pass
            self.computer = None
