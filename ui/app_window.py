import sys
import os
import math
import threading
import datetime
import tkinter as tk
import customtkinter as ctk
import psutil
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from core.voice_engine import get_voice_engine, speak
from core.speech_listener import get_speech_listener
from core.wake_word import WakeWordListener
from handlers.dispatcher import dispatch_command, DispatchResult
from handlers.utility_handler import get_utility_handler


def play_wake_chime():
    """Plays an instant futuristic wake chime when Jarvis wakes up."""
    try:
        import winsound
        winsound.Beep(900, 70)
        winsound.Beep(1400, 100)
    except Exception:
        pass


class JarvisApp:
    def __init__(self):
        ctk.set_appearance_mode(config.UI_THEME)

        self.app = ctk.CTk()
        self.app.title(config.UI_TITLE)
        self.app.geometry(config.UI_GEOMETRY)
        self.app.minsize(*config.UI_MIN_SIZE)
        self.app.configure(fg_color=config.COLOR_BG)

        self.voice_engine = get_voice_engine()
        self.speech_listener = get_speech_listener()
        self.utility_handler = get_utility_handler()

        self.is_busy = False
        self.core_angle = 0
        self.pulse_speed = 2
        self.pulse_intensity = 8

        self._build_ui()
        self._setup_voice_callbacks()
        self._setup_wake_word()

    def _build_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.app, fg_color=config.COLOR_BG, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        # Header
        self.header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header.pack(fill="x", padx=45, pady=(24, 0))

        self.title_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.title_frame.pack(side="left")

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="J A R V I S",
            font=("Segoe UI", 28, "bold"),
            text_color=config.COLOR_WHITE
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="PERSONAL ARTIFICIAL INTELLIGENCE",
            font=("Segoe UI", 10, "bold"),
            text_color=config.COLOR_MUTED
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Status badge
        self.system_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.system_frame.pack(side="right", pady=6)

        self.system_dot = ctk.CTkLabel(
            self.system_frame,
            text="●",
            font=("Segoe UI", 14),
            text_color=config.COLOR_GREEN
        )
        self.system_dot.pack(side="left", padx=(0, 6))

        self.system_text = ctk.CTkLabel(
            self.system_frame,
            text="SYSTEM ONLINE",
            font=("Segoe UI", 11, "bold"),
            text_color=config.COLOR_MUTED
        )
        self.system_text.pack(side="left")

        # Center Panel
        self.panel = ctk.CTkFrame(
            self.main_frame,
            fg_color=config.COLOR_PANEL,
            corner_radius=22,
            border_width=1,
            border_color="#101D24"
        )
        self.panel.pack(fill="both", expand=True, padx=45, pady=(15, 15))

        # Arc Reactor Core Canvas
        self.canvas = tk.Canvas(
            self.panel,
            width=260,
            height=260,
            bg=config.COLOR_PANEL,
            highlightthickness=0
        )
        self.canvas.pack(pady=(15, 0))

        # Outer ring
        self.canvas.create_oval(20, 20, 240, 240, outline=config.COLOR_CYAN_DARK, width=2)
        # Middle ring
        self.canvas.create_oval(45, 45, 215, 215, outline="#0B2731", width=2)
        # Inner ring
        self.canvas.create_oval(75, 75, 185, 185, outline=config.COLOR_CYAN, width=2)
        # Main core glow
        self.core = self.canvas.create_oval(105, 105, 155, 155, fill=config.COLOR_CYAN, outline="")
        # Dark center
        self.canvas.create_oval(115, 115, 145, 145, fill="#061017", outline="")

        # Status indicator
        self.status_label = ctk.CTkLabel(
            self.panel,
            text="SLEEPING",
            font=("Segoe UI", 22, "bold"),
            text_color=config.COLOR_CYAN
        )
        self.status_label.pack(pady=(5, 2))

        self.status_desc = ctk.CTkLabel(
            self.panel,
            text="Say 'Hey Jarvis' or click button to wake",
            font=("Segoe UI", 12),
            text_color=config.COLOR_MUTED
        )
        self.status_desc.pack(pady=(0, 10))

        # Last Command Box
        self.command_box = ctk.CTkFrame(
            self.panel,
            fg_color=config.COLOR_PANEL_2,
            corner_radius=12,
            border_width=1,
            border_color="#13232B"
        )
        self.command_box.pack(fill="x", padx=50, pady=(0, 12))

        self.command_title = ctk.CTkLabel(
            self.command_box,
            text="LAST COMMAND & RESPONSE",
            font=("Segoe UI", 9, "bold"),
            text_color=config.COLOR_MUTED
        )
        self.command_title.pack(anchor="w", padx=16, pady=(8, 0))

        self.last_command_label = ctk.CTkLabel(
            self.command_box,
            text="Ready for instruction.",
            font=("Segoe UI", 13),
            text_color=config.COLOR_WHITE,
            wraplength=700,
            justify="left"
        )
        self.last_command_label.pack(anchor="w", padx=16, pady=(3, 10))

        # Interaction Controls Frame
        self.controls_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=50, pady=(0, 12))

        # Wake Button
        self.talk_button = ctk.CTkButton(
            self.controls_frame,
            text="⚡  WAKE JARVIS",
            width=200,
            height=40,
            corner_radius=10,
            font=("Segoe UI", 12, "bold"),
            fg_color=config.COLOR_CYAN_DARK,
            hover_color="#0B5368",
            text_color=config.COLOR_WHITE,
            command=self.on_talk_clicked
        )
        self.talk_button.pack(side="left", padx=(0, 10))

        # Text input & send button for typing commands
        self.text_entry = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Or type a command / ask a question...",
            height=40,
            corner_radius=10,
            fg_color=config.COLOR_PANEL_2,
            border_color="#13232B",
            text_color=config.COLOR_WHITE,
            font=("Segoe UI", 12)
        )
        self.text_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.text_entry.bind("<Return>", lambda event: self.on_text_submitted())

        self.send_button = ctk.CTkButton(
            self.controls_frame,
            text="SEND",
            width=90,
            height=40,
            corner_radius=10,
            font=("Segoe UI", 11, "bold"),
            fg_color="#102530",
            hover_color="#183645",
            text_color=config.COLOR_CYAN,
            command=self.on_text_submitted
        )
        self.send_button.pack(side="right")

        # Telemetry Bar
        self.telemetry = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.telemetry.pack(fill="x", padx=45, pady=(0, 15))

        self.mic_label = ctk.CTkLabel(
            self.telemetry,
            text="●  MICROPHONE ONLINE",
            font=("Segoe UI", 10, "bold"),
            text_color=config.COLOR_GREEN
        )
        self.mic_label.pack(side="left")

        self.sep1 = ctk.CTkLabel(self.telemetry, text="   │   ", font=("Segoe UI", 10), text_color="#27343C")
        self.sep1.pack(side="left")

        self.cpu_label = ctk.CTkLabel(
            self.telemetry,
            text="CPU  0%",
            font=("Segoe UI", 10),
            text_color=config.COLOR_MUTED
        )
        self.cpu_label.pack(side="left")

        self.sep2 = ctk.CTkLabel(self.telemetry, text="   │   ", font=("Segoe UI", 10), text_color="#27343C")
        self.sep2.pack(side="left")

        self.memory_label = ctk.CTkLabel(
            self.telemetry,
            text="MEMORY  0%",
            font=("Segoe UI", 10),
            text_color=config.COLOR_MUTED
        )
        self.memory_label.pack(side="left")

        self.clock_label = ctk.CTkLabel(
            self.telemetry,
            text="",
            font=("Segoe UI", 10, "bold"),
            text_color=config.COLOR_MUTED
        )
        self.clock_label.pack(side="right")

    def _setup_voice_callbacks(self):
        # Hook status changes from voice engine and speech listener
        def on_tts_status(is_speaking: bool, text: str):
            if is_speaking:
                self.app.after(0, lambda: self.set_state("SPEAKING", "Speaking response...", config.COLOR_GREEN, 4))
            else:
                self.app.after(0, lambda: self.set_state("SLEEPING", "Say 'Hey Jarvis' or click button to wake", config.COLOR_CYAN, 2))

        self.voice_engine.register_status_callback(on_tts_status)

        def on_stt_status(status_text: str, state: str):
            if state == "LISTENING":
                self.app.after(0, lambda: self.set_state("LISTENING", "Listening to microphone...", config.COLOR_CYAN, 6))
            elif state == "THINKING":
                self.app.after(0, lambda: self.set_state("THINKING", "Processing command...", config.COLOR_YELLOW, 5))
            elif state in ("STANDBY", "SLEEPING"):
                self.app.after(0, lambda: self.set_state("SLEEPING", "Say 'Hey Jarvis' or click button to wake", config.COLOR_CYAN, 2))

        self.speech_listener.register_status_callback(on_stt_status)

    def _setup_wake_word(self):
        def on_wake(score):
            print(f"[UI] Wake word triggered! Score: {score:.2f}")
            self.app.after(0, self.trigger_voice_listen)

        self.wake_listener = WakeWordListener(on_wake_callback=on_wake)
        # Start wake word in background if enabled
        threading.Thread(target=self.wake_listener.start, daemon=True).start()

    def set_state(self, status: str, desc: str, color: str, pulse_speed: int = 2):
        """Thread-safe UI state updater."""
        self.status_label.configure(text=status, text_color=color)
        self.status_desc.configure(text=desc)
        self.pulse_speed = pulse_speed

        if status == "LISTENING":
            self.talk_button.configure(state="disabled", text="LISTENING...")
            self.mic_label.configure(text="●  MICROPHONE ACTIVE", text_color=config.COLOR_CYAN)
        elif status in ("STANDBY", "SLEEPING"):
            self.talk_button.configure(state="normal", text="⚡  WAKE JARVIS")
            self.mic_label.configure(text="●  VOICE WAKE ACTIVE ('Hey Jarvis')", text_color=config.COLOR_GREEN)
            self.is_busy = False

    def on_talk_clicked(self):
        """User clicked Wake Jarvis button."""
        if self.is_busy:
            return
        self.trigger_voice_listen()

    def trigger_voice_listen(self):
        """Wakes up Jarvis, plays chime, listens to microphone and executes command."""
        if self.is_busy:
            return
        self.is_busy = True
        self.wake_listener.pause()
        
        # Audio chime feedback
        play_wake_chime()

        self.set_state("LISTENING", "Listening for your command...", config.COLOR_CYAN, 6)

        def run_pipeline():
            try:
                query = self.speech_listener.listen()
                if query:
                    self.app.after(0, lambda: self.process_query(query))
                else:
                    self.app.after(0, lambda: self.set_state("SLEEPING", "Could not hear command, sleeping...", config.COLOR_CYAN))
            except Exception as e:
                print(f"[UI] Voice pipeline error: {e}")
                self.app.after(0, lambda: self.set_state("SLEEPING", f"Error: {e}", config.COLOR_RED))
            finally:
                self.is_busy = False
                self.wake_listener.resume()

        threading.Thread(target=run_pipeline, daemon=True).start()

    def on_text_submitted(self):
        """User typed a command into the text box."""
        text = self.text_entry.get().strip()
        if not text or self.is_busy:
            return

        self.text_entry.delete(0, tk.END)
        self.process_query(text)

    def process_query(self, query: str):
        """Dispatches command, updates UI, and speaks response."""
        self.is_busy = True
        self.set_state("THINKING", f"Executing: {query}", config.COLOR_YELLOW, 5)
        self.last_command_label.configure(text=f'"{query}"\nProcessing...')

        def execute():
            result: DispatchResult = dispatch_command(query)

            # Update UI on main thread
            def update_ui():
                display_text = f'"{query}"\n-> {result.response_text}'
                self.last_command_label.configure(text=display_text)
                if result.should_exit:
                    self.app.after(1500, self.app.destroy)

            self.app.after(0, update_ui)

            # Speak response
            if result.response_text:
                speak(result.response_text, block=True)

            self.is_busy = False

        threading.Thread(target=execute, daemon=True).start()

    def update_telemetry(self):
        """Periodic hardware and clock polling."""
        # Clock
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=now_str)

        # CPU & Memory
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            self.cpu_label.configure(text=f"CPU  {cpu:.0f}%")
            self.memory_label.configure(text=f"MEMORY  {mem:.0f}%")
        except Exception:
            pass

        self.app.after(1000, self.update_telemetry)

    def animate_core(self):
        """Pulsing core animation."""
        self.core_angle += self.pulse_speed
        pulse = (math.sin(math.radians(self.core_angle)) + 1) / 2
        size = int(45 + pulse * self.pulse_intensity)
        center = 130

        self.canvas.coords(
            self.core,
            center - size / 2,
            center - size / 2,
            center + size / 2,
            center + size / 2
        )
        self.app.after(40, self.animate_core)

    def greet_on_launch(self):
        """Greets user on startup in background."""
        def greet():
            greeting = self.utility_handler.get_greeting()
            speak(greeting, block=False)

        threading.Thread(target=greet, daemon=True).start()

    def run(self):
        self.update_telemetry()
        self.animate_core()
        self.greet_on_launch()
        self.app.mainloop()


def launch_gui():
    app = JarvisApp()
    app.run()
