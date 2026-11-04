# AeroThermal Monitor (V2.0)

A sleek, responsive dark-mode Windows hardware telemetry and thermal monitoring dashboard developed for the **Lenovo ThinkBook 14 G7+ IAH** featuring the **Intel Core Ultra 9 285H (Arrow Lake-H)** 16-Core processor.

![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20x86__64-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Version](https://img.shields.io/badge/Version-2.0.0-cyan)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## ⚡ What's New in Version 2.0

- 🚀 **True Standalone Mode (Zero Core Temp Dependency):**
  - Operates completely standalone without requiring Core Temp running in the background.
  - Automatically detects whether Core Temp is active:
    - If Core Temp is open: Seamlessly binds via shared memory for $0\%$ extra CPU load.
    - If Core Temp is closed: Switches automatically to the **Native Standalone Engine**, calculating per-core live temperatures across all 16 physical cores.
  - Visual mode pill in header indicates `● STANDALONE MODE (Native Engine)` or `● COMPANION MODE (Core Temp)`.

- 🌡 **Full Multi-Component Temperature Tracking:**
  - **🔥 CPU (16 Cores):** Individual live temperatures, loads, and Min/Max trackers for 6 P-Cores & 10 E-Cores.
  - **🎮 GPU Core Temperature:** Real-time temperature for the Intel Arc 140T graphics tile with min/max tracking, 3D engine load, and core clock.
  - **🔋 Battery Pack Temperature:** Smart battery thermistor telemetry (ATL L24N4PG7) with min/max tracking, voltage, and Conservation Mode health.
  - **💾 NVMe SSD Temperature:** Dedicated controller temperature with min/max tracking and PCIe 4.0 health status for the YMTC NVMe SSD.

- 📈 **Real-Time Thermal Sparkline Chart:**
  - Live animated graph tracking Package Temperature vs. Hottest Core over rolling samples.

- 🛡 **Integrated Elevation Helper:**
  - One-click "Elevate Admin" button directly inside the app to unlock low-level kernel hooks when needed.

---

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 (x86_64)
- Python 3.10+
- Dependencies:
  ```bash
  pip install customtkinter darkdetect psutil pythonnet
  ```

### Launching the Application
Double-click:
```cmd
Launch_Thermal_Monitor.bat
```
Or for elevated hardware hooks:
```cmd
Launch_Thermal_Monitor_Admin.bat
```

---

## 📂 Project Structure

```
ThermalMonitor/
├── gui_app.py                 # CustomTkinter dark-mode graphical user interface (V2.0)
├── sensor_manager.py          # Unified telemetry coordinator & Standalone Engine
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
