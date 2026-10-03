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

# Set global appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ClaudeKillSwitchGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🛡️ Claude Kill Switch — Anti-Leak Protection")
        self.geometry("780x720")
        self.minsize(720, 640)

        # Set window icon
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

        # Auto-arm on startup if user connected via VPN (non-RU IP)
        self.after(800, self._initial_ip_check)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Log area expands

        # ==================== 1. HEADER ====================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="CLAUDE KILL SWITCH",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#38BDF8"
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Мгновенное завершение Claude при смене IP, падении VPN или риске утечки",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#94A3B8"
        )
        subtitle_label.grid(row=1, column=0, sticky="w")

        # ==================== 2. STATUS CARD ====================
        self.status_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=2, border_color="#334155")
        self.status_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.status_card.grid_columnconfigure((0, 1), weight=1)

        # Left side: Big Status Badge
        badge_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        badge_frame.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")

        self.status_badge_icon = ctk.CTkLabel(
            badge_frame,
            text="⏸️",
            font=ctk.CTkFont(size=36)
        )
        self.status_badge_icon.pack(anchor="w")

        self.status_title_label = ctk.CTkLabel(
            badge_frame,
            text="РЕЖИМ ОЖИДАНИЯ",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#F59E0B"
        )
        self.status_title_label.pack(anchor="w", pady=(2, 0))

        self.status_desc_label = ctk.CTkLabel(
            badge_frame,
            text="Защита не включена. Нажмите «Включить защиту» для блокировки текущего IP.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94A3B8",
            wraplength=320,
            justify="left"
        )
        self.status_desc_label.pack(anchor="w", pady=(4, 0))

        # Right side: IP & Geo Details
        info_frame = ctk.CTkFrame(self.status_card, fg_color="#0F172A", corner_radius=8)
        info_frame.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_frame, text="Текущий IP:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
        self.lbl_current_ip = ctk.CTkLabel(info_frame, text="Определение...", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color="#38BDF8")
        self.lbl_current_ip.grid(row=0, column=1, padx=10, pady=(8, 2), sticky="w")

        ctk.CTkLabel(info_frame, text="Локация:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").grid(row=1, column=0, padx=10, pady=2, sticky="w")
        self.lbl_location = ctk.CTkLabel(info_frame, text="...", font=ctk.CTkFont(size=12), text_color="#F1F5F9")
        self.lbl_location.grid(row=1, column=1, padx=10, pady=2, sticky="w")

        ctk.CTkLabel(info_frame, text="Провайдер:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").grid(row=2, column=0, padx=10, pady=2, sticky="w")
        self.lbl_isp = ctk.CTkLabel(info_frame, text="...", font=ctk.CTkFont(size=11), text_color="#94A3B8")
        self.lbl_isp.grid(row=2, column=1, padx=10, pady=2, sticky="w")

        ctk.CTkLabel(info_frame, text="Закреплённый IP:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").grid(row=3, column=0, padx=10, pady=(2, 8), sticky="w")
        self.lbl_locked_ip = ctk.CTkLabel(info_frame, text="Не зафиксирован", font=ctk.CTkFont(family="Consolas", size=12), text_color="#CBD5E1")
        self.lbl_locked_ip.grid(row=3, column=1, padx=10, pady=(2, 8), sticky="w")

        # ==================== 3. CONTROL BUTTONS & SETTINGS ====================
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        ctrl_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_arm_toggle = ctk.CTkButton(
            ctrl_frame,
            text="🛡️ Включить защиту",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=42,
            command=self._toggle_arm
        )
        self.btn_arm_toggle.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_launch_claude = ctk.CTkButton(
            ctrl_frame,
            text="🚀 Запустить Claude",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=42,
            command=self._launch_claude
        )
        self.btn_launch_claude.grid(row=0, column=1, padx=6, sticky="ew")

        self.btn_panic_kill = ctk.CTkButton(
            ctrl_frame,
            text="⚡ Закрыть Claude",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            height=42,
            command=self._panic_kill
        )
        self.btn_panic_kill.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        # Settings options row
        settings_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E293B")
        settings_frame.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.switch_strict = ctk.CTkSwitch(
            settings_frame,
            text="Убивать при обрыве сети",
            font=ctk.CTkFont(size=12),
            command=self._update_settings
        )
        self.switch_strict.grid(row=0, column=0, padx=12, pady=10, sticky="w")
        if self.config_data.get("strict_mode", True):
            self.switch_strict.select()

        self.switch_sound = ctk.CTkSwitch(
            settings_frame,
            text="Звук тревоги",
            font=ctk.CTkFont(size=12),
            command=self._update_settings
        )
        self.switch_sound.grid(row=0, column=1, padx=12, pady=10, sticky="w")
        if self.config_data.get("sound_alarm", True):
            self.switch_sound.select()

        self.switch_autoguard = ctk.CTkSwitch(
            settings_frame,
            text="Блок на RU-IP",
            font=ctk.CTkFont(size=12),
            command=self._update_settings
        )
        self.switch_autoguard.grid(row=0, column=2, padx=12, pady=10, sticky="w")
        if self.config_data.get("auto_guard", True):
            self.switch_autoguard.select()

        # ==================== 4. LIVE EVENT LOG ====================
        log_container = ctk.CTkFrame(self, corner_radius=10, fg_color="#0F172A")
        log_container.grid(row=4, column=0, padx=20, pady=(5, 15), sticky="nsew")
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        log_header = ctk.CTkFrame(log_container, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        lbl_log = ctk.CTkLabel(
            log_header,
            text="Журнал событий реального времени",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94A3B8"
        )
        lbl_log.grid(row=0, column=0, sticky="w")

        btn_clear_log = ctk.CTkButton(
            log_header,
            text="Очистить",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_log
        )
        btn_clear_log.grid(row=0, column=1, sticky="e")

        self.log_textbox = ctk.CTkTextbox(
            log_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#020617",
            text_color="#E2E8F0",
            wrap="word"
        )
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    # ==================== LOG & STATUS CALLBACKS ====================

    def _handle_log(self, message: str, level: str):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }.get(level, "•")

        line = f"[{now_str}] {prefix} {message}\n"

        def append():
            self.log_textbox.insert("end", line)
            self.log_textbox.see("end")

        self.after(0, append)

    def _handle_status_change(self, state: str, message: str):
        def update():
            if state == KillSwitchEngine.STATE_ARMED:
                self.status_card.configure(border_color="#10B981")
                self.status_badge_icon.configure(text="🛡️")
                self.status_title_label.configure(text="ЗАЩИТА АКТИВНА", text_color="#10B981")
                self.status_desc_label.configure(
                    text="IP заблокирован. При смене IP, потере VPN или утечке все процессы Claude будут мгновенно уничтожены."
                )
                self.btn_arm_toggle.configure(
                    text="⏸️ Отключить защиту",
                    fg_color="#475569",
                    hover_color="#334155"
                )
                if self.engine.locked_ip:
                    self.lbl_locked_ip.configure(
                        text=f"{self.engine.locked_ip} [{self.engine.locked_country_code}]",
                        text_color="#10B981"
                    )

            elif state == KillSwitchEngine.STATE_TRIGGERED:
                self.status_card.configure(border_color="#EF4444")
                self.status_badge_icon.configure(text="🚨")
                self.status_title_label.configure(text="СРАБОТАЛА ТРЕВОГА!", text_color="#EF4444")
                self.status_desc_label.configure(
                    text=f"ВНИМАНИЕ! Claude был принудительно закрыт. Причина: {message}"
                )
                self.btn_arm_toggle.configure(
                    text="🔄 Сброс и повторная защита",
                    fg_color="#EF4444",
                    hover_color="#DC2626"
                )

            else:  # DISARMED
                self.status_card.configure(border_color="#334155")
                self.status_badge_icon.configure(text="⏸️")
                self.status_title_label.configure(text="РЕЖИМ ОЖИДАНИЯ", text_color="#F59E0B")
                self.status_desc_label.configure(
                    text="Защита не активна. Claude не защищён от падения VPN."
                )
                self.btn_arm_toggle.configure(
                    text="🛡️ Включить защиту",
                    fg_color="#10B981",
                    hover_color="#059669"
                )
                self.lbl_locked_ip.configure(text="Не зафиксирован", text_color="#CBD5E1")

        self.after(0, update)

    def _handle_ip_update(self, info: IPInfo):
        def update():
            if info.ip:
                self.lbl_current_ip.configure(text=f"{info.ip} ({info.latency_ms:.0f} ms)")
                loc_text = f"{info.country_code} - {info.country}, {info.city}" if info.country else "Определяется..."
                self.lbl_location.configure(text=loc_text)
                self.lbl_isp.configure(text=info.isp or "Неизвестно")
            elif info.error:
                self.lbl_current_ip.configure(text="Ошибка связи!", text_color="#EF4444")
                self.lbl_location.configure(text=info.error)

        self.after(0, update)

    def _handle_kill_event(self, reason: str, killed: list):
        def show_alert():
            msg = f"СРАБОТАЛ KILL SWITCH!\n\nПричина: {reason}\n\n"
            if killed:
                msg += f"Закрытые процессы:\n- " + "\n- ".join(killed)
            else:
                msg += "Claude не был запущен."
            messagebox.showwarning("🚨 Claude Kill Switch Triggered", msg)

        self.after(0, show_alert)

    # ==================== ACTIONS ====================

    def _initial_ip_check(self):
        info = self.engine.refresh_ip()
        blocked = self.config_data.get("blocked_countries", ["RU", "BY"])
        # If already on safe VPN, offer to arm or auto-arm
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
                    "Ошибка активации",
                    "Не удалось активировать защиту!\nУбедитесь, что VPN включен и ваш текущий IP не принадлежит России."
                )

    def _launch_claude(self):
        success, msg = self.engine.launch_claude_safely()
        if success:
            self.engine.log(f"🚀 {msg}", "SUCCESS")
        else:
            messagebox.showerror("Безопасный запуск Claude", f"Запуск заблокирован:\n{msg}")

    def _panic_kill(self):
        killed = self.engine.kill_claude_processes("Ручное экстренное закрытие пользователем")
        self.engine.log(f"Ручное закрытие завершено. Закрыто: {len(killed)} процессов.", "INFO")

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
