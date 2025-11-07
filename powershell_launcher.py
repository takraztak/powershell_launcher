# ============================================
# File: Powershell_launcher.py
# Purpose: Universal PowerShell Script Launcher (hybrid version, safe for spaces)
# Author: takraztak
# ============================================

import os
import sys
import subprocess
import shutil
import datetime
import ctypes
import shlex

# === оформление ===
FRAME_WIDTH = 72
TITLE = "Universal PowerShell Launcher"
AUTHOR = "by takraztak"

class Color:
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    GRAY = "\033[37m"
    DARKGRAY = "\033[90m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def show_header(subtitle=None, current_path=None):
    clear_screen()
    print(Color.CYAN + "=" * FRAME_WIDTH + Color.RESET)
    print(Color.CYAN + f"{TITLE} {AUTHOR}".center(FRAME_WIDTH) + Color.RESET)
    print(Color.CYAN + "=" * FRAME_WIDTH + Color.RESET)
    if subtitle:
        print(Color.GRAY + subtitle.center(FRAME_WIDTH) + Color.RESET)
        print(Color.DARKCYAN + "-" * FRAME_WIDTH + Color.RESET)
    if current_path:
        print(Color.DARKGRAY + f"📂 Path: {shorten_path(current_path)}" + Color.RESET)
        print(Color.DARKCYAN + "-" * FRAME_WIDTH + Color.RESET)

def shorten_path(path, max_len=60):
    if len(path) <= max_len:
        return path
    half = (max_len - 5) // 2
    return f"{path[:half]} ... {path[-half:]}"

def pause(msg="\nPress Enter to continue..."):
    input(msg)

# === Проверка прав администратора ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# === Повышение прав с защитой от пробелов ===
def elevate():
    try:
        # формируем строку аргументов с кавычками при необходимости
        quoted_args = " ".join(
            f'"{a}"' if " " in a or "\\" in a else a
            for a in sys.argv
        )

        # выполняем повторный запуск с правами администратора
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, quoted_args, None, 1
        )

        # завершаем текущий процесс, чтобы не выполнять код дважды
        sys.exit(0)

    except Exception as e:
        print(Color.RED + f"[ERROR] Elevation failed: {e}" + Color.RESET)
        pause()
        sys.exit(1)

# === Определение PowerShell ===
def detect_pwsh():
    pwsh7 = shutil.which("pwsh.exe")
    pwsh5 = shutil.which("powershell.exe")
    if pwsh7:
        return pwsh7, "PowerShell 7"
    elif pwsh5:
        return pwsh5, "PowerShell 5"
    else:
        print(Color.RED + "[ERROR] PowerShell not found." + Color.RESET)
        pause()
        sys.exit(1)

# === Запуск PowerShell-скрипта ===
def run_ps1(script_path, ps_args=None, auto_close=False):
    pwsh, version = detect_pwsh()
    print(Color.DARKCYAN + f"\nUsing {version} [{pwsh}]" + Color.RESET)
    print(Color.DARKCYAN + "-" * FRAME_WIDTH + Color.RESET)

    if auto_close:
        cmd = [
            "cmd", "/c", "start", "pwsh",
            "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", script_path
        ]
        if ps_args:
            cmd += ps_args
    else:
        wrapped = (
            f'& {{ . "{script_path}"; '
            f'Write-Host ""; Read-Host "Press Enter to close window..." }}'
        )
        cmd = [
            "cmd", "/c", "start", "pwsh",
            "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-Command", wrapped
        ]

    try:
        subprocess.run(cmd, check=False)
        print(Color.GREEN + f"\n[OK] Launched: {os.path.basename(script_path)}" + Color.RESET)
    except Exception as e:
        print(Color.RED + f"\n[ERROR] {e}" + Color.RESET)
    if not auto_close:
        pause()

# === Проверка на путь ===
def looks_like_path(arg):
    if os.path.exists(arg):
        return True
    if "\\" in arg or "/" in arg or ":" in arg:
        return True
    return False

# === Список .ps1 файлов ===
def list_ps1_files(directory):
    files = [f for f in os.listdir(directory) if f.lower().endswith(".ps1")]
    return sorted(files, key=str.lower)

# === Меню выбора ===
def menu_select(directory):
    ps1_files = list_ps1_files(directory)
    if not ps1_files:
        print(Color.RED + f"\n[ERROR] No .ps1 files found in:\n  {directory}" + Color.RESET)
        pause()
        return None

    while True:
        show_header(f"Scripts in: {os.path.basename(directory)}", directory)
        print(Color.DARKCYAN + f"{'No':<5} {'Script Name':<40} {'Modified'}" + Color.RESET)
        print(Color.CYAN + "-" * FRAME_WIDTH + Color.RESET)

        for i, name in enumerate(ps1_files, start=1):
            path = os.path.join(directory, name)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            color = Color.GRAY if i % 2 else Color.DARKGRAY
            print(color + f"{i:<5} {name:<40} {mtime.strftime('%Y-%m-%d %H:%M')}" + Color.RESET)

        print(Color.CYAN + "-" * FRAME_WIDTH + Color.RESET)
        print(Color.DARKGRAY + "00 - Exit" + Color.RESET)
        print(Color.CYAN + "=" * FRAME_WIDTH + Color.RESET)

        choice = input(Color.CYAN + "\nEnter number (or press Enter to cancel): " + Color.RESET).strip()
        if not choice or choice in ("0", "00"):
            return None
        if not choice.isdigit() or not (1 <= int(choice) <= len(ps1_files)):
            continue

        return os.path.join(directory, ps1_files[int(choice) - 1])

# === Главная функция ===
def main():
    show_header("PowerShell Launcher Hybrid")

    args = sys.argv[1:]
    auto_close = "--auto" in args
    auto_admin = "--admin" in args

    # убираем служебные флаги
    args = [a for a in args if a not in ("--auto", "--admin")]

    # если требуется авто-повышение прав
    if auto_admin and not is_admin():
        print(Color.YELLOW + "[INFO] Auto-elevating to administrator..." + Color.RESET)
        elevate()

    # режим без аргументов → меню
    if not args:
        directory = os.path.dirname(os.path.abspath(__file__))
        selected = menu_select(directory)
        if selected:
            run_ps1(selected, auto_close=auto_close)
        return

    target = args[0].strip().strip('"').strip("'")
    ps_args = [a.strip().strip('"').strip("'") for a in args[1:]]
    if len(args) == 2 and not looks_like_path(args[1]):
        ps_args = shlex.split(args[1])

    if os.path.isdir(target):
        selected = menu_select(target)
        if selected:
            run_ps1(selected, ps_args, auto_close=auto_close)
        return

    if os.path.isfile(target) and target.lower().endswith(".ps1"):
        show_header("Direct Script Launch", os.path.dirname(target))
        run_ps1(target, ps_args, auto_close=auto_close)
        return

    print(Color.RED + f"[ERROR] Path not found:\n  {target}" + Color.RESET)
    pause()

if __name__ == "__main__":
    main()
    print("\n===============================")
    input("Press Enter to exit...")
