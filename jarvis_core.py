"""
JARVIS Core Legacy Compatibility Bridge
Exports speak, takeCommand, wishMe, and searchFile for backwards compatibility.
"""
from core.voice_engine import speak, speak_async, get_voice_engine
from core.speech_listener import takeCommand, get_speech_listener
from handlers.file_handler import searchFile, get_file_handler
from handlers.utility_handler import get_utility_handler
from handlers.dispatcher import dispatch_command

# Backwards compatibility helpers
engine = get_voice_engine()

def wishMe():
    handler = get_utility_handler()
    msg = handler.get_greeting()
    speak(msg)

__all__ = [
    "speak",
    "speak_async",
    "takeCommand",
    "wishMe",
    "searchFile",
    "dispatch_command"
]