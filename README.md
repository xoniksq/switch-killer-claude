# 🛡️ Claude Kill Switch (Windows Anti-Leak & Account Protector)

<p align="center">
  <a href="#-english"><b>🇬🇧 English</b></a> &nbsp;•&nbsp; <a href="#-русский"><b>🇷🇺 Русский</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OS-Windows%2010%20%7C%2011-blue?logo=windows" alt="Windows" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-blueviolet" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/License-Freeware%20%7C%20Non--Commercial-red" alt="License" />
  <img src="https://img.shields.io/badge/Author-xoniksq-white?logo=github" alt="Author" />
</p>

---

## 🇬🇧 English

**Claude Kill Switch** is a high-speed, hardware-level network monitor and emergency kill switch for **Claude Desktop (Anthropic)** on Windows.

If your VPN disconnects, changes routing, or leaks your real ISP IP, the utility **instantly terminates all Claude processes within milliseconds**, preventing Anthropic account suspensions or regional lockouts.

### ✨ Key Features

- **⚡ Sub-Millisecond Win32 Hook (`NotifyAddrChange`):**  
  Listens directly to Windows kernel network route changes via `iphlpapi.dll`. If your VPN adapter (TUN, WireGuard, OpenVPN, Sing-box, V2Ray) drops, the app catches it in 0–5 ms before packets can leak.
- **🚀 Ultra-Fast HTTP Keep-Alive Polling:**  
  Regularly verifies external exit IP via redundant fast endpoints (`icanhazip`, `api.ipify.org`, `checkip.amazonaws.com`) with connection pooling (~150 ms response time).
- **💥 Forceful Multi-Tier Process Killer:**  
  Combines Windows `taskkill /F /T /IM claude.exe` process-tree termination with deep `psutil` process scans to wipe all background Claude helpers and proxies.
- **🔒 Safe Launcher:**  
  The *"Launch Claude"* button checks your VPN and IP status first. If your connection is not secure, Claude will not be opened.
- **🛡️ Auto-Guard Protection:**  
  If Claude is launched while the kill switch is disarmed on a restricted IP, it is immediately terminated.
- **🎨 Obsidian Chrome Aesthetic:**  
  High-contrast Black & White Chrome theme with Dark/Light mode toggle and live system console.
- **🌐 Bilingual UI:**  
  Instant one-click switching between **English** and **Russian**.
- **🔊 Native System Error Sound:**  
  Triggers standard Windows critical stop alarm upon execution.

---

### 📦 Quick Start for Users

