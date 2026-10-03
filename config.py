import os
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "target_processes": [
        "claude.exe",
        "claude-code.exe",
        "claude-ssh-proxy.exe",
        "claude-ssh-broker.exe",
        "claude-ssh-askpass.exe"
    ],
    "check_interval": 1.5,
    "strict_mode": True,               # Kill if connection drops or consecutive timeouts
    "country_block": True,             # Kill if country becomes RU, BY or changes from armed country
    "blocked_countries": ["RU", "BY"],
    "sound_alarm": True,               # Audible beep on kill
    "auto_guard": True,                # Prevent Claude from starting if kill switch is disarmed or unsafe
    "close_browser_claude_tabs": False, # Optional: close browser tabs (future extension)
    "endpoints": [
        "https://icanhazip.com",
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
        "https://ifconfig.me/ip"
    ]
}

def get_claude_executable_path() -> str:
    """Finds Claude Desktop executable path on user's machine."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        claude_path = Path(local_app_data) / "AnthropicClaude" / "claude.exe"
        if claude_path.exists():
            return str(claude_path)
        
        # Check subdirectories if any
        base_dir = Path(local_app_data) / "AnthropicClaude"
        if base_dir.exists():
            for p in base_dir.glob("app-*/claude.exe"):
                return str(p)
    return ""

def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                config.update(user_cfg)
        except Exception:
            pass
    return config

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
