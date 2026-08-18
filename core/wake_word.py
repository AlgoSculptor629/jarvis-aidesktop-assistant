import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import threading
import time
import numpy as np
import config

try:
    import sounddevice as sd
    import openwakeword
    from openwakeword import Model
    WAKE_WORD_AVAILABLE = True
except Exception as e:
    WAKE_WORD_AVAILABLE = False
    _wake_error = str(e)


class WakeWordListener:
    """
    Hands-free background wake-word listener using openWakeWord ('Hey Jarvis').
    Runs on a dedicated audio stream thread and fires callbacks upon detection.
    """
    def __init__(self, on_wake_callback=None, threshold: float = None):
        self.on_wake_callback = on_wake_callback
        self.threshold = threshold if threshold is not None else config.WAKE_WORD_THRESHOLD
        self.model = None
        self.stream = None
        self.is_running = False
        self.is_paused = False
        self.last_detection_time = 0
        self.cooldown = 2.0  # seconds between wake detections
        self._thread = None

    def initialize_model(self) -> bool:
        if not WAKE_WORD_AVAILABLE:
            print(f"[WakeWord] openWakeWord or sounddevice is unavailable.")
            return False

        if self.model is not None:
            return True

        try:
            print("[WakeWord] Loading wake-word model ('hey_jarvis')...")
            try:
                self.model = Model(
                    wakeword_models=[config.WAKE_WORD_MODEL],
                    inference_framework="onnx"
                )
            except Exception:
                # If model files are not yet downloaded, download them automatically
                print("[WakeWord] Model files missing. Downloading pretrained weights...")
                try:
                    import openwakeword.utils
                    openwakeword.utils.download_models(model_names=[config.WAKE_WORD_MODEL])
                except Exception as dl_err:
                    print(f"[WakeWord] Download warning: {dl_err}")
                self.model = Model(
                    wakeword_models=[config.WAKE_WORD_MODEL],
                    inference_framework="onnx"
                )
            print("[WakeWord] Model loaded successfully.")
            return True
        except Exception as e:
            print(f"[WakeWord] Failed to load model: {e}")
            return False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass  # Suppress sounddevice warnings (e.g., input overflow)

        if not self.is_running or self.is_paused or self.model is None:
            return

        # Check cooldown
        now = time.time()
        if now - self.last_detection_time < self.cooldown:
            return

        try:
            # Convert float32 microphone buffer to int16 PCM
            audio = (indata[:, 0] * 32767).astype(np.int16)

            prediction = self.model.predict(audio)
            score = prediction.get(config.WAKE_WORD_MODEL, 0.0)

            if score >= self.threshold:
                self.last_detection_time = now
                print(f"\n[WakeWord] HEY JARVIS DETECTED! (Score: {score:.2f})")
                if self.on_wake_callback:
                    # Run callback in separate thread to avoid blocking audio callback
                    threading.Thread(
                        target=self.on_wake_callback,
                        args=(score,),
                        daemon=True
                    ).start()
        except Exception as e:
            print(f"[WakeWord] Callback error: {e}")

    def start(self):
        """Start listening for wake word in background."""
        if not config.WAKE_WORD_ENABLED or not WAKE_WORD_AVAILABLE:
            return False

        if self.is_running:
            return True

        if not self.initialize_model():
            return False

        try:
            self.is_running = True
            self.is_paused = False

            self.stream = sd.InputStream(
                samplerate=config.WAKE_SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=config.WAKE_BLOCK_SIZE,
                callback=self._audio_callback
            )
            self.stream.start()
            print("[WakeWord] Background listener active.")
            return True
        except Exception as e:
            print(f"[WakeWord] Error starting audio stream: {e}")
            self.is_running = False
            return False

    def pause(self):
        """Pause wake word detection while Jarvis is speaking or processing."""
        self.is_paused = True
        if self.stream is not None:
            try:
                self.stream.stop()
            except Exception:
                pass

    def resume(self):
        """Resume wake word detection."""
        self.is_paused = False
        if self.stream is not None:
            try:
                if not self.stream.active:
                    self.stream.start()
            except Exception:
                pass

    def stop(self):
        """Stop audio stream and background listener."""
        self.is_running = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        print("[WakeWord] Stopped.")


if __name__ == "__main__":
    print("=" * 40)
    print("      JARVIS WAKE WORD TEST")
    print("=" * 40)
    if not WAKE_WORD_AVAILABLE:
        print("[Error] openWakeWord or sounddevice is not available.")
    else:
        print("Starting listener... Say 'Hey Jarvis' into your microphone.")
        listener = WakeWordListener(
            on_wake_callback=lambda score: print(f"-> Wake Word Detected! (Score: {score:.2f})")
        )
        if listener.start():
            print("Listening in background. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                listener.stop()
                print("\nWake Word test completed.")
        else:
            print("Failed to start Wake Word listener.")

