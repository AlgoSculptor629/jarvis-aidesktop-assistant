import sounddevice as sd
import numpy as np
import openwakeword
from openwakeword.model import Model


# ==========================================
# LOAD MODEL
# ==========================================

print("Loading Hey Jarvis model...")

model = Model(
    wakeword_models=["hey_jarvis"],
    inference_framework="onnx"
)

print("Wake-word model loaded.")


# ==========================================
# SETTINGS
# ==========================================

SAMPLE_RATE = 16000
BLOCK_SIZE = 1280

detected = False


# ==========================================
# MICROPHONE CALLBACK
# ==========================================

def callback(indata, frames, time, status):

    global detected

    if status:
        print(status)

    # Convert microphone audio to int16
    audio = (
        indata[:, 0] * 32767
    ).astype(np.int16)

    # Ask wake-word model
    prediction = model.predict(audio)

    score = prediction.get(
        "hey_jarvis",
        0
    )

    # Wake word detected
    if score > 0.5:

        print(
            f"\nHEY JARVIS DETECTED!"
            f" Score: {score:.2f}"
        )

        detected = True


# ==========================================
# START
# ==========================================

print()
print("==============================")
print("       JARVIS WAKE TEST")
print("==============================")
print()
print("Jarvis is in standby...")
print('Say "Hey Jarvis"')
print()


# ==========================================
# MICROPHONE STREAM
# ==========================================

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    blocksize=BLOCK_SIZE,
    callback=callback
):

    while not detected:
        sd.sleep(100)


print()
print("Wake word test finished.")