"""
AeroThermal Monitor - Modern Dark Mode Hardware Monitor
Featuring live per-core temperature bars, min/max tracking, and system telemetry.
"""

import os
import sys
import time
import math
import ctypes
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Ensure local imports work properly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from sensor_manager import SensorManager, is_user_admin

# Theme Colors
DARK_BG = "#0f1115"
PANEL_BG = "#181b20"
CARD_BG = "#1f232b"
CARD_BORDER = "#2b313d"
ACCENT_CYAN = "#00d2ff"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
TEXT_PRIMARY = "#f3f4f6"
TEXT_SECONDARY = "#9ca3af"
TEXT_MUTED = "#6b7280"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CoreCard(ctk.CTkFrame):
    """Visual card for an individual CPU core displaying temp, min/max, load, and live bars."""
    def __init__(self, master, core_id: int, core_name: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER, **kwargs)
        self.core_id = core_id
        self.core_name = core_name

        self.grid_columnconfigure(1, weight=1)

        # Header: Name and Load
        self.lbl_name = ctk.CTkLabel(
            self, text=core_name, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_PRIMARY, anchor="w"
        )
        self.lbl_name.grid(row=0, column=0, padx=(10, 5), pady=(8, 2), sticky="w")

        self.lbl_load = ctk.CTkLabel(
            self, text="0%", font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED, anchor="e"
        )
        self.lbl_load.grid(row=0, column=1, padx=(5, 10), pady=(8, 2), sticky="e")

        # Current Temperature
        self.lbl_temp = ctk.CTkLabel(
            self, text="-- °C", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ACCENT_CYAN, anchor="w"
        )
        self.lbl_temp.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 2), sticky="w")

        # Visual Temperature Bar (0 to 105°C)
        self.bar_temp = ctk.CTkProgressBar(
            self, height=7, corner_radius=4,
            progress_color=ACCENT_CYAN, fg_color="#282d37"
        )
        self.bar_temp.set(0)
        self.bar_temp.grid(row=2, column=0, columnspan=2, padx=10, pady=(2, 6), sticky="ew")

        # Footer: Min / Max tracking
        self.lbl_minmax = ctk.CTkLabel(
            self, text="Min: --°C  |  Max: --°C", font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED, anchor="w"
        )
        self.lbl_minmax.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

    def update_data(self, temp: float, load: int, min_temp: float, max_temp: float, tj_max: int = 105):
        # Determine color based on temperature severity
        if temp < 52.0:
            color = ACCENT_CYAN
        elif temp < 68.0:
            color = ACCENT_GREEN
        elif temp < 82.0:
            color = ACCENT_AMBER
        else:
            color = ACCENT_RED

        self.lbl_temp.configure(text=f"{temp:.1f} °C", text_color=color)
        self.lbl_load.configure(text=f"{load}% load")
        self.lbl_minmax.configure(text=f"Min: {min_temp:.1f}°C  |  Max: {max_temp:.1f}°C")

        # Progress fraction
        ratio = max(0.0, min(1.0, temp / float(tj_max)))
        self.bar_temp.set(ratio)
        self.bar_temp.configure(progress_color=color)


