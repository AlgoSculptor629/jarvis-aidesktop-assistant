import os
import ctypes
from pathlib import Path
import psutil

# Virtual key codes for Windows volume control
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


class SystemHandler:
    """
    System-level control for Windows:
    Folder navigation, volume control, battery/CPU telemetry, and workstation lock.
    """
    def __init__(self):
        self.home = Path.home()

    def open_special_folder(self, folder_type: str) -> tuple[bool, str]:
        """Opens standard Windows folders and drives."""
        folder_clean = folder_type.lower().strip()

        try:
            if any(w in folder_clean for w in ["this pc", "my computer"]):
                os.startfile("shell:MyComputerFolder")
                return True, "Opening This PC, Sir."

            elif any(w in folder_clean for w in ["disk c", "drive c", "local disk c"]):
                os.startfile("C:\\")
                return True, "Opening Local Disk C, Sir."

            elif any(w in folder_clean for w in ["disk d", "drive d", "local disk d"]):
                if os.path.exists("D:\\"):
                    os.startfile("D:\\")
                    return True, "Opening Local Disk D, Sir."
                else:
                    return False, "Local Disk D is not available on this machine, Sir."

            elif "desktop" in folder_clean:
                os.startfile(str(self.home / "Desktop"))
                return True, "Opening Desktop, Sir."

            elif "documents" in folder_clean:
                os.startfile(str(self.home / "Documents"))
                return True, "Opening Documents, Sir."

            elif "downloads" in folder_clean:
                os.startfile(str(self.home / "Downloads"))
                return True, "Opening Downloads, Sir."

            elif "pictures" in folder_clean:
                os.startfile(str(self.home / "Pictures"))
                return True, "Opening Pictures, Sir."

            elif "videos" in folder_clean:
                os.startfile(str(self.home / "Videos"))
                return True, "Opening Videos, Sir."

            return False, f"Could not find folder {folder_type}."

        except Exception as e:
            return False, f"Failed to open {folder_type}. Error: {e}"

    def adjust_volume(self, action: str, steps: int = 5) -> tuple[bool, str]:
        """Adjusts master Windows volume using native Windows API."""
        action_clean = action.lower()
        try:
            if "up" in action_clean or "increase" in action_clean:
                for _ in range(steps):
                    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
                return True, "Increased volume, Sir."

            elif "down" in action_clean or "decrease" in action_clean or "lower" in action_clean:
                for _ in range(steps):
                    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
                return True, "Decreased volume, Sir."

            elif "mute" in action_clean or "unmute" in action_clean:
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                return True, "Toggled volume mute, Sir."

        except Exception as e:
            return False, f"Could not adjust volume: {e}"

        return False, "Unknown volume command."

    def get_system_stats(self) -> dict:
        """Returns CPU, RAM, and Battery metrics."""
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()

        stats = {
            "cpu_percent": cpu,
            "memory_percent": mem,
            "battery_percent": battery.percent if battery else None,
            "power_plugged": battery.power_plugged if battery else None,
        }
        return stats

    def report_system_status(self) -> str:
        """Generates a verbal system status report."""
        stats = self.get_system_stats()
        msg = f"CPU utilization is at {stats['cpu_percent']:.0f} percent, and RAM usage is at {stats['memory_percent']:.0f} percent."

        if stats['battery_percent'] is not None:
            plug_str = "plugged in" if stats['power_plugged'] else "on battery power"
            msg += f" Battery is at {stats['battery_percent']:.0f} percent and {plug_str}."

        return msg

    def lock_workstation(self) -> tuple[bool, str]:
        """Locks the Windows user session."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "Locking workstation now, Sir."
        except Exception as e:
            return False, f"Could not lock screen: {e}"


# Global instance
_system_handler_instance = None

def get_system_handler() -> SystemHandler:
    global _system_handler_instance
    if _system_handler_instance is None:
        _system_handler_instance = SystemHandler()
    return _system_handler_instance
