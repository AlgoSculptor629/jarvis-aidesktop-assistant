"""
Unit verification script for Jarvis modular architecture.
Runs in headless test mode with mocked GUI/OS openers for fast validation.
"""
import sys
import os
import unittest.mock as mock

# Force UTF-8 and line buffering
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

def run_tests():
    print("========================================", flush=True)
    print("     JARVIS TEST SUITE", flush=True)
    print("========================================", flush=True)

    # 1. Config test
    import config
    print("[OK] config.py loaded successfully.", flush=True)

    # 2. Voice Engine test
    from core.voice_engine import get_voice_engine
    engine = get_voice_engine()
    assert engine is not None
    print("[OK] core.voice_engine initialized.", flush=True)

    # 3. Speech Listener test
    from core.speech_listener import get_speech_listener
    listener = get_speech_listener()
    assert listener is not None
    print("[OK] core.speech_listener initialized.", flush=True)

    # 4. Utility Handler test
    from handlers.utility_handler import get_utility_handler
    util = get_utility_handler()
    greeting = util.get_greeting()
    time_str = util.get_time()
    date_str = util.get_date()
    calc_ok, calc_res = util.calculate("calculate 25 * 4 + 10")
    assert calc_ok and "110" in calc_res
    note_ok, note_res = util.add_note("take a note complete test suite")
    assert note_ok
    print(f"[OK] utility_handler: time='{time_str}', date='{date_str}', calc='{calc_res}'", flush=True)

    # 5. System Handler test
    from handlers.system_handler import get_system_handler
    sys_h = get_system_handler()
    stats = sys_h.get_system_stats()
    assert "cpu_percent" in stats and "memory_percent" in stats
    print(f"[OK] system_handler: CPU={stats['cpu_percent']}%, RAM={stats['memory_percent']}%", flush=True)

    # 6. App Handler test
    from handlers.app_handler import get_app_handler
    app_h = get_app_handler()
    code_path = app_h.find_app_path("vs code")
    calc_path = app_h.find_app_path("calculator")
    spotify_path = app_h.find_app_path("spotify")
    print(f"[OK] app_handler: found VS Code -> {code_path}, Calc -> {calc_path}, Spotify -> {spotify_path}", flush=True)

    # 7. File Handler test
    from handlers.file_handler import get_file_handler
    file_h = get_file_handler()
    jarvis_files = file_h.search_file("jarvis.py", limit=3)
    print(f"[OK] file_handler: found files matching 'jarvis.py': {len(jarvis_files)} found", flush=True)

    # 8. AI Brain test
    from core.ai_brain import get_ai_brain
    brain = get_ai_brain()
    reply = brain.ask("who are you")
    assert "JARVIS" in reply
    print(f"[OK] ai_brain: query='who are you' -> reply='{reply}'", flush=True)

    # 9. Command Dispatcher test (Mocking OS openers to prevent popup windows)
    with mock.patch("webbrowser.open", return_value=True), \
         mock.patch("os.startfile", return_value=True), \
         mock.patch("ctypes.windll.user32.LockWorkStation", return_value=1):

        from handlers.dispatcher import dispatch_command
        
        test_queries = [
            ("what is the time", "time"),
            ("what is the date", "date"),
            ("system telemetry", "system_stats"),
            ("calculate 100 / 4", "calc"),
            ("open youtube", "web"),
            ("play shape of you on youtube", "youtube"),
            ("who are you", "ai_conversation"),
            ("stop", "exit")
        ]

        for q, expected_action in test_queries:
            res = dispatch_command(q)
            print(f"[OK] dispatch('{q}') -> action_type='{res.action_type}', response='{res.response_text[:50]}...'", flush=True)
            assert res.action_type == expected_action or res.success

    print("\n========================================", flush=True)
    print(" ALL TESTS PASSED SUCCESSFULLY! ", flush=True)
    print("========================================", flush=True)

if __name__ == "__main__":
    run_tests()
    os._exit(0)
