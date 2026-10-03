# 🛡️ Claude Kill Switch (Windows Anti-Leak & Account Protector)

<p align="center">
  <img src="https://img.shields.io/badge/OS-Windows%2010%20%7C%2011-blue?logo=windows" alt="Windows" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-blueviolet" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/License-Freeware%20%7C%20Non--Commercial-red" alt="License" />
  <img src="https://img.shields.io/badge/Author-xoniksq-white?logo=github" alt="Author" />
</p>

Утилита **Kill Switch** для Windows, предотвращающая блокировку аккаунта Claude (Anthropic). Программа отслеживает сетевой интерфейс и внешний IP-адрес в режиме реального времени. 

В случае обрыва VPN, смены IP или риска утечки реального российского/белорусского IP-адреса утилита **за доли секунды принудительно завершает все процессы Claude**, не давая приложению отправить запросы через незащищенное соединение.

---

## ⚡ Особенности и возможности

- **⚡ Мгновенный перехват событий сети (Win32 API):**  
  Использует системный вызов ядра Windows `NotifyAddrChange` (`iphlpapi.dll`). Если VPN-адаптер (WireGuard, OpenVPN, TUN, V2Ray/Sing-box) падает — программа реагирует мгновенно (в течение 0–5 мс), не дожидаясь таймера опроса.
- **🚀 Быстрый Keep-Alive опрос IP:**  
  Каждые 1.5 сек сверяет внешний IP через пул независимых endpoint'ов (`icanhazip`, `api.ipify.org`, `checkip.amazonaws.com`). Ответ за ~150–200 мс с переиспользованием TCP-соединений.
- **💥 Бескомпромиссное завершение процессов:**  
  Комбинация вызова `taskkill /F /T /IM claude.exe` (уничтожает всё дерево процессов) и глубокого обхода дерева процессов через `psutil` (включая CLI `claude-code`, фоновые SSH-прокси и т.д.).
- **🔒 Безопасный лаунчер (Safe Launch):**  
  Кнопка *«Запустить Claude»* сначала верифицирует безопасность IP (не RU/BY, VPN активен), включает блокировку и лишь затем запускает Claude Desktop.
- **🛡️ Режим Auto-Guard:**  
  Если защита отключена, но обнаружен запуск Claude на запрещенном IP — приложение мгновенно закроет его.
- **🔊 Звуковая сирена:**  
  Громкий звуковой сигнал тревоги при срабатывании.
- **🎨 Современный интерфейс:**  
  Темная тема CustomTkinter, отображение страны с флагом, города, провайдера, пинга и логов в реальном времени.

---

## 📦 Быстрый старт (для пользователей)

### Вариант 1: Запуск из исходников (самый простой)
1. Скачайте репозиторий (кнопка **Code** → **Download ZIP** или `git clone`).
2. Распакуйте папку.
3. Запустите файл **`install.bat`** (он установит необходимые зависимости для Python).
4. Запустите **`run.bat`** (или **`run_silent.vbs`** для запуска без консольного окна).

### Вариант 2: Сборка в автономный `.exe`
Если вы хотите запускать программу без установленного Python на других ПК:
1. Запустите скрипт **`build_exe.bat`**.
2. В появившейся папке `dist/` появится файл **`ClaudeKillSwitch.exe`**.

---

## 💻 Разработчикам (Ручная установка)

```bash
git clone https://github.com/xoniksq/switch-killer-claude.git
cd switch-killer-claude

# Установка зависимостей
pip install -r requirements.txt

# Запуск графического интерфейса
python main.py

# Или запуск в консольном режиме (CLI)
python main.py --cli
```

---

## ⚙️ Конфигурация (`config.json`)

Файл настроек создается автоматически при первом запуске:

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
    "auto_guard": true
}
```

* `target_processes` — список имен исполняемых файлов для принудительного закрытия.
* `check_interval` — частота проверки IP в секундах.
* `strict_mode` — если `true`, закрывает Claude даже при полной потере связи / таймауте.
* `country_block` — авто-убийство процессов при определении стран из `blocked_countries`.
* `sound_alarm` — проигрывание звука тревоги через системный динамик.

---

## 👤 Автор

Разработчик: **[xoniksq](https://github.com/xoniksq)**

---

## 📄 Лицензия

Программное обеспечение распространяется под лицензией **Freeware (Non-Commercial, No-Derivatives)**:
- ✅ **Бесплатное использование:** разрешено свободное личное и некоммерческое использование.
- ✅ **Бесплатное распространение:** разрешено делиться программой в исходном виде с обязательным указанием авторства (`xoniksq`).
- ❌ **Запрет коммерции и продаж:** продажа, сублицензирование, монетизация или взимание платы за программу строго запрещены.
- ❌ **Запрет модификаций:** изменение кода, создание производных версий и их распространение запрещены без письменного согласия автора.
