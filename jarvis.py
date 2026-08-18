"""
===================================================================
                       J A R V I S
          Personal Artificial Intelligence Assistant
===================================================================
Modular, high-reliability desktop assistant with voice interaction,
app & file control, system telemetry, web capabilities, and AI reasoning.
"""
import sys
import argparse

# Core imports
from core.voice_engine import speak, speak_async, get_voice_engine
from core.speech_listener import takeCommand, get_speech_listener
from core.wake_word import WakeWordListener
from core.ai_brain import get_ai_brain

# Handler imports
from handlers.file_handler import searchFile, get_file_handler
from handlers.app_handler import get_app_handler
from handlers.web_handler import get_web_handler
from handlers.system_handler import get_system_handler
from handlers.utility_handler import get_utility_handler
from handlers.dispatcher import dispatch_command, DispatchResult

# UI import
from ui.app_window import launch_gui, play_wake_chime


# =========================================================
# BACKWARDS-COMPATIBLE LEGACY FUNCTIONS
# =========================================================

def wishMe():
    """Dynamic hour-based greeting."""
    greeting = get_utility_handler().get_greeting()
    speak(greeting)


# =========================================================
# CLI RUNNER LOOP
# =========================================================

def run_cli():
    """Runs Jarvis in terminal / console mode with background wake-word and voice interaction."""
    import threading

    print("\n" + "=" * 55)
    print("        J A R V I S   (CLI MODE)")
    print("=" * 55)
    print("[Jarvis] Initializing wake-word listener ('Hey Jarvis')...\n")

    wishMe()

    wake_event = threading.Event()

    def on_wake(score):
        print(f"\n⚡ [WakeWord] 'Hey Jarvis' detected! (Score: {score:.2f})")
        play_wake_chime()
        wake_event.set()

    wake_listener = WakeWordListener(on_wake_callback=on_wake)
    wake_listener.start()

    print("[Jarvis] Sleeping in background. Say 'Hey Jarvis' to wake me up.")
    print("         (Press Ctrl+C to exit)\n")

    while True:
        try:
            # Wait for wake word trigger
            triggered = wake_event.wait(timeout=0.5)

            if triggered:
                wake_event.clear()
                wake_listener.pause()

                print("[Jarvis: LISTENING] Speak your command now...")
                query = takeCommand()

                if query and query != "None":
                    print(f"[USER]: {query}")
                    result: DispatchResult = dispatch_command(query)

                    if result.response_text:
                        speak(result.response_text)

                    if result.should_exit:
                        wake_listener.stop()
                        break
                else:
                    print("[Jarvis] Could not hear command, returning to sleep...")

                wake_listener.resume()
                print("\n[Jarvis: SLEEPING] Waiting for 'Hey Jarvis'...")

        except KeyboardInterrupt:
            speak("Goodbye Sir.")
            wake_listener.stop()
            break
        except Exception as e:
            print(f"[Jarvis CLI Error]: {e}")
            wake_listener.resume()


# =========================================================
# MAIN PROGRAM ENTRY POINT
# =========================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in Command Line Interface mode instead of GUI mode"
    )
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        # Default: Launch modern animated CustomTkinter GUI
        try:
            launch_gui()
        except Exception as e:
            print(f"[Jarvis GUI Error]: {e}. Falling back to CLI mode...")
            run_cli()