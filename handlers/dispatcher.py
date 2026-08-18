import sys
import re
from pathlib import Path
from dataclasses import dataclass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from handlers.app_handler import get_app_handler
from handlers.file_handler import get_file_handler
from handlers.web_handler import get_web_handler
from handlers.system_handler import get_system_handler
from handlers.utility_handler import get_utility_handler
from core.ai_brain import get_ai_brain


@dataclass
class DispatchResult:
    action_type: str
    response_text: str
    should_exit: bool = False
    success: bool = True


class CommandDispatcher:
    """
    Central Intent Dispatcher.
    Parses user queries and executes the appropriate handler,
    falling back to conversational AI when no deterministic command matches.
    """
    def __init__(self):
        self.app_handler = get_app_handler()
        self.file_handler = get_file_handler()
        self.web_handler = get_web_handler()
        self.system_handler = get_system_handler()
        self.utility_handler = get_utility_handler()
        self.ai_brain = get_ai_brain()

    def dispatch(self, query: str) -> DispatchResult:
        if not query or not query.strip() or query.strip().lower() == "none":
            return DispatchResult(
                action_type="empty",
                response_text="",
                success=False
            )

        q = query.strip().lower()

        # =========================================================
        # 1. EXIT / TERMINATE COMMANDS
        # =========================================================
        if any(w in q for w in ["stop jarvis", "quit jarvis", "exit jarvis", "goodbye jarvis", "shutdown jarvis"]) or \
           q in ["stop", "quit", "exit", "goodbye", "bye"]:
            return DispatchResult(
                action_type="exit",
                response_text="Goodbye Sir. Have a productive day.",
                should_exit=True,
                success=True
            )

        # =========================================================
        # 2. TIME & DATE
        # =========================================================
        if any(pattern in q for pattern in ["the time", "what time", "current time", "time now"]):
            msg = self.utility_handler.get_time()
            return DispatchResult(action_type="time", response_text=msg)

        if any(pattern in q for pattern in ["the date", "what date", "today's date", "current date", "what day is it"]):
            msg = self.utility_handler.get_date()
            return DispatchResult(action_type="date", response_text=msg)

        # =========================================================
        # 3. SYSTEM STATS & LOCK
        # =========================================================
        if any(w in q for w in ["system status", "battery status", "cpu usage", "ram usage", "system telemetry"]):
            msg = self.system_handler.report_system_status()
            return DispatchResult(action_type="system_stats", response_text=msg)

        if any(w in q for w in ["lock screen", "lock workstation", "lock computer", "lock pc"]):
            ok, msg = self.system_handler.lock_workstation()
            return DispatchResult(action_type="lock", response_text=msg, success=ok)

        # =========================================================
        # 4. VOLUME CONTROLS
        # =========================================================
        if "volume" in q or "mute" in q or "unmute" in q:
            if any(w in q for w in ["volume up", "increase volume", "raise volume", "louder"]):
                ok, msg = self.system_handler.adjust_volume("up")
                return DispatchResult(action_type="volume", response_text=msg, success=ok)
            elif any(w in q for w in ["volume down", "decrease volume", "lower volume", "quieter"]):
                ok, msg = self.system_handler.adjust_volume("down")
                return DispatchResult(action_type="volume", response_text=msg, success=ok)
            elif "mute" in q or "unmute" in q:
                ok, msg = self.system_handler.adjust_volume("mute")
                return DispatchResult(action_type="volume", response_text=msg, success=ok)

        # =========================================================
        # 5. EXPLORER / SPECIAL FOLDERS
        # =========================================================
        folder_triggers = [
            "this pc", "my computer", "local disk c", "disk c", "drive c",
            "local disk d", "disk d", "drive d", "desktop", "documents",
            "downloads", "pictures", "videos"
        ]
        if q.startswith("open ") and any(folder in q for folder in folder_triggers):
            folder_target = q.replace("open", "").strip()
            ok, msg = self.system_handler.open_special_folder(folder_target)
            return DispatchResult(action_type="open_folder", response_text=msg, success=ok)

        # =========================================================
        # 6. WEB SHORTCUTS
        # =========================================================
        if "open youtube" in q:
            ok, msg = self.web_handler.open_url("https://www.youtube.com", "YouTube")
            return DispatchResult(action_type="web", response_text=msg, success=ok)

        if "open gmail" in q:
            ok, msg = self.web_handler.open_url("https://mail.google.com", "Gmail")
            return DispatchResult(action_type="web", response_text=msg, success=ok)

        if "open google" in q and not any(w in q for w in ["search", "what is"]):
            ok, msg = self.web_handler.open_url("https://www.google.com", "Google")
            return DispatchResult(action_type="web", response_text=msg, success=ok)

        if "open github" in q:
            ok, msg = self.web_handler.open_url("https://github.com", "GitHub")
            return DispatchResult(action_type="web", response_text=msg, success=ok)

        # =========================================================
        # 7. YOUTUBE PLAY / SEARCH
        # =========================================================
        if q.startswith("play ") or "on youtube" in q or "play on youtube" in q:
            ok, msg = self.web_handler.youtube_search(q)
            return DispatchResult(action_type="youtube", response_text=msg, success=ok)

        # =========================================================
        # 8. WIKIPEDIA
        # =========================================================
        if "wikipedia" in q:
            ok, msg = self.web_handler.search_wikipedia(q)
            return DispatchResult(action_type="wikipedia", response_text=msg, success=ok)

        # =========================================================
        # 9. WEATHER
        # =========================================================
        if "weather" in q:
            city = re.sub(r'.*weather\s+(?:in|for|at)?\s*', '', q).strip()
            city = city.replace("today", "").replace("now", "").strip()
            ok, msg = self.web_handler.get_weather(city)
            return DispatchResult(action_type="weather", response_text=msg, success=ok)

        # =========================================================
        # 10. NOTES & CALCULATIONS
        # =========================================================
        if any(q.startswith(w) for w in ["take a note", "write note", "note down", "make a note"]):
            ok, msg = self.utility_handler.add_note(q)
            return DispatchResult(action_type="note", response_text=msg, success=ok)

        if any(w in q for w in ["read notes", "read my notes", "show notes", "what are my notes"]):
            ok, msg = self.utility_handler.read_notes()
            return DispatchResult(action_type="note", response_text=msg, success=ok)

        if q.startswith("calculate ") or q.startswith("compute ") or q.startswith("math "):
            ok, msg = self.utility_handler.calculate(q)
            return DispatchResult(action_type="calc", response_text=msg, success=ok)

        # =========================================================
        # 11. FILE SEARCH & OPEN
        # =========================================================
        if any(trigger in q for trigger in ["find file", "search file", "open file"]):
            target_name = re.sub(r'.*(?:find file|search file|open file)\s*', '', q).strip()
            if target_name:
                ok, msg = self.file_handler.find_and_open_file(target_name)
                return DispatchResult(action_type="file_search", response_text=msg, success=ok)
            else:
                return DispatchResult(
                    action_type="file_prompt",
                    response_text="What is the name of the file you want to search for, Sir?",
                    success=True
                )

        # =========================================================
        # 12. CLOSE / KILL APPLICATION
        # =========================================================
        if q.startswith("close ") or q.startswith("terminate ") or q.startswith("kill "):
            app_target = re.sub(r'^(close|terminate|kill)\s+', '', q).strip()
            ok, msg = self.app_handler.close_app(app_target)
            return DispatchResult(action_type="close_app", response_text=msg, success=ok)

        # =========================================================
        # 13. OPEN APPLICATION / FILE / WEBSITE
        # =========================================================
        if q.startswith("open ") or q.startswith("launch ") or q.startswith("start "):
            target = re.sub(r'^(open|launch|start)\s+', '', q).strip()
            # Try app first
            ok, msg = self.app_handler.open_app(target)
            if ok:
                return DispatchResult(action_type="open_app", response_text=msg, success=True)

            # Try finding as a local file or document
            file_ok, file_msg = self.file_handler.find_and_open_file(target)
            if file_ok:
                return DispatchResult(action_type="file_search", response_text=file_msg, success=True)

            # Check if domain name (e.g. "open chatgpt.com" or "open reddit.com")
            if any(tld in target for tld in [".com", ".org", ".net", ".io", ".dev", ".ai", ".in"]):
                url = target if target.startswith("http") else f"https://{target}"
                ok_web, web_msg = self.web_handler.open_url(url, target)
                return DispatchResult(action_type="web", response_text=web_msg, success=ok_web)

            return DispatchResult(action_type="open_app", response_text=msg, success=False)

        # =========================================================
        # 14. EXPLICIT GOOGLE SEARCH
        # =========================================================
        if q.startswith("search ") or q.startswith("google ") or q.startswith("search for "):
            ok, msg = self.web_handler.google_search(q)
            return DispatchResult(action_type="google_search", response_text=msg, success=ok)

        # =========================================================
        # 15. GENERAL CONVERSATION & AI FALLBACK
        # =========================================================
        ai_reply = self.ai_brain.ask(query)
        return DispatchResult(
            action_type="ai_conversation",
            response_text=ai_reply,
            success=True
        )


# Global instance
_dispatcher_instance = None

def get_dispatcher() -> CommandDispatcher:
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = CommandDispatcher()
    return _dispatcher_instance

def dispatch_command(query: str) -> DispatchResult:
    """Helper to dispatch a command through singleton dispatcher."""
    return get_dispatcher().dispatch(query)
