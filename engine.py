import os
import sys
import time
import json
import ctypes
import winsound
import subprocess
import threading
from typing import Optional, Dict, Any, Callable, List
from ctypes import wintypes
from dataclasses import dataclass

try:
    import psutil
except ImportError:
    psutil = None

try:
    import httpx
except ImportError:
    httpx = None

import urllib.request

from config import load_config, save_config, get_claude_executable_path


@dataclass
class IPInfo:
    ip: str = ""
    country: str = ""
    country_code: str = ""
    city: str = ""
    isp: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None


class KillSwitchEngine:
    STATE_DISARMED = "DISARMED"
    STATE_ARMED = "ARMED"
    STATE_TRIGGERED = "TRIGGERED"

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self.state = self.STATE_DISARMED

        self.locked_ip: Optional[str] = None
        self.locked_country_code: Optional[str] = None
        self.locked_country_name: Optional[str] = None

        self.current_ip_info: Optional[IPInfo] = None
        self.last_check_time: float = 0.0
        self.consecutive_failures: int = 0
        self.max_allowed_failures: int = 2

        self.is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._network_event_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Callbacks for GUI or CLI integration
        self.on_log: Optional[Callable[[str, str], None]] = None  # (message, level)
        self.on_status_change: Optional[Callable[[str, str], None]] = None  # (state, message)
        self.on_ip_update: Optional[Callable[[IPInfo], None]] = None
        self.on_kill: Optional[Callable[[str, List[str]], None]] = None  # (reason, killed_processes)

        # HTTP client for fast connection reuse
        self._http_client = httpx.Client(timeout=2.0) if httpx else None

    def log(self, message: str, level: str = "INFO"):
        if self.on_log:
            self.on_log(message, level)
        else:
            print(f"[{level}] {message}")

    # ==================== IP RESOLUTION ====================

    def fetch_fast_ip(self) -> tuple[Optional[str], float]:
        """Queries fast external IP services with quick timeout."""
        endpoints = self.config.get("endpoints", [
            "https://icanhazip.com",
            "https://api.ipify.org",
            "https://checkip.amazonaws.com"
        ])

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ClaudeKillSwitch/1.0"}

        for url in endpoints:
            start_t = time.time()
            try:
                if self._http_client:
                    resp = self._http_client.get(url, timeout=1.8)
                    if resp.status_code == 200:
                        ip_text = resp.text.strip()
                        latency = (time.time() - start_t) * 1000
                        if ip_text and len(ip_text) <= 45:  # Valid IPv4 or IPv6 length
                            return ip_text, latency
                else:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=1.8) as response:
                        ip_text = response.read().decode("utf-8").strip()
                        latency = (time.time() - start_t) * 1000
                        if ip_text and len(ip_text) <= 45:
                            return ip_text, latency
            except Exception:
                continue

        return None, 0.0

    def fetch_geo_info(self, ip: str) -> IPInfo:
        """Fetches country, city, and ISP for a given IP."""
        info = IPInfo(ip=ip)
        try:
            # Service 1: ip-api.com
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,city,isp"
            req = urllib.request.Request(url, headers={"User-Agent": "ClaudeKillSwitch/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "success":
                    info.country = data.get("country", "")
                    info.country_code = data.get("countryCode", "").upper()
                    info.city = data.get("city", "")
                    info.isp = data.get("isp", "")
                    return info
        except Exception:
            pass

        try:
            # Fallback service: ipinfo.io
            url = f"https://ipinfo.io/{ip}/json"
            req = urllib.request.Request(url, headers={"User-Agent": "ClaudeKillSwitch/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                info.country_code = data.get("country", "").upper()
                info.country = data.get("country", "")
                info.city = data.get("city", "")
                info.isp = data.get("org", "")
                return info
        except Exception as e:
            info.error = str(e)

        return info

    def refresh_ip(self) -> IPInfo:
        """Full refresh of IP and location."""
        ip, latency = self.fetch_fast_ip()
        if not ip:
            return IPInfo(error="No Internet / IP check timeout", latency_ms=latency)

        geo = self.fetch_geo_info(ip)
        geo.latency_ms = latency
        self.current_ip_info = geo
        return geo

    # ==================== PROCESS KILLING ====================

    def kill_claude_processes(self, reason: str) -> List[str]:
        """Immediately terminates all Claude processes forcefully."""
        killed = []
        my_pid = os.getpid()

        target_names = [name.lower() for name in self.config.get("target_processes", ["claude.exe"])]

        # 1. Fast OS-level taskkill
        for target in ["claude.exe", "claude-code.exe"]:
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", target],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                if res.returncode == 0:
                    killed.append(target)
            except Exception:
                pass

        # 2. psutil deep scan for any lingering sub-processes / helpers
        if psutil:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                    try:
                        p_pid = proc.info['pid']
                        if p_pid == my_pid:
                            continue

                        p_name = (proc.info['name'] or "").lower()
                        p_exe = (proc.info['exe'] or "").lower()
                        p_cmd = " ".join(proc.info['cmdline'] or []).lower()

                        should_kill = False
                        if p_name in target_names:
                            should_kill = True
                        elif "anthropicclaude" in p_exe or ("claude" in p_name and "python" not in p_name):
                            should_kill = True
                        elif "claude-code" in p_cmd and "python" not in p_name:
                            should_kill = True

                        if should_kill:
                            proc.kill()
                            killed.append(f"{proc.info['name']} (PID {p_pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as e:
                self.log(f"psutil scan error: {e}", "WARNING")

        # 3. Sound Alarm
        if self.config.get("sound_alarm", True):
            threading.Thread(target=self._play_alarm_sound, daemon=True).start()

        self.log(f"🚨 KILL SWITCH EXECUTED! Reason: {reason}", "CRITICAL")
        if killed:
            self.log(f"Killed processes: {', '.join(killed)}", "CRITICAL")
        else:
            self.log("Claude was not running or was already closed.", "INFO")

        if self.on_kill:
            self.on_kill(reason, killed)

        return killed

    def _play_alarm_sound(self):
        try:
            for _ in range(3):
                winsound.Beep(1500, 150)
                time.sleep(0.05)
            winsound.Beep(1000, 400)
        except Exception:
            pass

    # ==================== CONTROLS (ARM / DISARM) ====================

    def arm(self) -> bool:
        """Arms the kill switch, locking the current IP and country."""
        self.log("Locking current IP connection...", "INFO")
        info = self.refresh_ip()

        if not info.ip or info.error:
            self.log(f"Cannot arm: unable to determine IP ({info.error})", "ERROR")
            return False

        # Check if country is blocked
        blocked = self.config.get("blocked_countries", ["RU", "BY"])
        if self.config.get("country_block", True) and info.country_code in blocked:
            self.log(
                f"Cannot arm: Current IP is in blocked country {info.country_code} ({info.country})! "
                "Turn on VPN first!",
                "CRITICAL"
            )
            return False

        self.locked_ip = info.ip
        self.locked_country_code = info.country_code
        self.locked_country_name = info.country
        self.consecutive_failures = 0
        self.state = self.STATE_ARMED

        msg = f"Armed! Protected IP: {self.locked_ip} [{self.locked_country_code} - {self.locked_country_name}]"
        self.log(msg, "SUCCESS")

        if self.on_status_change:
            self.on_status_change(self.state, msg)

        if self.on_ip_update:
            self.on_ip_update(info)

        return True

    def disarm(self):
        """Disarms the kill switch."""
        self.state = self.STATE_DISARMED
        self.locked_ip = None
        self.locked_country_code = None
        self.locked_country_name = None
        self.consecutive_failures = 0
        msg = "Kill Switch disarmed (Standby mode)."
        self.log(msg, "INFO")
        if self.on_status_change:
            self.on_status_change(self.state, msg)

    def trigger_kill(self, reason: str):
        """Transitions to TRIGGERED state and terminates Claude."""
        self.state = self.STATE_TRIGGERED
        killed = self.kill_claude_processes(reason)
        if self.on_status_change:
            self.on_status_change(self.state, f"TRIGGERED: {reason}")
        return killed

    def reset_trigger(self):
        """Resets from TRIGGERED state back to DISARMED."""
        self.disarm()

    # ==================== SAFE CLAUDE LAUNCHER ====================

    def launch_claude_safely(self) -> tuple[bool, str]:
        """Launches Claude only if the connection is confirmed safe."""
        # 1. Check current IP
        ip, _ = self.fetch_fast_ip()
        if not ip:
            return False, "Cannot verify IP! Check your VPN/Internet connection."

        geo = self.fetch_geo_info(ip)
        blocked = self.config.get("blocked_countries", ["RU", "BY"])
        if geo.country_code in blocked:
            return False, f"UNSAFE! Detected Russian/Blocked IP ({ip}, {geo.country_code}). Claude will NOT be launched."

        if self.state == self.STATE_ARMED and self.locked_ip and ip != self.locked_ip:
            return False, f"IP mismatch! Current: {ip}, Locked: {self.locked_ip}. Re-arm or check VPN."

        # If not armed, automatically arm it with this verified safe IP
        if self.state != self.STATE_ARMED:
            self.arm()

        claude_exe = get_claude_executable_path()
        if not claude_exe or not os.path.exists(claude_exe):
            return False, "Claude Desktop executable not found on system."

        try:
            subprocess.Popen([claude_exe], shell=False)
            return True, f"Claude Desktop launched safely under VPN ({ip}, {geo.country_code})."
        except Exception as e:
            return False, f"Error launching Claude: {e}"

    # ==================== BACKGROUND MONITORING ====================

    def _check_cycle(self):
        """Single check iteration in the monitoring loop."""
        fast_ip, latency = self.fetch_fast_ip()

        if not fast_ip:
            self.consecutive_failures += 1
            self.log(f"IP check timeout/failed ({self.consecutive_failures}/{self.max_allowed_failures})", "WARNING")

            # In strict mode, kill Claude if connection fails consecutively
            if self.state == self.STATE_ARMED and self.config.get("strict_mode", True):
                if self.consecutive_failures >= self.max_allowed_failures:
                    self.trigger_kill(
                        f"Internet connection lost or VPN dropped! ({self.consecutive_failures} failed checks)"
                    )
            return

        self.consecutive_failures = 0

        # Update IPInfo object
        if self.current_ip_info and self.current_ip_info.ip == fast_ip:
            self.current_ip_info.latency_ms = latency
            info = self.current_ip_info
        else:
            # IP changed or first check
            info = self.fetch_geo_info(fast_ip)
            info.latency_ms = latency
            self.current_ip_info = info

        if self.on_ip_update:
            self.on_ip_update(info)

        # CHECK 1: If Armed, check if IP has changed
        if self.state == self.STATE_ARMED:
            if self.locked_ip and fast_ip != self.locked_ip:
                reason = f"IP Address changed! Previous: {self.locked_ip} -> Now: {fast_ip} ({info.country_code})"
                self.trigger_kill(reason)
                return

            # CHECK 2: If Armed, check if country is in blocked list
            blocked = self.config.get("blocked_countries", ["RU", "BY"])
            if self.config.get("country_block", True) and info.country_code in blocked:
                reason = f"Country switched to blocked region ({info.country_code})!"
                self.trigger_kill(reason)
                return

        # CHECK 3: Auto-guard (If disarmed or untrusted, and auto-guard is enabled, kill Claude if launched)
        if self.config.get("auto_guard", True) and self.state == self.STATE_DISARMED:
            blocked = self.config.get("blocked_countries", ["RU", "BY"])
            if info.country_code in blocked:
                # Check if Claude is running while on Russian IP
                target_names = [t.lower() for t in self.config.get("target_processes", ["claude.exe"])]
                if psutil:
                    for proc in psutil.process_iter(['name']):
                        try:
                            if (proc.info['name'] or "").lower() in target_names:
                                self.trigger_kill("Claude was started without VPN on Russian IP!")
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

    def _monitor_loop(self):
        """Continuous polling thread."""
        while not self._stop_event.is_set():
            try:
                self._check_cycle()
            except Exception as e:
                self.log(f"Monitor error: {e}", "ERROR")

            interval = max(0.5, float(self.config.get("check_interval", 1.5)))
            self._stop_event.wait(interval)

    def _network_event_loop(self):
        """Win32 NotifyAddrChange event listener thread (sub-millisecond adapter change detection)."""
        try:
            iphlpapi = ctypes.WinDLL("iphlpapi.dll")
            iphlpapi.NotifyAddrChange.argtypes = [ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p]
            iphlpapi.NotifyAddrChange.restype = wintypes.DWORD

            while not self._stop_event.is_set():
                handle = wintypes.HANDLE()
                # Blocks until any network adapter/route changes in Windows
                res = iphlpapi.NotifyAddrChange(ctypes.byref(handle), None)
                if self._stop_event.is_set():
                    break

                if res == 0:  # NO_ERROR - network change detected!
                    self.log("⚡ Windows Network Adapter / Route change detected!", "WARNING")
                    # Immediately trigger check
                    if self.state == self.STATE_ARMED:
                        self._check_cycle()
                    time.sleep(0.5)  # debounce
        except Exception as e:
            self.log(f"Network event watcher error: {e}", "WARNING")

    def start(self):
        """Starts monitoring threads."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="MonitorLoop")
        self._monitor_thread.start()

        self._network_event_thread = threading.Thread(target=self._network_event_loop, daemon=True, name="NetWatcher")
        self._network_event_thread.start()

        self.log("Claude Kill Switch Engine started.", "INFO")

    def stop(self):
        """Stops monitoring threads."""
        self.is_running = False
        self._stop_event.set()
        if self._http_client:
            try:
                self._http_client.close()
            except Exception:
                pass
        self.log("Claude Kill Switch Engine stopped.", "INFO")
