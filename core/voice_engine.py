import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import threading
import queue
import pyttsx3
import time
import config

try:
    import pythoncom
except ImportError:
    pythoncom = None


class VoiceEngine:
    """
    Thread-safe, non-blocking Text-To-Speech engine using pyttsx3 and SAPI5.
    Uses a dedicated background worker to prevent GUI/audio loop blocking.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VoiceEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.queue = queue.Queue()
        self.is_speaking = False
        self.status_callbacks = []
        self.stop_event = threading.Event()

        # Start the background worker thread
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="JarvisTTSWorker"
        )
        self.worker_thread.start()

    def register_status_callback(self, callback):
        """Register a callback fn(is_speaking: bool, text: str) for UI updates."""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)

    def _notify_callbacks(self, is_speaking: bool, text: str = ""):
        for cb in self.status_callbacks:
            try:
                cb(is_speaking, text)
            except Exception as e:
                print(f"[VoiceEngine] Callback error: {e}")

    def _worker_loop(self):
        """Worker loop that initializes pyttsx3 in its own thread."""
        if pythoncom is not None:
            try:
                pythoncom.CoInitialize()
            except Exception:
                pass

        try:
            engine = pyttsx3.init(config.TTS_ENGINE)
            engine.setProperty("rate", config.TTS_RATE)
            engine.setProperty("volume", config.TTS_VOLUME)

            voices = engine.getProperty("voices")
            if voices and len(voices) > config.TTS_VOICE_INDEX:
                engine.setProperty("voice", voices[config.TTS_VOICE_INDEX].id)
        except Exception as e:
            print(f"[VoiceEngine] Initialization error: {e}")
            engine = None

        while not self.stop_event.is_set():
            try:
                item = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if item is None:  # Sentinel to exit
                break

            text, done_event = item

            if not text or not str(text).strip():
                if done_event:
                    done_event.set()
                self.queue.task_done()
                continue

            self.is_speaking = True
            self._notify_callbacks(True, text)

            try:
                if engine is not None:
                    engine.say(text)
                    engine.runAndWait()
                else:
                    print(f"[JARVIS VOICEOVER]: {text}")
                    time.sleep(len(text) * 0.05)
            except Exception as err:
                print(f"[VoiceEngine] Speak error: {err}")
                # Try reinitializing engine if it crashed
                try:
                    engine = pyttsx3.init(config.TTS_ENGINE)
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass
            finally:
                self.is_speaking = False
                self._notify_callbacks(False, "")
                if done_event:
                    done_event.set()
                self.queue.task_done()

        if pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def speak(self, text: str, block: bool = True):
        """
        Speaks the given text.
        If block is True, waits until speech is completed.
        If block is False, returns immediately.
        """
        if not text:
            return

        print(f"[Jarvis]: {text}")

        if block:
            done_event = threading.Event()
            self.queue.put((text, done_event))
            done_event.wait()
        else:
            self.queue.put((text, None))

    def speak_async(self, text: str):
        """Speak asynchronously without blocking the caller."""
        self.speak(text, block=False)

    def set_rate(self, rate: int):
        config.TTS_RATE = rate

    def set_volume(self, volume: float):
        config.TTS_VOLUME = max(0.0, min(1.0, volume))


# Global singleton helpers for clean backwards compatibility
_engine_instance = None

def get_voice_engine() -> VoiceEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = VoiceEngine()
    return _engine_instance

def speak(audio: str, block: bool = True):
    """Backwards-compatible speak function."""
    engine = get_voice_engine()
    engine.speak(audio, block=block)

def speak_async(audio: str):
    """Non-blocking speak function."""
    engine = get_voice_engine()
    engine.speak_async(audio)
