"""
Core Temp Shared Memory API Wrapper
Enables high-performance, zero-overhead per-core temperature monitoring.
"""

import ctypes
from ctypes import wintypes
from typing import Dict, Any, Optional, List

class CoreTempSharedDataEx(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('uiLoad', wintypes.UINT * 256),
        ('uiTjMax', wintypes.UINT * 128),
        ('uiCoreCnt', wintypes.UINT),
        ('uiCPUCnt', wintypes.UINT),
        ('fTemp', ctypes.c_float * 256),
        ('fVID', ctypes.c_float),
        ('fCPUSpeed', ctypes.c_float),
        ('fFSBSpeed', ctypes.c_float),
        ('fMultiplier', ctypes.c_float),
        ('sCPUName', ctypes.c_char * 100),
        ('ucFahrenheit', ctypes.c_ubyte),
        ('ucDeltaToTjMax', ctypes.c_ubyte),
        ('ucTdpSupported', ctypes.c_ubyte),
        ('ucPowerSupported', ctypes.c_ubyte),
        ('uiStructVersion', wintypes.UINT),
        ('uiTdp', wintypes.UINT * 128),
        ('fPower', ctypes.c_float * 128),
        ('fMultipliers', ctypes.c_float * 256),
    ]

FILE_MAP_READ = 0x0004
kernel32 = ctypes.windll.kernel32
kernel32.OpenFileMappingW.restype = wintypes.HANDLE
kernel32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.MapViewOfFile.restype = ctypes.c_void_p
kernel32.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
kernel32.UnmapViewOfFile.restype = wintypes.BOOL
kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

class CoreTempClient:
    def __init__(self):
        self.mapping_name = "CoreTempMappingObject"

    def is_available(self) -> bool:
        h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, self.mapping_name)
        if h_map and h_map != 0:
            kernel32.CloseHandle(h_map)
            return True
        return False

    def read_telemetry(self) -> Optional[Dict[str, Any]]:
        h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, self.mapping_name)
        if not h_map or h_map == 0:
            return None

        size = ctypes.sizeof(CoreTempSharedDataEx)
        p_buf = kernel32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, size)
        if not p_buf:
            kernel32.CloseHandle(h_map)
            return None

        try:
            raw = CoreTempSharedDataEx.from_address(p_buf)
            core_count = int(raw.uiCoreCnt)
            if core_count <= 0 or core_count > 128:
                core_count = 16  # fallback

            cores: List[Dict[str, Any]] = []
            temps: List[float] = []
            loads: List[int] = []

            for i in range(core_count):
                temp_val = round(float(raw.fTemp[i]), 1)
                load_val = int(raw.uiLoad[i])
                temps.append(temp_val)
                loads.append(load_val)
                
                # Distinguish P-Cores vs E-Cores for Arrow Lake / Core Ultra
                core_type = "P-Core" if i < 6 else "E-Core"
                core_num = (i + 1) if i < 6 else (i - 5)
                cores.append({
                    "id": i,
                    "name": f"{core_type} #{core_num}",
                    "temp": temp_val,
                    "load": load_val,
                    "multiplier": round(float(raw.fMultipliers[i]), 1) if raw.fMultipliers[i] > 0 else 0
                })

            cpu_name = raw.sCPUName.decode('ascii', errors='ignore').strip()
            if not cpu_name:
                cpu_name = "Intel Core Ultra Processor"

            package_temp = max(temps) if temps else 0.0
            avg_temp = round(sum(temps) / len(temps), 1) if temps else 0.0

            result = {
                "source": "CoreTemp (Shared Memory)",
                "cpu_name": cpu_name,
                "core_count": core_count,
                "tj_max": int(raw.uiTjMax[0]) if raw.uiTjMax[0] > 0 else 105,
                "clock_mhz": round(float(raw.fCPUSpeed), 1),
                "vid_volts": round(float(raw.fVID), 3),
                "power_watts": round(float(raw.fPower[0]), 1) if raw.fPower[0] > 0 else None,
                "package_temp": package_temp,
                "avg_temp": avg_temp,
                "cores": cores,
                "overall_load": round(sum(loads) / len(loads), 1) if loads else 0
            }
            return result
        finally:
            kernel32.UnmapViewOfFile(ctypes.c_void_p(p_buf))
            kernel32.CloseHandle(h_map)

if __name__ == "__main__":
    client = CoreTempClient()
    print("Available:", client.is_available())
    data = client.read_telemetry()
    if data:
        print(f"Read {data['core_count']} cores from {data['cpu_name']}")
        print(f"Package Temp: {data['package_temp']}°C, Clock: {data['clock_mhz']} MHz")
