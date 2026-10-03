import sys
import time
import os
from engine import KillSwitchEngine, IPInfo
from config import load_config

def run_cli():
    config = load_config()
    engine = KillSwitchEngine(config)

    print("=" * 60)
    print("      🛡️  CLAUDE KILL SWITCH — CONSOLE ENGINE")
    print("=" * 60)
    print("Мгновенное завершение Claude при смене IP или падении VPN.")
    print("Нажмите Ctrl+C для выхода.\n")

    def log_handler(msg: str, level: str):
        icons = {
            "INFO": "[*]",
            "SUCCESS": "[+]",
            "WARNING": "[!]",
            "ERROR": "[-]",
            "CRITICAL": "[🚨]"
        }
        icon = icons.get(level, "[*]")
        print(f"{icon} {msg}")

    engine.on_log = log_handler

    # Start engine
    engine.start()
    time.sleep(0.5)

    # Initial arm
    info = engine.refresh_ip()
    print(f"Текущий IP: {info.ip} [{info.country_code} - {info.country}] ({info.isp})")

    if engine.arm():
        print(f"\n[+] Защита АКТИВНА. Зафиксирован IP: {engine.locked_ip}")
        print("[+] Мониторинг сети запущен. При падении VPN Claude будет закрыт мгновенно.\n")
    else:
        print("\n[-] Внимание: Не удалось активировать защиту. Убедитесь, что VPN включен!\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка Kill Switch...")
        engine.stop()
        print("Завершено.")

if __name__ == "__main__":
    run_cli()