#### Option 1: Standalone Executable (No Python Required)
1. Go to the [Releases](https://github.com/xoniksq/switch-killer-claude/releases) section.
2. Download **`ClaudeKillSwitch.exe`**.
3. Run the file — zero dependencies required.

#### Option 2: Run from Source
1. Download or clone this repository:
   ```bash
   git clone https://github.com/xoniksq/switch-killer-claude.git
   cd switch-killer-claude
   ```
2. Run **`install.bat`** (installs required dependencies).
3. Run **`run.bat`** (or **`run_silent.vbs`** for clean windowed launch).

---

### ⚙️ Configuration (`config.json`)

Settings are automatically loaded from `config.json`:

```json
{
    "target_processes": [
        "claude.exe",
        "claude-code.exe",
        "claude-ssh-proxy.exe",
        "claude-ssh-broker.exe",
        "claude-ssh-askpass.exe"
    ],
    "check_interval": 1.5,
    "strict_mode": true,
    "country_block": true,
    "blocked_countries": ["RU", "BY"],
    "sound_alarm": true,
    "auto_guard": true,
    "language": "en",
    "theme": "dark"
}
```

---

### 👤 Author & License (English)

- **Author / Developer:** **[xoniksq](https://github.com/xoniksq)**
- **License:** **Freeware (Non-Commercial, No-Derivatives)**
  - ✅ **Free Personal Use:** Anyone may use this software free of charge.
  - ✅ **Free Sharing:** You may freely distribute original unmodified copies with attribution to `xoniksq`.
  - ❌ **No Commercial Use / No Selling:** Selling, licensing, or charging any fees is strictly prohibited.
  - ❌ **No Modifications:** Altering or distributing modified source code or binaries without explicit written permission from `xoniksq` is prohibited.

---
---

## 🇷🇺 Русский

**Claude Kill Switch** — сверхбыстрая утилита для Windows, предотвращающая блокировку аккаунта Claude (Anthropic). Программа непрерывно отслеживает сетевой интерфейс и внешний IP-адрес.

В случае обрыва VPN, смены IP или риска утечки реального провайдера утилита **за доли секунды принудительно закрывает все процессы Claude**, не давая приложению отправить запросы через незащищенную сеть.

### ✨ Возможности

- **⚡ Мгновенный перехват ядра Windows (Win32 API):**  
  Использует системный вызов `NotifyAddrChange` библиотеки `iphlpapi.dll`. Если сетевой адаптер VPN (WireGuard, OpenVPN, TUN, Sing-box, V2Ray) падает — программа реагирует за 0–5 мс, не дожидаясь таймера.
- **🚀 Сверхбыстрый Keep-Alive опрос IP:**  
  Каждые 1.5 сек сверяет реальный выходной IP через независимые серверы (`icanhazip`, `api.ipify.org`, `checkip.amazonaws.com`) с переиспользованием TCP-соединений (~150 мс).
- **💥 Бескомпромиссное закрытие процессов:**  
  Комбинация `taskkill /F /T /IM claude.exe` (уничтожение дерева процессов) и глубокого поиска через `psutil` (включая CLI `claude-code`, фоновые SSH-прокси и службы).
- **🔒 Безопасный лаунчер (Safe Launch):**  
  Кнопка *«Запустить Claude»* сначала верифицирует безопасность IP, включает защиту и только затем запускает Claude Desktop.
- **🛡️ Режим Auto-Guard:**  
  Если защита выключена, но Claude запущен на запрещённом IP — приложение мгновенно закроет его.
- **🎨 Дизайн «Чёрно-белый хром»:**  
  Контрастная эстетика с поддержкой переключения Тёмной и Светлой темы, а также живым системным логом.
- **🌐 Двуязычный интерфейс:**  
  Мгновенное переключение языка (**RU** ⇄ **EN**) в шапке приложения.
- **🔊 Системный звук ошибки:**  
  Звуковое оповещение стандартным сигналом критической ошибки Windows.

---

### 📦 Быстрый старт

#### Способ 1: Готовый `.exe` (без установки Python)
1. Перейдите в раздел [Releases](https://github.com/xoniksq/switch-killer-claude/releases).
2. Скачайте файл **`ClaudeKillSwitch.exe`**.
3. Запустите двойным кликом — установка зависимостей не требуется.

#### Способ 2: Запуск из исходного кода
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/xoniksq/switch-killer-claude.git
   cd switch-killer-claude
   ```
2. Запустите **`install.bat`** (установит необходимые библиотеки).
3. Запустите **`run.bat`** (или **`run_silent.vbs`** для запуска без консольного окна).

---

### 🔨 Сборка автономного `.exe`
Для самостоятельной компиляции в `.exe` запустите скрипт:
```cmd
build_exe.bat
```
Готовый исполняемый файл появится в папке `dist/ClaudeKillSwitch.exe`.

---

### 👤 Автор и лицензия (Русский)

- **Разработчик:** **[xoniksq](https://github.com/xoniksq)**
- **Лицензия:** **Freeware (Non-Commercial, No-Derivatives)**
  - ✅ **Бесплатное использование:** разрешено свободное личное и некоммерческое использование.
  - ✅ **Бесплатное распространение:** разрешено делиться оригинальной программой с обязательным указанием автора `xoniksq`.
  - ❌ **Запрет коммерции и продажи:** продажа программы или взимание платы категорически запрещены.
  - ❌ **Запрет модификации:** изменение кода, создание производных версий и их распространение запрещены без письменного согласия автора.
