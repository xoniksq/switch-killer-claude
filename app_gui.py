import os
import sys
import time
import datetime
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from config import load_config, save_config, get_claude_executable_path
from engine import KillSwitchEngine, IPInfo

# Set global appearance: Pitch Dark / Monochrome Chrome
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class ClaudeKillSwitchGUI(ctk.CTk):
    # Chrome Monochrome Palette
    BG_ROOT = "#09090B"           # Deep OLED Black
    BG_CARD = "#121214"           # Obsidian Surface
    BG_INNER = "#050505"          # Pitch Black Panel
    BORDER_CHROME = "#27272A"     # Subtle Metallic Border
    BORDER_HIGHLIGHT = "#71717A"  # Silver Chrome Border
    BORDER_ARMED = "#E4E4E7"      # Platinum White Highlight
    BORDER_ALERT = "#EF4444"      # Alert Crimson
    
    TEXT_MAIN = "#FFFFFF"         # Crisp Pure White
    TEXT_MUTED = "#A1A1AA"        # Chrome Silver Secondary
    TEXT_DIM = "#52525B"          # Dark Titanium Label
    TEXT_MONO = "#E4E4E7"         # Terminal Silver

    def __init__(self):
        super().__init__()

        self.title("Claude Kill Switch — Chrome Edition")
        self.geometry("780x740")
        self.minsize(720, 660)
        self.configure(fg_color=self.BG_ROOT)

        # Set window icon if exists
        icon_file = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_file):
            try:
                self.iconbitmap(icon_file)
            except Exception:
                pass

        # Config & Engine
        self.config_data = load_config()
        self.engine = KillSwitchEngine(self.config_data)

        # Setup engine callbacks
        self.engine.on_log = self._handle_log
        self.engine.on_status_change = self._handle_status_change
        self.engine.on_ip_update = self._handle_ip_update
        self.engine.on_kill = self._handle_kill_event

        self._build_ui()

        # Start engine
        self.engine.start()

        # Initial check
        self.after(600, self._initial_ip_check)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # Log expands

        # ==================== 1. TOP HEADER ====================
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        title = ctk.CTkLabel(
            title_row,
            text="CLAUDE KILL SWITCH",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.TEXT_MAIN
        )
        title.pack(side="left")

        version_badge = ctk.CTkFrame(
            title_row,
            fg_color="#18181B",
            corner_radius=6,
            border_width=1,
            border_color=self.BORDER_CHROME
        )
        version_badge.pack(side="right")
        ctk.CTkLabel(
            version_badge,
            text="CHROME EDITION",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=self.TEXT_MUTED
        ).pack(padx=10, pady=3)

        subtitle = ctk.CTkLabel(
            header,
            text="HARDWARE-LEVEL ANTI-LEAK NETWORK MONITOR FOR ANTHROPIC CLAUDE",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=self.TEXT_DIM
        )
        subtitle.pack(anchor="w", pady=(3, 0))

        # ==================== 2. STATUS CARD ====================
        self.status_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=self.BG_CARD,
            border_width=1,
            border_color=self.BORDER_CHROME
        )
        self.status_card.grid(row=1, column=0, padx=24, pady=8, sticky="ew")
        self.status_card.grid_columnconfigure(0, weight=1)
        self.status_card.grid_columnconfigure(1, weight=1)

        # Left Column: State indicator
        badge_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        badge_frame.grid(row=0, column=0, padx=22, pady=20, sticky="nsew")

        self.status_dot = ctk.CTkLabel(
            badge_frame,
            text="○",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.TEXT_DIM
        )
        self.status_dot.pack(anchor="w")

        self.status_title = ctk.CTkLabel(
            badge_frame,
            text="STANDBY",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.TEXT_MAIN
        )
        self.status_title.pack(anchor="w", pady=(2, 0))

        self.status_desc = ctk.CTkLabel(
            badge_frame,
            text="Protection disarmed. Click 'ARM PROTECTION' to lock your current VPN connection.",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_MUTED,
            wraplength=320,
            justify="left"
        )
        self.status_desc.pack(anchor="w", pady=(6, 0))

        # Right Column: Network Data Grid
        info_frame = ctk.CTkFrame(
            self.status_card,
            fg_color=self.BG_INNER,
            corner_radius=8,
            border_width=1,
            border_color=self.BORDER_CHROME
        )
        info_frame.grid(row=0, column=1, padx=20, pady=16, sticky="nsew")
        info_frame.grid_columnconfigure(1, weight=1)

        # Data rows
        def make_row(parent, r, label, val_widget):
            ctk.CTkLabel(
                parent,
                text=label,
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color=self.TEXT_DIM
            ).grid(row=r, column=0, padx=12, pady=5, sticky="w")
            val_widget.grid(row=r, column=1, padx=12, pady=5, sticky="w")

        self.lbl_current_ip = ctk.CTkLabel(
            info_frame,
            text="Detecting...",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=self.TEXT_MAIN
        )
        make_row(info_frame, 0, "CURRENT IP", self.lbl_current_ip)

        self.lbl_location = ctk.CTkLabel(
            info_frame,
            text="...",
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_MUTED
        )
        make_row(info_frame, 1, "LOCATION", self.lbl_location)

        self.lbl_isp = ctk.CTkLabel(
            info_frame,
            text="...",
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_MUTED
        )
        make_row(info_frame, 2, "NETWORK / ISP", self.lbl_isp)

        self.lbl_locked_ip = ctk.CTkLabel(
            info_frame,
            text="UNLOCKED",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=self.TEXT_DIM
        )
        make_row(info_frame, 3, "LOCKED IP", self.lbl_locked_ip)

        # ==================== 3. ACTION CONTROLS ====================
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, padx=24, pady=8, sticky="ew")
        ctrl_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Chrome White Button
        self.btn_arm_toggle = ctk.CTkButton(
            ctrl_frame,
            text="ARM PROTECTION",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#FFFFFF",
            hover_color="#E4E4E7",
            text_color="#000000",
            corner_radius=8,
            height=44,
            command=self._toggle_arm
        )
        self.btn_arm_toggle.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        # Sleek Obsidian Outline Button
        self.btn_launch_claude = ctk.CTkButton(
            ctrl_frame,
            text="LAUNCH CLAUDE",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#18181B",
            hover_color="#27272A",
            border_width=1,
            border_color=self.BORDER_CHROME,
            text_color=self.TEXT_MAIN,
            corner_radius=8,
            height=44,
            command=self._launch_claude
        )
        self.btn_launch_claude.grid(row=0, column=1, padx=6, sticky="ew")

        # Monochrome Panic Kill
        self.btn_panic_kill = ctk.CTkButton(
            ctrl_frame,
            text="PANIC KILL",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#18181B",
            hover_color="#2D1518",
            border_width=1,
            border_color="#7F1D1D",
            text_color="#F87171",
            corner_radius=8,
            height=44,
            command=self._panic_kill
        )
        self.btn_panic_kill.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        # ==================== 4. SETTINGS STRIP ====================
        settings_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=self.BG_CARD,
            border_width=1,
            border_color=self.BORDER_CHROME
        )
        settings_frame.grid(row=3, column=0, padx=24, pady=6, sticky="ew")
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)

        switch_args = {
            "font": ctk.CTkFont(size=12),
            "text_color": self.TEXT_MUTED,
            "progress_color": "#FFFFFF",
            "button_color": "#E4E4E7",
            "button_hover_color": "#FFFFFF",
            "command": self._update_settings
        }

        self.switch_strict = ctk.CTkSwitch(
            settings_frame,
            text="Kill on network loss",
            **switch_args
        )
        self.switch_strict.grid(row=0, column=0, padx=16, pady=12, sticky="w")
        if self.config_data.get("strict_mode", True):
            self.switch_strict.select()

        self.switch_sound = ctk.CTkSwitch(
            settings_frame,
            text="System error sound",
            **switch_args
        )
        self.switch_sound.grid(row=0, column=1, padx=16, pady=12, sticky="w")
        if self.config_data.get("sound_alarm", True):
            self.switch_sound.select()

        self.switch_autoguard = ctk.CTkSwitch(
            settings_frame,
            text="Block on RU IP",
            **switch_args
        )
        self.switch_autoguard.grid(row=0, column=2, padx=16, pady=12, sticky="w")
        if self.config_data.get("auto_guard", True):
            self.switch_autoguard.select()

        # ==================== 5. CHROME TERMINAL LOG ====================
        log_container = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=self.BG_CARD,
            border_width=1,
            border_color=self.BORDER_CHROME
        )
        log_container.grid(row=4, column=0, padx=24, pady=(6, 20), sticky="nsew")
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_container, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        lbl_log = ctk.CTkLabel(
            log_header,
            text="SYSTEM CONSOLE LOG",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=self.TEXT_DIM
        )
        lbl_log.grid(row=0, column=0, sticky="w")

        btn_clear_log = ctk.CTkButton(
            log_header,
            text="CLEAR",
            width=54,
            height=22,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#18181B",
            hover_color="#27272A",
            border_width=1,
            border_color=self.BORDER_CHROME,
            text_color=self.TEXT_MUTED,
            command=self._clear_log
        )
        btn_clear_log.grid(row=0, column=1, sticky="e")

        self.log_textbox = ctk.CTkTextbox(
            log_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=self.BG_INNER,
            text_color=self.TEXT_MONO,
            border_width=1,
            border_color=self.BORDER_CHROME,
            wrap="word"
        )
        self.log_textbox.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

    # ==================== LOG & STATUS CALLBACKS ====================

    def _handle_log(self, message: str, level: str):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        tags = {
            "INFO": "[INFO] ",
            "SUCCESS": "[OK]   ",
            "WARNING": "[WARN] ",
            "ERROR": "[FAIL] ",
            "CRITICAL": "[ALERT]"
        }
        tag = tags.get(level, "[SYS]  ")
        line = f"[{now_str}] {tag} {message}\n"

        def append():
            self.log_textbox.insert("end", line)
            self.log_textbox.see("end")

        self.after(0, append)

    def _handle_status_change(self, state: str, message: str):
        def update():
            if state == KillSwitchEngine.STATE_ARMED:
                self.status_card.configure(border_color=self.BORDER_ARMED)
                self.status_dot.configure(text="●", text_color="#FFFFFF")
                self.status_title.configure(text="ARMED & PROTECTED", text_color="#FFFFFF")
                self.status_desc.configure(
                    text="Network connection locked. Instant process termination will trigger upon any IP variation or adapter drop."
                )
                self.btn_arm_toggle.configure(
                    text="DISARM",
                    fg_color="#18181B",
                    hover_color="#27272A",
                    border_width=1,
                    border_color=self.BORDER_HIGHLIGHT,
                    text_color="#FFFFFF"
                )
                if self.engine.locked_ip:
                    self.lbl_locked_ip.configure(
                        text=f"{self.engine.locked_ip} [{self.engine.locked_country_code}]",
                        text_color="#FFFFFF"
                    )

            elif state == KillSwitchEngine.STATE_TRIGGERED:
                self.status_card.configure(border_color=self.BORDER_ALERT)
                self.status_dot.configure(text="▲", text_color=self.BORDER_ALERT)
                self.status_title.configure(text="SYSTEM TRIGGERED", text_color=self.BORDER_ALERT)
                self.status_desc.configure(
                    text=f"CRITICAL: Claude was forcefully terminated. Trigger reason: {message}"
                )
                self.btn_arm_toggle.configure(
                    text="RESET & RE-ARM",
                    fg_color="#7F1D1D",
                    hover_color="#991B1B",
                    border_width=1,
                    border_color=self.BORDER_ALERT,
                    text_color="#FFFFFF"
                )

            else:  # DISARMED
                self.status_card.configure(border_color=self.BORDER_CHROME)
                self.status_dot.configure(text="○", text_color=self.TEXT_DIM)
                self.status_title.configure(text="STANDBY", text_color=self.TEXT_MAIN)
                self.status_desc.configure(
                    text="Protection disarmed. Click 'ARM PROTECTION' to lock your current VPN connection."
                )
                self.btn_arm_toggle.configure(
                    text="ARM PROTECTION",
                    fg_color="#FFFFFF",
                    hover_color="#E4E4E7",
                    border_width=0,
                    text_color="#000000"
                )
                self.lbl_locked_ip.configure(text="UNLOCKED", text_color=self.TEXT_DIM)

        self.after(0, update)

    def _handle_ip_update(self, info: IPInfo):
        def update():
            if info.ip:
                self.lbl_current_ip.configure(
                    text=f"{info.ip}  ({info.latency_ms:.0f}ms)",
                    text_color=self.TEXT_MAIN
                )
                loc_text = f"{info.country_code} — {info.country}, {info.city}" if info.country else "Resolving..."
                self.lbl_location.configure(text=loc_text)
                self.lbl_isp.configure(text=info.isp or "Unknown Network")
            elif info.error:
                self.lbl_current_ip.configure(text="CONNECTION OFFLINE", text_color=self.BORDER_ALERT)
                self.lbl_location.configure(text=info.error)

        self.after(0, update)

    def _handle_kill_event(self, reason: str, killed: list):
        def show_alert():
            msg = f"CLAUDE KILL SWITCH TRIGGERED\n\nReason: {reason}\n\n"
            if killed:
                msg += "Terminated processes:\n- " + "\n- ".join(killed)
            else:
                msg += "No active Claude process was running."
            messagebox.showwarning("Kill Switch Alert", msg)

        self.after(0, show_alert)

    # ==================== ACTIONS ====================

    def _initial_ip_check(self):
        info = self.engine.refresh_ip()
        blocked = self.config_data.get("blocked_countries", ["RU", "BY"])
        if info.ip and info.country_code not in blocked:
            self.engine.arm()

    def _toggle_arm(self):
        if self.engine.state == KillSwitchEngine.STATE_ARMED:
            self.engine.disarm()
        elif self.engine.state == KillSwitchEngine.STATE_TRIGGERED:
            self.engine.reset_trigger()
            self.engine.arm()
        else:
            success = self.engine.arm()
            if not success:
                messagebox.showerror(
                    "Activation Denied",
                    "Unable to arm protection.\nEnsure your VPN is active and external IP is outside restricted regions."
                )

    def _launch_claude(self):
        success, msg = self.engine.launch_claude_safely()
        if success:
            self.engine.log(msg, "SUCCESS")
        else:
            messagebox.showerror("Safe Launch Denied", f"Launch aborted for safety:\n{msg}")

    def _panic_kill(self):
        killed = self.engine.kill_claude_processes("Manual panic trigger by user")
        self.engine.log(f"Manual panic execution finished. Closed {len(killed)} processes.", "INFO")

    def _update_settings(self):
        self.config_data["strict_mode"] = bool(self.switch_strict.get())
        self.config_data["sound_alarm"] = bool(self.switch_sound.get())
        self.config_data["auto_guard"] = bool(self.switch_autoguard.get())
        self.engine.config = self.config_data
        save_config(self.config_data)

    def _clear_log(self):
        self.log_textbox.delete("1.0", "end")

    def _on_close(self):
        self.engine.stop()
        self.destroy()


def run_gui():
    app = ClaudeKillSwitchGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