class SparklineCanvas(ctk.CTkCanvas):
    """Custom smooth canvas for real-time temperature graph."""
    def __init__(self, master, width=600, height=130, **kwargs):
        super().__init__(
            master, width=width, height=height,
            bg=CARD_BG, highlightthickness=0, **kwargs
        )
        self.width = width
        self.height = height

    def draw_chart(self, package_history: list, max_core_history: list):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50:
            w = self.width
        if h < 30:
            h = self.height

        pad_x = 40
        pad_y = 20
        chart_w = w - pad_x - 15
        chart_h = h - (pad_y * 2)

        # Baseline grid lines (40°C, 60°C, 80°C, 100°C)
        min_scale = 30.0
        max_scale = 100.0
        scale_range = max_scale - min_scale

        for mark in [40, 60, 80, 100]:
            y = (h - pad_y) - ((mark - min_scale) / scale_range) * chart_h
            self.create_line(pad_x, y, pad_x + chart_w, y, fill="#2b313d", dash=(3, 3))
            self.create_text(pad_x - 5, y, text=f"{mark}°C", fill=TEXT_MUTED, font=("Segoe UI", 8), anchor="e")

        if not package_history or len(package_history) < 2:
            self.create_text(w // 2, h // 2, text="Collecting real-time thermal samples...", fill=TEXT_MUTED, font=("Segoe UI", 11))
            return

        def get_coords(data):
            coords = []
            n = len(data)
            step = chart_w / (max(n - 1, 1))
            for idx, val in enumerate(data):
                x = pad_x + idx * step
                v_clamped = max(min_scale, min(max_scale, val))
                y = (h - pad_y) - ((v_clamped - min_scale) / scale_range) * chart_h
                coords.extend([x, y])
            return coords

        # Draw Hottest Core Line (Amber)
        if len(max_core_history) >= 2:
            c_coords = get_coords(max_core_history)
            self.create_line(c_coords, fill=ACCENT_AMBER, width=2, smooth=True)

        # Draw Package Line (Cyan)
        p_coords = get_coords(package_history)
        self.create_line(p_coords, fill=ACCENT_CYAN, width=2, smooth=True)

        # Legend at top right
        self.create_oval(w - 180, 8, w - 172, 16, fill=ACCENT_CYAN, outline="")
        self.create_text(w - 130, 12, text="Package Temp", fill=TEXT_PRIMARY, font=("Segoe UI", 9))
        self.create_oval(w - 75, 8, w - 67, 16, fill=ACCENT_AMBER, outline="")
        self.create_text(w - 30, 12, text="Peak Core", fill=TEXT_PRIMARY, font=("Segoe UI", 9))


class AeroThermalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AeroThermal Monitor - ThinkBook 14 G7+")
        self.geometry("1100x760")
        self.minsize(980, 680)
        self.configure(fg_color=DARK_BG)

        # Initialize Hardware Sensor Manager
        dll_dir = os.path.join(SCRIPT_DIR, "hardware_monitor_lib")
        self.sensor_mgr = SensorManager(dll_dir)
        self.refresh_rate_ms = 1000
        self.is_paused = False

        self._build_ui()
        self._start_update_loop()

    def _build_ui(self):
        # 1. Top Header Bar
        self.header_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=65)
        self.header_frame.pack(fill="x", side="top", padx=0, pady=0)

        # Title & Subtitle
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=10)

        lbl_app_title = ctk.CTkLabel(
            title_box, text="⚡ AEROTHERMAL MONITOR",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_PRIMARY
        )
        lbl_app_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box, text="Lenovo ThinkBook 14 G7+ IAH  •  Intel Core Ultra 9 285H (16 Cores)",
            font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY
        )
        self.lbl_subtitle.pack(anchor="w")

        # Right Controls
        ctrl_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        ctrl_box.pack(side="right", padx=20, pady=10)

        self.btn_reset = ctk.CTkButton(
            ctrl_box, text="↺ Reset Min/Max", width=110, height=32,
            fg_color="#2b313d", hover_color="#374151", text_color=TEXT_PRIMARY,
            command=self._on_reset_minmax
        )
        self.btn_reset.pack(side="left", padx=5)

        self.btn_pause = ctk.CTkButton(
            ctrl_box, text="⏸ Pause", width=80, height=32,
            fg_color="#2b313d", hover_color="#374151", text_color=TEXT_PRIMARY,
            command=self._toggle_pause
        )
        self.btn_pause.pack(side="left", padx=5)

        if not is_user_admin():
            self.btn_elevate = ctk.CTkButton(
                ctrl_box, text="🛡 Elevate Admin", width=120, height=32,
                fg_color="#7c3aed", hover_color="#6d28d9", text_color=TEXT_PRIMARY,
                command=self._elevate_admin
            )
            self.btn_elevate.pack(side="left", padx=5)

        # 2. Top Summary KPI Cards (CPU, GPU, Battery, RAM)
        kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        kpi_container.pack(fill="x", padx=20, pady=(15, 10))
        kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        # KPI 1: CPU Package
        self.card_cpu = self._create_kpi_card(
            kpi_container, 0, "CPU PACKAGE TEMP", "-- °C", "Min: -- | Max: --", ACCENT_CYAN
        )
        # KPI 2: GPU Status
        self.card_gpu = self._create_kpi_card(
            kpi_container, 1, "INTEL ARC 140T GPU", "-- MHz", "Load: --% | VRAM: --", ACCENT_GREEN
        )
        # KPI 3: Battery Status
        self.card_bat = self._create_kpi_card(
            kpi_container, 2, "BATTERY (L24N4PG7)", "-- %", "Voltage: -- V", ACCENT_AMBER
        )
        # KPI 4: Memory (RAM)
        self.card_mem = self._create_kpi_card(
            kpi_container, 3, "SYSTEM MEMORY", "-- GB", "Usage: --%", "#a78bfa"
        )

        # 3. Main Content Tab View
        self.tabview = ctk.CTkTabview(
            self, fg_color=PANEL_BG, segmented_button_fg_color="#2b313d",
            segmented_button_selected_color=ACCENT_CYAN,
            segmented_button_selected_hover_color="#0ea5e9"
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        self.tab_cores = self.tabview.add("  🔥 CPU 16-Core Matrix  ")
        self.tab_graph = self.tabview.add("  📈 Thermal History Chart  ")
        self.tab_system = self.tabview.add("  💻 Full Component Telemetry  ")

        self._build_cores_tab()
        self._build_graph_tab()
        self._build_system_tab()

    def _create_kpi_card(self, parent, col, title, main_val, sub_val, accent_color):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        card.grid(row=0, column=col, padx=6, pady=0, sticky="ew")

        lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        lbl_t.pack(anchor="w", padx=12, pady=(10, 0))

        lbl_v = ctk.CTkLabel(card, text=main_val, font=ctk.CTkFont(size=24, weight="bold"), text_color=accent_color)
        lbl_v.pack(anchor="w", padx=12, pady=(2, 0))

        lbl_s = ctk.CTkLabel(card, text=sub_val, font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY)
        lbl_s.pack(anchor="w", padx=12, pady=(0, 10))

        return {"frame": card, "val": lbl_v, "sub": lbl_s}

    def _build_cores_tab(self):
        # Scrollable Frame for the 16 cores
        self.scroll_cores = ctk.CTkScrollableFrame(self.tab_cores, fg_color="transparent")
        self.scroll_cores.pack(fill="both", expand=True, padx=5, pady=5)

        # 4 Columns Grid
        self.scroll_cores.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="cores")

        self.core_cards: list[CoreCard] = []
        for i in range(16):
            core_name = f"P-Core #{i+1}" if i < 6 else f"E-Core #{i-5}"
            card = CoreCard(self.scroll_cores, core_id=i, core_name=core_name)
            row = i // 4
            col = i % 4
            card.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
            self.core_cards.append(card)

    def _build_graph_tab(self):
        frame = ctk.CTkFrame(self.tab_graph, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_desc = ctk.CTkLabel(
            frame, text="Real-Time Thermal Sparkline (Package vs Hottest Core over last 40 samples)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY
        )
        lbl_desc.pack(anchor="w", pady=(0, 10))

        self.chart_canvas = SparklineCanvas(frame, height=260)
        self.chart_canvas.pack(fill="both", expand=True, pady=5)

    def _build_system_tab(self):
        self.scroll_sys = ctk.CTkScrollableFrame(self.tab_system, fg_color="transparent")
        self.scroll_sys.pack(fill="both", expand=True, padx=5, pady=5)
        self.scroll_sys.grid_columnconfigure((0, 1), weight=1, uniform="sys_col")

        # Left Column: Battery & Power
        self.box_battery = ctk.CTkFrame(self.scroll_sys, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        self.box_battery.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(self.box_battery, text="🔋 BATTERY & CHARGING HEALTH", font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_AMBER).pack(anchor="w", padx=15, pady=(12, 6))
        self.lbl_bat_details = ctk.CTkLabel(self.box_battery, text="Scanning battery hardware...", font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY, justify="left")
        self.lbl_bat_details.pack(anchor="w", padx=15, pady=(0, 15))

        # Right Column: GPU & Memory
        self.box_gpu = ctk.CTkFrame(self.scroll_sys, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        self.box_gpu.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(self.box_gpu, text="🎮 GRAPHICS & ACCELERATOR", font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_GREEN).pack(anchor="w", padx=15, pady=(12, 6))
        self.lbl_gpu_details = ctk.CTkLabel(self.box_gpu, text="Scanning graphics sensors...", font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY, justify="left")
        self.lbl_gpu_details.pack(anchor="w", padx=15, pady=(0, 15))

        # Left Column Row 1: Motherboard & Platform
        self.box_mb = ctk.CTkFrame(self.scroll_sys, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        self.box_mb.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(self.box_mb, text="🖥 MOTHERBOARD & BIOS", font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_CYAN).pack(anchor="w", padx=15, pady=(12, 6))
        self.lbl_mb_details = ctk.CTkLabel(self.box_mb, text="Motherboard: Lenovo ThinkBook 14 G7+\nBIOS Version: R6CN17WW", font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY, justify="left")
        self.lbl_mb_details.pack(anchor="w", padx=15, pady=(0, 15))

        # Right Column Row 1: Storage & NVMe
        self.box_storage = ctk.CTkFrame(self.scroll_sys, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        self.box_storage.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(self.box_storage, text="💾 STORAGE & DRIVES", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a78bfa").pack(anchor="w", padx=15, pady=(12, 6))
        self.lbl_disk_details = ctk.CTkLabel(self.box_storage, text="Scanning storage drives...", font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY, justify="left")
        self.lbl_disk_details.pack(anchor="w", padx=15, pady=(0, 15))

    def _start_update_loop(self):
        self._update_telemetry()

    def _update_telemetry(self):
        if not self.is_paused:
            try:
                data = self.sensor_mgr.poll_all_sensors()
                self._apply_data_to_ui(data)
            except Exception as e:
                print(f"[UI] Update error: {e}")

        self.after(self.refresh_rate_ms, self._update_telemetry)

    def _apply_data_to_ui(self, data: dict):
        cpu = data.get("cpu")
        gpu = data.get("gpu") or {}
        bat = data.get("battery") or {}
        mem = data.get("memory") or {}
        disks = data.get("disks") or []

        # 1. Update CPU KPI & Core Cards
        if cpu:
            pkg_temp = cpu.get("package_temp", 0.0)
            min_pkg = cpu.get("min_package", pkg_temp)
            max_pkg = cpu.get("max_package", pkg_temp)
            clock = cpu.get("clock_mhz", 0)
            power = cpu.get("power_watts")

            power_str = f" | {power:.1f}W" if power else ""
            self.card_cpu["val"].configure(text=f"{pkg_temp:.1f} °C")
            self.card_cpu["sub"].configure(text=f"Min: {min_pkg:.1f}° | Max: {max_pkg:.1f}° | {clock:.0f}MHz{power_str}")

            cores_list = cpu.get("cores", [])
            for c_info in cores_list:
                cid = c_info["id"]
                if cid < len(self.core_cards):
                    self.core_cards[cid].update_data(
                        temp=c_info["temp"],
                        load=c_info["load"],
                        min_temp=c_info.get("min_temp", c_info["temp"]),
                        max_temp=c_info.get("max_temp", c_info["temp"]),
                        tj_max=cpu.get("tj_max", 105)
                    )
        else:
            self.card_cpu["val"].configure(text="Offline")
            self.card_cpu["sub"].configure(text="Start Core Temp or Run as Admin")

        # 2. Update GPU KPI & Details
        gpu_clock = gpu.get("clock_mhz")
        gpu_load = gpu.get("load_3d")
        gpu_vram = gpu.get("memory_used_mb")
        vram_total = gpu.get("memory_total_mb")

        gpu_val_text = f"{gpu_clock:.0f} MHz" if gpu_clock else "Active"
        gpu_sub_text = f"Load: {gpu_load or 0:.0f}%" + (f" | VRAM: {gpu_vram/1024:.1f}G" if gpu_vram else "")
        self.card_gpu["val"].configure(text=gpu_val_text)
        self.card_gpu["sub"].configure(text=gpu_sub_text)

        gpu_detail_text = (
            f"Device: {gpu.get('name', 'Intel(R) Arc(TM) 140T GPU (16GB)')}\n"
            f"Core Clock: {gpu_clock or 'N/A'} MHz\n"
            f"3D Engine Load: {gpu_load or 0:.1f} %\n"
            f"D3D Shared Memory: {gpu_vram or 'N/A'} MB / {vram_total or 'N/A'} MB"
        )
        self.lbl_gpu_details.configure(text=gpu_detail_text)

        # 3. Update Battery KPI & Details
        charge = bat.get("charge_percent", 0.0)
        voltage = bat.get("voltage_v", 0.0)
        deg = bat.get("degradation_percent", 0.0)
        rem_mwh = bat.get("remaining_mwh", 0)
        des_mwh = bat.get("designed_mwh", 85000)

        self.card_bat["val"].configure(text=f"{charge:.0f} %")
        self.card_bat["sub"].configure(text=f"{voltage:.2f} V • Conservation Active" if charge < 85 else f"{voltage:.2f} V")

        bat_detail_text = (
            f"Battery Model: L24N4PG7 (ATL Smart Battery)\n"
            f"State of Charge: {charge:.1f} %\n"
            f"Voltage: {voltage:.3f} V\n"
            f"Remaining Energy: {rem_mwh:,.0f} mWh\n"
            f"Designed Capacity: {des_mwh:,.0f} mWh\n"
            f"Battery Health / Wear: {deg:+.1f} %\n"
            f"Power Mode: AC Wall Adapter Connected"
        )
        self.lbl_bat_details.configure(text=bat_detail_text)

        # 4. Update Memory KPI
        if mem:
            mem_pct = mem.get("percent", 0)
            mem_used = mem.get("used_gb", 0)
            mem_tot = mem.get("total_gb", 32)
            self.card_mem["val"].configure(text=f"{mem_used:.1f} / {mem_tot:.0f} GB")
            self.card_mem["sub"].configure(text=f"Usage: {mem_pct:.1f}% of LPDDR5x")

        # 5. Storage Details
        if disks:
            disk_lines = ["Local Storage Volumes:"]
            for d in disks:
                disk_lines.append(f"  • {d['device']} ({d['mountpoint']}) - {d['used_gb']} GB used of {d['total_gb']} GB ({d['percent']}%)")
            self.lbl_disk_details.configure(text="\n".join(disk_lines))

        # 6. Historical Chart
        p_hist = data.get("history_package", [])
        m_hist = data.get("history_max_core", [])
        self.chart_canvas.draw_chart(p_hist, m_hist)

    def _on_reset_minmax(self):
        self.sensor_mgr.reset_min_max()

    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        self.btn_pause.configure(text="▶ Resume" if self.is_paused else "⏸ Pause")

    def _elevate_admin(self):
        """Relaunch the app with Windows Administrator elevation."""
        try:
            script_path = os.path.abspath(__file__)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
            self.destroy()
        except Exception as e:
            print(f"Failed to elevate: {e}")

    def on_closing(self):
        self.sensor_mgr.close()
        self.destroy()

if __name__ == "__main__":
    app = AeroThermalApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
