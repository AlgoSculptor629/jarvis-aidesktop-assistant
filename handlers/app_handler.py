import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import subprocess
import winreg
import config
import psutil


import shutil


class AppHandler:
    """
    Intelligent Application Launcher & Process Controller for Windows.
    Discovers installed apps via Start Menu, Desktop, Registry, Environment Paths, and Local Programs.
    """
    def __init__(self):
        self._cached_apps = {}
        self.refresh_app_cache()

    def refresh_app_cache(self):
        """Scans Windows Start Menu, Desktop, and Programs folders for .lnk and .exe files."""
        dirs = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path.home() / "Desktop",
            Path("C:/Users/Public/Desktop"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        ]
        self._cached_apps = {}
        for d in dirs:
            if d.exists():
                for root, _, files in os.walk(d):
                    for file in files:
                        if file.lower().endswith((".lnk", ".exe")):
                            name = file.rsplit(".", 1)[0].lower().strip()
                            full_path = os.path.join(root, file)
                            self._cached_apps[name] = full_path

    def _find_in_registry(self, app_name: str) -> str | None:
        """Looks up executable path in Windows Registry App Paths."""
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]
        for root_key, sub_key in reg_paths:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for i in range(count):
                        try:
                            app_sub = winreg.EnumKey(key, i)
                            if app_name.lower() in app_sub.lower():
                                with winreg.OpenKey(key, app_sub) as target:
                                    val, _ = winreg.QueryValueEx(target, "")
                                    if val and os.path.exists(val):
                                        return val
                        except Exception:
                            continue
            except Exception:
                continue
        return None

    def find_app_path(self, target: str) -> str | None:
        """Attempts to find the path or command for a requested application."""
        if not target:
            return None

        target_clean = target.lower().strip()
        # Remove common filler words
        for filler in ["the app", "the application", "the program", "the software", "please", "app", "application"]:
            if target_clean.endswith(f" {filler}"):
                target_clean = target_clean[:-len(f" {filler}")].strip()
            elif target_clean.startswith(f"{filler} "):
                target_clean = target_clean[len(f"{filler} "):].strip()

        # 1. Check known aliases in config.py
        for alias_key, alias_list in config.APP_ALIASES.items():
            if target_clean == alias_key or any(target_clean == a or a in target_clean for a in alias_list):
                if alias_key == "antigravity":
                    # Check desktop, local appdata, or cached apps
                    if (Path.home() / "Desktop" / "Antigravity IDE.lnk").exists():
                        return str(Path.home() / "Desktop" / "Antigravity IDE.lnk")
                    for k, v in self._cached_apps.items():
                        if "antigravity" in k:
                            return v
                elif alias_key == "code":
                    user_code = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe"
                    if user_code.exists():
                        return str(user_code)
                    if (Path.home() / "Desktop" / "Visual Studio Code.lnk").exists():
                        return str(Path.home() / "Desktop" / "Visual Studio Code.lnk")
                    return "code"
                elif alias_key == "spotify":
                    return "spotify:"
                elif alias_key == "discord":
                    return "discord:"
                elif alias_key == "steam":
                    return "steam:"
                elif alias_key == "settings":
                    return "ms-settings:"
                elif alias_key == "calc":
                    return "calc.exe"
                elif alias_key == "notepad":
                    return "notepad.exe"
                elif alias_key == "cmd":
                    return "cmd.exe"
                elif alias_key == "powershell":
                    return "powershell.exe"
                elif alias_key == "taskmgr":
                    return "taskmgr.exe"
                elif alias_key == "explorer":
                    return "explorer.exe"

        # 2. Check Antigravity / IDE specifically
        if "antigravity" in target_clean or "agy" in target_clean:
            desktop_link = Path.home() / "Desktop" / "Antigravity IDE.lnk"
            if desktop_link.exists():
                return str(desktop_link)
            for name, path in self._cached_apps.items():
                if "antigravity" in name:
                    return path

        # 3. Check VS Code specifically
        if any(w in target_clean for w in ["code", "vs code", "vs", "visual studio code"]):
            user_code = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe"
            if user_code.exists():
                return str(user_code)
            pfiles_code = Path("C:/Program Files/Microsoft VS Code/Code.exe")
            if pfiles_code.exists():
                return str(pfiles_code)
            return "code"

        # 4. Check cached Start Menu & Desktop shortcuts (exact & fuzzy)
        # Exact match
        if target_clean in self._cached_apps:
            return self._cached_apps[target_clean]

        # Word subset match
        for name, path in self._cached_apps.items():
            if target_clean in name or name in target_clean:
                return path

        # Word token overlap match
        target_words = set(target_clean.split())
        for name, path in self._cached_apps.items():
            name_words = set(name.split())
            if target_words and target_words.issubset(name_words):
                return path

        # 5. Check Windows Registry App Paths
        reg_match = self._find_in_registry(target_clean)
        if reg_match:
            return reg_match

        # 6. Check common browser paths
        if "chrome" in target_clean:
            candidates = [
                str(Path.home() / "Desktop" / "Google Chrome.lnk"),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c

        if "brave" in target_clean:
            candidates = [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe")
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c

        # 7. Check if system command/executable is available on PATH
        which_path = shutil.which(target_clean) or shutil.which(f"{target_clean}.exe")
        if which_path:
            return which_path

        return None

    def open_app(self, app_name: str) -> tuple[bool, str]:
        """Opens the specified application and returns (success, message)."""
        app_path = self.find_app_path(app_name)

        if not app_path:
            # Fallback to attempting start command directly
            try:
                os.startfile(app_name)
                return True, f"Opening {app_name}, Sir."
            except Exception:
                return False, f"Sorry Sir, I could not find or launch {app_name}."

        try:
            if app_path.endswith((".exe", ".lnk")) or ":" in app_path:
                os.startfile(app_path)
            else:
                subprocess.Popen(app_path, shell=True)
            return True, f"Opening {app_name}, Sir."
        except Exception as e:
            return False, f"Failed to launch {app_name}. Error: {e}"

    def close_app(self, app_name: str) -> tuple[bool, str]:
        """Closes a running application by process name."""
        app_name_clean = app_name.lower().strip()
        closed_count = 0

        # Known process name mappings
        mappings = {
            "code": ["code.exe"],
            "vs code": ["code.exe"],
            "chrome": ["chrome.exe"],
            "spotify": ["spotify.exe"],
            "notepad": ["notepad.exe"],
            "calculator": ["calculatorapp.exe", "calc.exe"],
            "discord": ["discord.exe"],
            "brave": ["brave.exe"],
            "edge": ["msedge.exe"]
        }

        target_exes = []
        for key, exes in mappings.items():
            if key in app_name_clean:
                target_exes.extend(exes)

        try:
            for proc in psutil.process_iter(['pid', 'name']):
                pname = (proc.info['name'] or "").lower()
                should_kill = False

                if target_exes:
                    if pname in target_exes:
                        should_kill = True
                elif app_name_clean in pname:
                    should_kill = True

                if should_kill:
                    try:
                        proc.terminate()
                        closed_count += 1
                    except Exception:
                        pass

            if closed_count > 0:
                return True, f"Closed {app_name}, Sir."
            else:
                return False, f"I could not find an active process for {app_name}."
        except Exception as e:
            return False, f"Error terminating {app_name}: {e}"


# Singleton
_app_handler_instance = None

def get_app_handler() -> AppHandler:
    global _app_handler_instance
    if _app_handler_instance is None:
        _app_handler_instance = AppHandler()
    return _app_handler_instance
