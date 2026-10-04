import os
import sys
import time
import datetime
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog

import customtkinter as ctk

from config import load_config, save_config, get_claude_executable_path
from engine import KillSwitchEngine, IPInfo

# Translations Dictionary
I18N = {
    "ru": {
        "title": "CLAUDE KILL SWITCH",
        "subtitle": "СИСТЕМА ЗАЩИТЫ ОТ УТЕЧКИ СЕТИ • АВТОР: XONIKSQ",
        "status_standby": "ОЖИДАНИЕ",
        "status_standby_desc": "Защита отключена. Нажмите «ВКЛЮЧИТЬ ЗАЩИТУ», чтобы зафиксировать текущий VPN IP.",
        "status_armed": "ЗАЩИТА АКТИВНА",
        "status_armed_desc": "IP-соединение зафиксировано. При любой смене IP или отключении VPN все процессы Claude будут мгновенно закрыты.",
        "status_triggered": "ТРЕВОГА: CLAUDE ЗАКРЫТ",
        "status_triggered_desc": "Внимание: Claude был принудительно закрыт. Причина: {}",
        "btn_arm": "ВКЛЮЧИТЬ ЗАЩИТУ",
        "btn_disarm": "ОТКЛЮЧИТЬ ЗАЩИТУ",
        "btn_reset": "СБРОСИТЬ ТРЕВОГУ",
        "btn_launch": "ЗАПУСТИТЬ CLAUDE",
        "btn_panic": "ЭКСТРЕННО ЗАКРЫТЬ",
        "lbl_cur_ip": "ТЕКУЩИЙ IP",
        "lbl_location": "ЛОКАЦИЯ",
        "lbl_isp": "ПРОВАЙДЕР / СЕТЬ",
        "lbl_locked_ip": "ЗАФИКСИРОВАННЫЙ IP",
        "unlocked": "НЕ ЗАФИКСИРОВАН",
        "detecting": "Определение...",
        "resolving": "Определяется...",
        "switch_strict": "Убивать при обрыве сети",
        "switch_sound": "Звук ошибки Windows",
        "switch_autoguard": "Блок на RU IP",
        "log_title": "СИСТЕМНЫЙ ЛОГ",
        "btn_clear": "ОЧИСТИТЬ",
        "alert_title": "Внимание Kill Switch",
        "alert_term": "Закрытые процессы:",
        "alert_none": "Claude не был запущен.",
        "denied_title": "Отказ активации",
        "denied_msg": "Не удалось включить защиту.\nУбедитесь, что VPN включен и IP не принадлежит России.",
        "launch_denied_title": "Безопасный запуск отклонён",
        "launch_denied_msg": "Запуск отменён в целях безопасности:\n{}",
        "claude_not_found_title": "Claude Desktop не найден",
        "claude_not_found_desc": "Официальное приложение Claude Desktop не найдено на этом компьютере.\n\n• Если Claude установлен в другую папку — укажите путь к claude.exe вручную.\n• Если Claude ещё не установлен — скачайте его с официального сайта claude.ai.",
        "btn_browse_claude": "УКАЗАТЬ CLAUDE.EXE",
        "btn_download_claude": "СКАЧАТЬ С CLAUDE.AI",
        "btn_close": "ЗАКРЫТЬ",
        "path_saved_title": "Путь сохранён",
        "path_saved_msg": "Исполняемый файл Claude успешно сохранён:\n{}",
        "lang_name": "RU",
        "theme_dark": "ТЕМНАЯ",
        "theme_light": "СВЕТЛАЯ"
    },
    "en": {
        "title": "CLAUDE KILL SWITCH",
        "subtitle": "HARDWARE-LEVEL ANTI-LEAK NETWORK MONITOR • BY XONIKSQ",
        "status_standby": "STANDBY",
        "status_standby_desc": "Protection disarmed. Click 'ENABLE PROTECTION' to lock your current VPN connection.",
        "status_armed": "ARMED & PROTECTED",
        "status_armed_desc": "Network connection locked. Instant process termination will trigger upon any IP variation or adapter drop.",
        "status_triggered": "SYSTEM TRIGGERED",
        "status_triggered_desc": "Critical: Claude was forcefully terminated. Trigger reason: {}",
        "btn_arm": "ENABLE PROTECTION",
        "btn_disarm": "DISABLE PROTECTION",
        "btn_reset": "RESET ALARM",
        "btn_launch": "LAUNCH CLAUDE",
        "btn_panic": "PANIC KILL",
        "lbl_cur_ip": "CURRENT IP",
        "lbl_location": "LOCATION",
        "lbl_isp": "NETWORK / ISP",
        "lbl_locked_ip": "LOCKED IP",
        "unlocked": "UNLOCKED",
        "detecting": "Detecting...",
        "resolving": "Resolving...",
        "switch_strict": "Kill on network loss",
        "switch_sound": "Windows error sound",
        "switch_autoguard": "Block on RU IP",
        "log_title": "SYSTEM CONSOLE LOG",
        "btn_clear": "CLEAR",
        "alert_title": "Kill Switch Alert",
        "alert_term": "Terminated processes:",
        "alert_none": "No active Claude process was running.",
        "denied_title": "Activation Denied",
        "denied_msg": "Unable to arm protection.\nEnsure your VPN is active and external IP is outside restricted regions.",
        "launch_denied_title": "Safe Launch Denied",
        "launch_denied_msg": "Launch aborted for safety:\n{}",
        "claude_not_found_title": "Claude Desktop Not Found",
        "claude_not_found_desc": "Claude Desktop executable was not found on this system.\n\n• If Claude is installed in a custom location, locate claude.exe manually.\n• If Claude is not installed yet, download it from the official website.",
        "btn_browse_claude": "LOCATE CLAUDE.EXE",
        "btn_download_claude": "DOWNLOAD FROM CLAUDE.AI",
        "btn_close": "CLOSE",
        "path_saved_title": "Path Saved",
        "path_saved_msg": "Claude executable path updated:\n{}",
        "lang_name": "EN",
        "theme_dark": "DARK",
        "theme_light": "LIGHT"
    }
}


