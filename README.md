# AeroThermal Monitor (V1.0)

A sleek, responsive dark-mode Windows hardware telemetry and thermal monitoring dashboard developed for the **Lenovo ThinkBook 14 G7+ IAH** featuring the **Intel Core Ultra 9 285H (Arrow Lake-H)** 16-Core processor.

![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20x86__64-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Version](https://img.shields.io/badge/Version-1.0.0-cyan)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## ⚡ Features in V1.0

- **🔥 16-Core CPU Matrix:**
  - Real-time live temperature readings for all 6 Performance Cores (P-Cores) and 10 Efficient Cores (E-Cores).
  - Dynamic thermal gauge bars with color transitions:
    - 🔵 Cool (< 52°C)
    - 🟢 Optimal (52°C - 68°C)
    - 🟡 Warm (68°C - 82°C)
    - 🔴 Hot (> 82°C)
  - Core load percentages (0–100%) and continuous Min/Max tracking per core.

- **📈 Real-Time Thermal Sparkline Chart:**
  - Smooth animated historical chart tracking Package Temperature and Peak Hottest Core over rolling samples.

- **🎮 Intel Arc 140T GPU Monitoring:**
  - Real-time core clock (MHz), 3D engine utilization, and shared memory usage.

- **🔋 Battery & Charging Health (L24N4PG7):**
  - State of charge %, battery voltage, design vs. full capacity, wear level, and Conservation Mode detection.

- **💾 System Memory & Storage:**
  - 32GB LPDDR5x RAM usage metrics and local storage volume statuses.

- **Zero Overhead Companion Mode:**
  - Interfaces directly with Core Temp's shared memory (`CoreTempMappingObject`) for 0% extra CPU overhead and instantaneous startup without UAC elevation.

---

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 (x86_64)
- Python 3.10+
- Dependencies:
  ```bash
  pip install customtkinter darkdetect psutil pythonnet
  ```

### Launching V1.0
Simply double-click:
```cmd
Launch_Thermal_Monitor.bat
```
or run from terminal:
```bash
python gui_app.py
```

---

## 📂 Project Structure

```
ThermalMonitor/
├── gui_app.py                 # CustomTkinter dark-mode graphical user interface
├── sensor_manager.py          # Unified telemetry coordinator & Min/Max tracker
├── core_temp_api.py           # Core Temp Shared Memory CTypes wrapper
├── lhm_api.py                 # LibreHardwareMonitorLib .NET integration
├── system_telemetry.py        # System storage, memory, and battery telemetries
├── hardware_monitor_lib/      # Bundled LibreHardwareMonitorLib .NET binaries
├── Launch_Thermal_Monitor.bat # 1-click standard launcher
└── Launch_Thermal_Monitor_Admin.bat # 1-click elevated launcher
```

---

## 📜 License
MIT License.
