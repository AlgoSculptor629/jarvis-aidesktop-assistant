import os
import sys
from pathlib import Path

# =========================================================
# PATH CONFIGURATION
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

NOTES_FILE = DATA_DIR / "notes.txt"
REMINDERS_FILE = DATA_DIR / "reminders.json"

# Default directories scanned for file search
USER_HOME = Path.home()
SEARCH_DIRECTORIES = [
    USER_HOME / "Desktop",
    USER_HOME / "Documents",
    USER_HOME / "Downloads",
    USER_HOME / "Pictures",
    USER_HOME / "Videos",
]

# Folders to skip during deep file searches for performance
SEARCH_IGNORE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    "AppData",
    ".vscode",
    ".idea",
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "System32",
    "$Recycle.Bin",
}

# Maximum recursion depth when searching files
MAX_SEARCH_DEPTH = 4

# =========================================================
# VOICE ENGINE CONFIGURATION (TTS)
# =========================================================
TTS_ENGINE = "sapi5" if sys.platform == "win32" else "nsss"
TTS_RATE = 180          # Speech speed (words per min)
TTS_VOLUME = 1.0        # Volume (0.0 to 1.0)
TTS_VOICE_INDEX = 0     # 0 for default male/David, 1 for female/Zira (if available)

# =========================================================
# SPEECH RECOGNITION CONFIGURATION (STT)
# =========================================================
STT_LANGUAGE = "en-in"   # Primary recognition language
STT_ENERGY_THRESHOLD = 300
STT_DYNAMIC_ENERGY = True
STT_PAUSE_THRESHOLD = 0.8
STT_PHRASE_TIME_LIMIT = 10
STT_TIMEOUT = 5

# =========================================================
# WAKE WORD CONFIGURATION (openWakeWord)
# =========================================================
WAKE_WORD_ENABLED = True
WAKE_WORD_MODEL = "hey_jarvis"
WAKE_WORD_THRESHOLD = 0.5
WAKE_SAMPLE_RATE = 16000
WAKE_BLOCK_SIZE = 1280

# =========================================================
# AI / LLM BRAIN CONFIGURATION
# =========================================================
# Read API key from environment or fallback
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"

# Local Ollama endpoint if available
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "llama3:8b"

SYSTEM_PROMPT = (
    "You are JARVIS, an advanced, highly intelligent desktop AI assistant. "
    "Respond in a concise, articulate, and polite tone, addressing the user as Sir when appropriate. "
    "Keep voice responses brief (1-3 sentences maximum) unless the user explicitly requests an in-depth explanation."
)

# =========================================================
# UI CONFIGURATION
# =========================================================
UI_THEME = "dark"
UI_TITLE = "JARVIS - AI Desktop Assistant"
UI_GEOMETRY = "1100x700"
UI_MIN_SIZE = (950, 620)

COLOR_BG = "#05070A"
COLOR_PANEL = "#0A0F14"
COLOR_PANEL_2 = "#0D141B"
COLOR_WHITE = "#EAF2F7"
COLOR_MUTED = "#667784"
COLOR_CYAN = "#00D9FF"
COLOR_CYAN_DARK = "#073847"
COLOR_GREEN = "#00E676"
COLOR_RED = "#FF4D67"
COLOR_YELLOW = "#FFD166"

# =========================================================
# COMMON APPLICATION SHORTCUTS & ALIASES
# =========================================================
APP_ALIASES = {
    "antigravity": ["antigravity", "antigravity ide", "antigravityide", "agy"],
    "code": ["code", "vs code", "visual studio code"],
    "chrome": ["chrome", "google chrome"],
    "brave": ["brave", "brave browser"],
    "edge": ["edge", "microsoft edge"],
    "firefox": ["firefox", "mozilla firefox"],
    "spotify": ["spotify", "music"],
    "notepad": ["notepad", "text editor"],
    "calc": ["calculator", "calc"],
    "cmd": ["cmd", "command prompt", "terminal"],
    "powershell": ["powershell", "ps"],
    "taskmgr": ["task manager", "taskmgr", "processes"],
    "explorer": ["file explorer", "explorer", "files"],
    "settings": ["settings", "windows settings", "control panel"],
    "discord": ["discord"],
    "steam": ["steam"],
    "vlc": ["vlc", "vlc media player"],
}
