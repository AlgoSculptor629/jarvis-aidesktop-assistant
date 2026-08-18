import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import speech_recognition as sr
import config


class SpeechListener:
    """
    Robust Speech-To-Text listener using SpeechRecognition and Google Web Speech API.
    Provides ambient noise calibration, dynamic thresholds, and status callbacks.
    """
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.STT_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = config.STT_DYNAMIC_ENERGY
        self.recognizer.pause_threshold = config.STT_PAUSE_THRESHOLD
        self.status_callbacks = []
        self._calibrated = False

    def register_status_callback(self, callback):
        """Register a callback fn(status_text: str, state: str) for UI updates."""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)

    def _notify_status(self, status_text: str, state: str = "IDLE"):
        for cb in self.status_callbacks:
            try:
                cb(status_text, state)
            except Exception as e:
                print(f"[SpeechListener] Status callback error: {e}")

    def calibrate(self, duration: float = 0.6):
        """Calibrate recognizer energy threshold with ambient noise."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                self._calibrated = True
        except Exception as e:
            print(f"[SpeechListener] Calibration warning: {e}")

    def listen(self, timeout: float = None, phrase_time_limit: float = None) -> str | None:
        """
        Listens to the microphone and transcribes speech to text.
        Returns the recognized string, or None if silence/unintelligible.
        """
        if timeout is None:
            timeout = config.STT_TIMEOUT
        if phrase_time_limit is None:
            phrase_time_limit = config.STT_PHRASE_TIME_LIMIT

        try:
            with sr.Microphone() as source:
                if not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    self._calibrated = True

                self._notify_status("Listening...", "LISTENING")
                print("Listening...")

                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                except sr.WaitTimeoutError:
                    self._notify_status("Standby", "STANDBY")
                    return None

            self._notify_status("Recognizing...", "THINKING")
            print("Recognizing...")

            query = self.recognizer.recognize_google(
                audio,
                language=config.STT_LANGUAGE
            )

            print(f"User said: {query}\n")
            self._notify_status("Command received", "STANDBY")
            return query.strip()

        except sr.UnknownValueError:
            # Speech was unintelligible or silence
            print("Say that again please...")
            self._notify_status("Could not understand audio", "STANDBY")
            return None

        except sr.RequestError as e:
            # Network issue with Google Speech API
            print(f"Could not request results from Google Speech Recognition service; {e}")
            self._notify_status("STT Network Error", "STANDBY")
            return None

        except Exception as ex:
            print(f"Speech recognition error: {ex}")
            self._notify_status("Microphone Error", "STANDBY")
            return None


# Global singleton helper
_listener_instance = None

def get_speech_listener() -> SpeechListener:
    global _listener_instance
    if _listener_instance is None:
        _listener_instance = SpeechListener()
    return _listener_instance

def takeCommand() -> str:
    """
    Backwards-compatible takeCommand function returning a string.
    Returns 'None' if unrecognized (to preserve legacy compatibility)
    or the recognized string.
    """
    listener = get_speech_listener()
    result = listener.listen()
    return result if result is not None else "None"