class ClaudeKillSwitchGUI(ctk.CTk):
    # Dynamic Chrome Palette (tuple: Light mode, Dark mode)
    C_ROOT = ("#ECECF1", "#09090B")
    C_CARD = ("#FFFFFF", "#121214")
    C_INNER = ("#F4F4F6", "#050505")
    C_BORDER = ("#D4D4D8", "#27272A")
    C_BORDER_ACTIVE = ("#18181B", "#E4E4E7")
    C_BORDER_ALERT = "#EF4444"

    C_TEXT_MAIN = ("#09090B", "#FFFFFF")
    C_TEXT_MUTED = ("#52525B", "#A1A1AA")
    C_TEXT_DIM = ("#71717A", "#52525B")
    C_TEXT_MONO = ("#18181B", "#E4E4E7")

    def __init__(self):
        super().__init__()

        # Config & Engine
        self.config_data = load_config()
        self.lang = self.config_data.get("language", "ru")
        self.theme_mode = self.config_data.get("theme", "dark")

        ctk.set_appearance_mode(self.theme_mode.capitalize())
        ctk.set_default_color_theme("dark-blue")

        self.title("Claude Kill Switch")
        self.geometry("780x750")
        self.minsize(720, 680)
        self.configure(fg_color=self.C_ROOT)

        # Set window icon if exists
        icon_file = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_file):
            try:
                self.iconbitmap(icon_file)
            except Exception:
                pass

        self.engine = KillSwitchEngine(self.config_data)

        # Setup engine callbacks
        self.engine.on_log = self._handle_log
        self.engine.on_status_change = self._handle_status_change
        self.engine.on_ip_update = self._handle_ip_update
        self.engine.on_kill = self._handle_kill_event

        self._build_ui()
        self._apply_texts()

        # Start engine
        self.engine.start()

        # Initial check
        self.after(600, self._initial_ip_check)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def t(self, key: str) -> str:
        """Returns translated text for current language."""
        return I18N.get(self.lang, I18N["ru"]).get(key, key)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # Log expands

        # ==================== 1. TOP HEADER ====================
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        self.lbl_main_title = ctk.CTkLabel(
            title_row,
            text=self.t("title"),
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.C_TEXT_MAIN
        )
        self.lbl_main_title.pack(side="left")

        # Top-Right Controls: Theme & Language Toggle Buttons
        controls_group = ctk.CTkFrame(title_row, fg_color="transparent")
        controls_group.pack(side="right")

        # Language button
        self.btn_lang = ctk.CTkButton(
            controls_group,
            text="🌐 " + self.t("lang_name"),
            width=64,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.C_CARD,
            hover_color=("#E4E4E7", "#27272A"),
            border_width=1,
            border_color=self.C_BORDER,
            text_color=self.C_TEXT_MAIN,
            corner_radius=6,
            command=self._toggle_language
        )
        self.btn_lang.pack(side="left", padx=(0, 6))

        # Theme button
        theme_icon = "☀️" if self.theme_mode == "light" else "🌙"
        theme_label = self.t("theme_light") if self.theme_mode == "light" else self.t("theme_dark")
        self.btn_theme = ctk.CTkButton(
            controls_group,
            text=f"{theme_icon} {theme_label}",
            width=84,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.C_CARD,
            hover_color=("#E4E4E7", "#27272A"),
            border_width=1,
            border_color=self.C_BORDER,
            text_color=self.C_TEXT_MAIN,
            corner_radius=6,
            command=self._toggle_theme
        )
        self.btn_theme.pack(side="left")

        self.lbl_subtitle = ctk.CTkLabel(
            header,
            text=self.t("subtitle"),
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=self.C_TEXT_DIM
        )
        self.lbl_subtitle.pack(anchor="w", pady=(3, 0))

        # ==================== 2. STATUS CARD ====================
        self.status_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=self.C_CARD,
            border_width=1,
            border_color=self.C_BORDER
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
            text_color=self.C_TEXT_DIM
        )
        self.status_dot.pack(anchor="w")

        self.status_title = ctk.CTkLabel(
            badge_frame,
            text=self.t("status_standby"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.C_TEXT_MAIN
        )
        self.status_title.pack(anchor="w", pady=(2, 0))

        self.status_desc = ctk.CTkLabel(
            badge_frame,
            text=self.t("status_standby_desc"),
            font=ctk.CTkFont(size=12),
            text_color=self.C_TEXT_MUTED,
            wraplength=320,
            justify="left"
        )
        self.status_desc.pack(anchor="w", pady=(6, 0))

        # Right Column: Network Data Grid
        info_frame = ctk.CTkFrame(
            self.status_card,
            fg_color=self.C_INNER,
            corner_radius=8,
            border_width=1,
            border_color=self.C_BORDER
        )
        info_frame.grid(row=0, column=1, padx=20, pady=16, sticky="nsew")
        info_frame.grid_columnconfigure(1, weight=1)

        # Labels for network fields
        self.lbl_tag_cur_ip = ctk.CTkLabel(info_frame, text=self.t("lbl_cur_ip"), font=ctk.CTkFont(family="Consolas", size=11), text_color=self.C_TEXT_DIM)
        self.lbl_tag_cur_ip.grid(row=0, column=0, padx=12, pady=5, sticky="w")
        self.lbl_current_ip = ctk.CTkLabel(info_frame, text=self.t("detecting"), font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color=self.C_TEXT_MAIN)
        self.lbl_current_ip.grid(row=0, column=1, padx=12, pady=5, sticky="w")

        self.lbl_tag_loc = ctk.CTkLabel(info_frame, text=self.t("lbl_location"), font=ctk.CTkFont(family="Consolas", size=11), text_color=self.C_TEXT_DIM)
        self.lbl_tag_loc.grid(row=1, column=0, padx=12, pady=5, sticky="w")
        self.lbl_location = ctk.CTkLabel(info_frame, text="...", font=ctk.CTkFont(size=11), text_color=self.C_TEXT_MUTED)
        self.lbl_location.grid(row=1, column=1, padx=12, pady=5, sticky="w")

        self.lbl_tag_isp = ctk.CTkLabel(info_frame, text=self.t("lbl_isp"), font=ctk.CTkFont(family="Consolas", size=11), text_color=self.C_TEXT_DIM)
        self.lbl_tag_isp.grid(row=2, column=0, padx=12, pady=5, sticky="w")
        self.lbl_isp = ctk.CTkLabel(info_frame, text="...", font=ctk.CTkFont(size=11), text_color=self.C_TEXT_MUTED)
        self.lbl_isp.grid(row=2, column=1, padx=12, pady=5, sticky="w")

        self.lbl_tag_locked = ctk.CTkLabel(info_frame, text=self.t("lbl_locked_ip"), font=ctk.CTkFont(family="Consolas", size=11), text_color=self.C_TEXT_DIM)
        self.lbl_tag_locked.grid(row=3, column=0, padx=12, pady=5, sticky="w")
        self.lbl_locked_ip = ctk.CTkLabel(info_frame, text=self.t("unlocked"), font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=self.C_TEXT_DIM)
        self.lbl_locked_ip.grid(row=3, column=1, padx=12, pady=5, sticky="w")

        # ==================== 3. ACTION CONTROLS ====================
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, padx=24, pady=8, sticky="ew")
        ctrl_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Primary Toggle Button
        self.btn_arm_toggle = ctk.CTkButton(
            ctrl_frame,
            text=self.t("btn_arm"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#18181B", "#FFFFFF"),
            hover_color=("#27272A", "#E4E4E7"),
            text_color=("#FFFFFF", "#000000"),
            corner_radius=8,
            height=44,
            command=self._toggle_arm
        )
        self.btn_arm_toggle.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        # Launch Claude Button Container
        launch_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        launch_frame.grid(row=0, column=1, padx=6, sticky="ew")
        launch_frame.grid_columnconfigure(0, weight=1)

        self.btn_launch_claude = ctk.CTkButton(
            launch_frame,
            text=self.t("btn_launch"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=self.C_CARD,
            hover_color=("#E4E4E7", "#27272A"),
            border_width=1,
            border_color=self.C_BORDER,
            text_color=self.C_TEXT_MAIN,
            corner_radius=8,
            height=44,
            command=self._launch_claude
        )
        self.btn_launch_claude.grid(row=0, column=0, sticky="ew")

        self.btn_browse_claude = ctk.CTkButton(
            launch_frame,
            text="📁",
            font=ctk.CTkFont(size=14),
            fg_color=self.C_CARD,
            hover_color=("#E4E4E7", "#27272A"),
            border_width=1,
            border_color=self.C_BORDER,
            text_color=self.C_TEXT_MAIN,
            corner_radius=8,
            width=38,
            height=44,
            command=self._choose_claude_path
        )
        self.btn_browse_claude.grid(row=0, column=1, padx=(6, 0), sticky="e")

        # Panic Kill Button
        self.btn_panic_kill = ctk.CTkButton(
            ctrl_frame,
            text=self.t("btn_panic"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=self.C_CARD,
            hover_color=("#FEE2E2", "#2D1518"),
            border_width=1,
            border_color=("#FCA5A5", "#7F1D1D"),
            text_color=("#DC2626", "#F87171"),
            corner_radius=8,
            height=44,
            command=self._panic_kill
        )
        self.btn_panic_kill.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        # ==================== 4. SETTINGS STRIP ====================
        settings_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=self.C_CARD,
            border_width=1,
            border_color=self.C_BORDER
        )
        settings_frame.grid(row=3, column=0, padx=24, pady=6, sticky="ew")
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)

        switch_args = {
            "font": ctk.CTkFont(size=12),
            "text_color": self.C_TEXT_MUTED,
            "progress_color": ("#18181B", "#FFFFFF"),
            "button_color": ("#FFFFFF", "#E4E4E7"),
            "button_hover_color": ("#E4E4E7", "#FFFFFF"),
            "command": self._update_settings
        }

        self.switch_strict = ctk.CTkSwitch(settings_frame, text=self.t("switch_strict"), **switch_args)
        self.switch_strict.grid(row=0, column=0, padx=16, pady=12, sticky="w")
        if self.config_data.get("strict_mode", True):
            self.switch_strict.select()

        self.switch_sound = ctk.CTkSwitch(settings_frame, text=self.t("switch_sound"), **switch_args)
        self.switch_sound.grid(row=0, column=1, padx=16, pady=12, sticky="w")
        if self.config_data.get("sound_alarm", True):
            self.switch_sound.select()

        self.switch_autoguard = ctk.CTkSwitch(settings_frame, text=self.t("switch_autoguard"), **switch_args)
        self.switch_autoguard.grid(row=0, column=2, padx=16, pady=12, sticky="w")
        if self.config_data.get("auto_guard", True):
            self.switch_autoguard.select()

        # ==================== 5. CHROME TERMINAL LOG ====================
        log_container = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=self.C_CARD,
            border_width=1,
            border_color=self.C_BORDER
        )
        log_container.grid(row=4, column=0, padx=24, pady=(6, 20), sticky="nsew")
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_container, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        self.lbl_log_title = ctk.CTkLabel(
            log_header,
            text=self.t("log_title"),
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=self.C_TEXT_DIM
        )
        self.lbl_log_title.grid(row=0, column=0, sticky="w")

        self.btn_clear_log = ctk.CTkButton(
            log_header,
            text=self.t("btn_clear"),
            width=58,
            height=22,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=self.C_INNER,
            hover_color=("#E4E4E7", "#27272A"),
            border_width=1,
            border_color=self.C_BORDER,
            text_color=self.C_TEXT_MUTED,
            command=self._clear_log
        )
        self.btn_clear_log.grid(row=0, column=1, sticky="e")

        self.log_textbox = ctk.CTkTextbox(
            log_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=self.C_INNER,
            text_color=self.C_TEXT_MONO,
            border_width=1,
            border_color=self.C_BORDER,
            wrap="word"
        )
        self.log_textbox.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

    # ==================== LANGUAGE & THEME TOGGLES ====================

    def _toggle_language(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.config_data["language"] = self.lang
        save_config(self.config_data)
        self._apply_texts()

    def _toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.config_data["theme"] = self.theme_mode
        save_config(self.config_data)

        ctk.set_appearance_mode(self.theme_mode.capitalize())
        theme_icon = "☀️" if self.theme_mode == "light" else "🌙"
        theme_label = self.t("theme_light") if self.theme_mode == "light" else self.t("theme_dark")
        self.btn_theme.configure(text=f"{theme_icon} {theme_label}")

    def _apply_texts(self):
        """Refreshes all texts across the UI according to current language."""
        self.lbl_main_title.configure(text=self.t("title"))
        self.lbl_subtitle.configure(text=self.t("subtitle"))

        self.btn_lang.configure(text="🌐 " + self.t("lang_name"))
        theme_icon = "☀️" if self.theme_mode == "light" else "🌙"
        theme_label = self.t("theme_light") if self.theme_mode == "light" else self.t("theme_dark")
        self.btn_theme.configure(text=f"{theme_icon} {theme_label}")

        self.lbl_tag_cur_ip.configure(text=self.t("lbl_cur_ip"))
        self.lbl_tag_loc.configure(text=self.t("lbl_location"))
        self.lbl_tag_isp.configure(text=self.t("lbl_isp"))
        self.lbl_tag_locked.configure(text=self.t("lbl_locked_ip"))

        self.btn_launch_claude.configure(text=self.t("btn_launch"))
        self.btn_panic_kill.configure(text=self.t("btn_panic"))

        self.switch_strict.configure(text=self.t("switch_strict"))
        self.switch_sound.configure(text=self.t("switch_sound"))
        self.switch_autoguard.configure(text=self.t("switch_autoguard"))

        self.lbl_log_title.configure(text=self.t("log_title"))
        self.btn_clear_log.configure(text=self.t("btn_clear"))

        # Re-trigger status styling according to engine state
        self._update_status_ui()

    def _update_status_ui(self):
        state = self.engine.state
        if state == KillSwitchEngine.STATE_ARMED:
            self.status_card.configure(border_color=self.C_BORDER_ACTIVE)
            self.status_dot.configure(text="●", text_color=("#18181B", "#FFFFFF"))
            self.status_title.configure(text=self.t("status_armed"), text_color=self.C_TEXT_MAIN)
            self.status_desc.configure(text=self.t("status_armed_desc"))
            self.btn_arm_toggle.configure(
                text=self.t("btn_disarm"),
                fg_color=self.C_CARD,
                hover_color=("#E4E4E7", "#27272A"),
                border_width=1,
                border_color=self.C_BORDER,
                text_color=self.C_TEXT_MAIN
            )
            if self.engine.locked_ip:
                self.lbl_locked_ip.configure(
                    text=f"{self.engine.locked_ip} [{self.engine.locked_country_code}]",
                    text_color=self.C_TEXT_MAIN
                )
        elif state == KillSwitchEngine.STATE_TRIGGERED:
            self.status_card.configure(border_color=self.C_BORDER_ALERT)
            self.status_dot.configure(text="▲", text_color=self.C_BORDER_ALERT)
            self.status_title.configure(text=self.t("status_triggered"), text_color=self.C_BORDER_ALERT)
            self.btn_arm_toggle.configure(
                text=self.t("btn_reset"),
                fg_color=("#FEE2E2", "#7F1D1D"),
                hover_color=("#FECACA", "#991B1B"),
                border_width=1,
                border_color=self.C_BORDER_ALERT,
                text_color=("#DC2626", "#FFFFFF")
            )
        else:  # DISARMED
            self.status_card.configure(border_color=self.C_BORDER)
            self.status_dot.configure(text="○", text_color=self.C_TEXT_DIM)
            self.status_title.configure(text=self.t("status_standby"), text_color=self.C_TEXT_MAIN)
            self.status_desc.configure(text=self.t("status_standby_desc"))
            self.btn_arm_toggle.configure(
                text=self.t("btn_arm"),
                fg_color=("#18181B", "#FFFFFF"),
                hover_color=("#27272A", "#E4E4E7"),
                border_width=0,
                text_color=("#FFFFFF", "#000000")
            )
            self.lbl_locked_ip.configure(text=self.t("unlocked"), text_color=self.C_TEXT_DIM)

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
            self._update_status_ui()
            if state == KillSwitchEngine.STATE_TRIGGERED:
                desc_text = self.t("status_triggered_desc").format(message)
                self.status_desc.configure(text=desc_text)

        self.after(0, update)

    def _handle_ip_update(self, info: IPInfo):
        def update():
            if info.ip:
                self.lbl_current_ip.configure(
                    text=f"{info.ip}  ({info.latency_ms:.0f}ms)",
                    text_color=self.C_TEXT_MAIN
                )
                loc_text = f"{info.country_code} — {info.country}, {info.city}" if info.country else self.t("resolving")
                self.lbl_location.configure(text=loc_text)
                self.lbl_isp.configure(text=info.isp or "Unknown Network")
            elif info.error:
                self.lbl_current_ip.configure(text="OFFLINE", text_color=self.C_BORDER_ALERT)
                self.lbl_location.configure(text=info.error)

        self.after(0, update)

    def _handle_kill_event(self, reason: str, killed: list):
        def show_alert():
            msg = f"{self.t('alert_title')}\n\n{reason}\n\n"
            if killed:
                msg += f"{self.t('alert_term')}\n- " + "\n- ".join(killed)
            else:
                msg += self.t("alert_none")
            messagebox.showwarning(self.t("alert_title"), msg)

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
                messagebox.showerror(self.t("denied_title"), self.t("denied_msg"))

    def _choose_claude_path(self):
        initial_dir = os.environ.get("LOCALAPPDATA", "C:\\")
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Выберите claude.exe",
            initialdir=initial_dir,
            filetypes=[("Claude Executable", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.config_data["claude_path"] = file_path
            self.engine.config["claude_path"] = file_path
            save_config(self.config_data)
            self.engine.log(f"Настроен путь к Claude: {file_path}", "SUCCESS")
            messagebox.showinfo(self.t("path_saved_title"), self.t("path_saved_msg").format(file_path))
            return file_path
        return None

    def _show_claude_not_found_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.t("claude_not_found_title"))
        dialog.geometry("520x290")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center relative to parent
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 520) // 2
        y = self.winfo_y() + (self.winfo_height() - 290) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        dialog.configure(fg_color=self.C_ROOT)

        card = ctk.CTkFrame(
            dialog,
            fg_color=self.C_CARD,
            border_width=1,
            border_color=self.C_BORDER,
            corner_radius=10
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)

        title_lbl = ctk.CTkLabel(
            card,
            text=f"⚠️  {self.t('claude_not_found_title')}",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.C_TEXT_MAIN
        )
        title_lbl.pack(anchor="w", padx=20, pady=(18, 8))

        desc_lbl = ctk.CTkLabel(
            card,
            text=self.t("claude_not_found_desc"),
            font=ctk.CTkFont(size=12),
            text_color=self.C_TEXT_MUTED,
            justify="left",
            wraplength=440
        )
        desc_lbl.pack(anchor="w", padx=20, pady=(0, 16))

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16), side="bottom")

        def on_locate():
            dialog.destroy()
            chosen = self._choose_claude_path()
            if chosen:
                self._launch_claude()

        def on_download():
            dialog.destroy()
            webbrowser.open("https://claude.ai/download")

        def on_cancel():
            dialog.destroy()

        btn_locate = ctk.CTkButton(
            btn_box,
            text=self.t("btn_browse_claude"),
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#18181B", "#FFFFFF"),
            hover_color=("#27272A", "#E4E4E7"),
            text_color=("#FFFFFF", "#000000"),
            height=36,
            command=on_locate
        )
        btn_locate.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_dl = ctk.CTkButton(
            btn_box,
            text=self.t("btn_download_claude"),
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=self.C_CARD,
            border_width=1,
            border_color=self.C_BORDER,
            hover_color=("#E4E4E7", "#27272A"),
            text_color=self.C_TEXT_MAIN,
            height=36,
            command=on_download
        )
        btn_dl.pack(side="left", fill="x", expand=True, padx=6)

        btn_cancel = ctk.CTkButton(
            btn_box,
            text=self.t("btn_close"),
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("#E4E4E7", "#27272A"),
            text_color=self.C_TEXT_MUTED,
            width=60,
            height=36,
            command=on_cancel
        )
        btn_cancel.pack(side="right", padx=(6, 0))

    def _launch_claude(self):
        success, msg = self.engine.launch_claude_safely()
        if success:
            self.engine.log(msg, "SUCCESS")
        elif msg == "CLAUDE_NOT_FOUND":
            self._show_claude_not_found_dialog()
        else:
            messagebox.showerror(self.t("launch_denied_title"), self.t("launch_denied_msg").format(msg))

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
