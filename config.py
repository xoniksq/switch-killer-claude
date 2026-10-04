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
    "claude_path": "",                 # Custom path to claude.exe if non-standard
    "endpoints": [
        "https://icanhazip.com",
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
        "https://ifconfig.me/ip"
    ]
}

def get_claude_executable_path(custom_path: str = "") -> str:
    """Finds Claude Desktop executable path on user's machine."""
    # 1. Custom path override (argument or config)
    if custom_path and os.path.isfile(custom_path):
        return custom_path

    cfg = load_config()
    cfg_path = cfg.get("claude_path", "")
    if cfg_path and os.path.isfile(cfg_path):
        return cfg_path

    # 2. Check standard Windows installation directories
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    app_data = os.environ.get("APPDATA", "")
    prog_files = os.environ.get("ProgramFiles", "")
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", "")

    candidates = []

    if local_app_data:
        base_dir = Path(local_app_data) / "AnthropicClaude"
        candidates.append(base_dir / "claude.exe")
        if base_dir.exists():
            try:
                for p in sorted(base_dir.glob("app-*/claude.exe"), reverse=True):
                    candidates.append(p)
            except Exception:
                pass
        candidates.append(Path(local_app_data) / "Programs" / "Claude" / "Claude.exe")
        candidates.append(Path(local_app_data) / "Programs" / "Claude" / "claude.exe")
        candidates.append(Path(local_app_data) / "Claude" / "Claude.exe")
        candidates.append(Path(local_app_data) / "Claude" / "claude.exe")

    if app_data:
        candidates.append(Path(app_data) / "Claude" / "claude.exe")
        candidates.append(Path(app_data) / "AnthropicClaude" / "claude.exe")

    if prog_files:
        candidates.append(Path(prog_files) / "AnthropicClaude" / "claude.exe")
        candidates.append(Path(prog_files) / "Claude" / "Claude.exe")
        candidates.append(Path(prog_files) / "Claude" / "claude.exe")

    if prog_files_x86:
        candidates.append(Path(prog_files_x86) / "AnthropicClaude" / "claude.exe")
        candidates.append(Path(prog_files_x86) / "Claude" / "Claude.exe")
        candidates.append(Path(prog_files_x86) / "Claude" / "claude.exe")

    for cand in candidates:
        if cand.is_file():
            return str(cand)

    # 3. Check system PATH
    import shutil
    for cmd in ["claude.exe", "claude"]:
        found = shutil.which(cmd)
        if found and os.path.isfile(found):
            return found

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
