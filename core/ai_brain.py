import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import requests
import json
import warnings
import config


class AIBrain:
    """
    Intelligent Conversational AI Engine.
    Routes queries to Gemini, local Ollama, or an intelligent offline fallback.
    Uses lazy initialization for optimal startup speed.
    """
    def __init__(self):
        self.history = []
        self.max_history = 6
        self._gemini_model = None
        self._gemini_initialized = False

    def _init_gemini(self):
        if self._gemini_initialized:
            return

        self._gemini_initialized = True
        api_key = config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    import google.genai as genai_client
                    # Modern google.genai client
                    self._gemini_model = genai_client.Client(api_key=api_key)
                    self._use_new_client = True
                    print("[AIBrain] Google GenAI client initialized.")
                    return
                except ImportError:
                    pass

                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._gemini_model = genai.GenerativeModel(
                    model_name=config.GEMINI_MODEL,
                    system_instruction=config.SYSTEM_PROMPT
                )
                self._use_new_client = False
                print("[AIBrain] Google Gemini model initialized.")
        except Exception as e:
            print(f"[AIBrain] Gemini initialization failed: {e}")
            self._gemini_model = None

    def ask_gemini(self, prompt: str) -> str | None:
        """Query Google Gemini API."""
        if not self._gemini_initialized:
            self._init_gemini()

        if not self._gemini_model:
            return None

        try:
            if getattr(self, "_use_new_client", False):
                response = self._gemini_model.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt
                )
                reply = response.text.strip()
            else:
                chat = self._gemini_model.start_chat(
                    history=[
                        {"role": h["role"], "parts": [h["text"]]}
                        for h in self.history
                    ]
                )
                response = chat.send_message(prompt)
                reply = response.text.strip()

            clean_reply = reply.replace("**", "").replace("*", "").replace("`", "")
            return clean_reply
        except Exception as e:
            print(f"[AIBrain] Gemini API error: {e}")
            return None

    def ask_ollama(self, prompt: str) -> str | None:
        """Query local Ollama instance."""
        try:
            url = f"{config.OLLAMA_HOST}/api/generate"
            payload = {
                "model": config.OLLAMA_MODEL,
                "prompt": f"{config.SYSTEM_PROMPT}\n\nUser: {prompt}\nJarvis:",
                "stream": False
            }
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                reply = data.get("response", "").strip()
                clean_reply = reply.replace("**", "").replace("*", "")
                return clean_reply
        except Exception:
            pass
        return None

    def ask_offline_fallback(self, prompt: str) -> str:
        """Smart responses if internet AI keys (Gemini) are unconfigured."""
        p = prompt.lower().strip()

        # Common greetings & identity
        if any(w in p for w in ["who are you", "what are you", "your name"]):
            return "I am JARVIS, your personal artificial intelligence desktop assistant."
        elif any(w in p for w in ["how are you", "how are you doing"]):
            return "I am operating at peak efficiency, Sir. All systems and telemetry are nominal."
        elif any(w in p for w in ["thank you", "thanks", "appreciate it"]):
            return "You are very welcome, Sir. Always happy to assist."
        elif any(w in p for w in ["hello", "hi jarvis", "hey jarvis", "good morning", "good evening", "good afternoon"]):
            return "Greetings Sir. How can I assist you right now?"
        elif any(w in p for w in ["what can you do", "help me", "your capabilities", "commands"]):
            return "I can launch applications, search local files, search Google & YouTube, check Wikipedia, control volume, monitor system telemetry, and answer questions."

        # Quick factual lookup via Wikipedia REST API fallback
        try:
            from handlers.web_handler import get_web_handler
            wh = get_web_handler()
            # Clean prompt for wiki query
            wiki_topic = p
            for prefix in ["who is", "who was", "what is", "what was", "tell me about", "explain", "define"]:
                if wiki_topic.startswith(prefix):
                    wiki_topic = wiki_topic[len(prefix):].strip()
                    break
            if wiki_topic and len(wiki_topic) > 2:
                ok, summary = wh.search_wikipedia(wiki_topic)
                if ok and summary and "Could not find" not in summary:
                    return summary
        except Exception:
            pass

        return (
            f"I understood your request: '{prompt}'. "
            "To unlock full generative conversation and deep reasoning, add your free GEMINI_API_KEY in config.py or environment."
        )

    def ask(self, prompt: str) -> str:
        """
        Ask Jarvis a natural language question.
        Attempts Gemini -> Ollama -> Offline Fallback.
        """
        if not prompt or not prompt.strip():
            return "I am listening, Sir."

        prompt_clean = prompt.strip()

        # 1. Try Gemini
        answer = self.ask_gemini(prompt_clean)

        # 2. Try Local Ollama
        if not answer:
            answer = self.ask_ollama(prompt_clean)

        # 3. Offline Fallback
        if not answer:
            answer = self.ask_offline_fallback(prompt_clean)

        # Record history
        self.history.append({"role": "user", "text": prompt_clean})
        self.history.append({"role": "model", "text": answer})
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]

        return answer


# Global instance
_brain_instance = None

def get_ai_brain() -> AIBrain:
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AIBrain()
    return _brain_instance
