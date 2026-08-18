import webbrowser
import urllib.parse
import re
import requests


class WebHandler:
    """
    Handles Web browsing, Google searches, YouTube, Wikipedia, and Weather queries.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "JarvisVirtualAssistant/1.0 (https://github.com; contact: assistant@local.dev)"
        }

    def open_url(self, url: str, site_name: str = "the website") -> tuple[bool, str]:
        """Opens a specified URL in default browser."""
        try:
            webbrowser.open(url)
            return True, f"Opening {site_name}, Sir."
        except Exception as e:
            return False, f"Could not open {site_name}. Error: {e}"

    def google_search(self, raw_query: str) -> tuple[bool, str]:
        """Cleans voice prompt and opens Google search."""
        # Clean trigger phrases
        clean = raw_query
        for trigger in [
            "google search for",
            "google search",
            "search google for",
            "search google",
            "search for",
            "search",
            "what is",
            "who is",
            "tell me about"
        ]:
            if clean.lower().startswith(trigger):
                clean = clean[len(trigger):].strip()
                break

        clean = clean.strip()
        if not clean:
            clean = raw_query

        encoded = urllib.parse.quote_plus(clean)
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        return True, f"Searching Google for {clean}, Sir."

    def youtube_search(self, raw_query: str) -> tuple[bool, str]:
        """Searches or plays video on YouTube."""
        clean = raw_query.lower()
        for trigger in [
            "play on youtube",
            "play",
            "search youtube for",
            "search on youtube",
            "youtube search for",
            "open youtube and play",
            "on youtube"
        ]:
            clean = clean.replace(trigger, "").strip()

        clean = clean.strip()
        if not clean:
            webbrowser.open("https://www.youtube.com")
            return True, "Opening YouTube, Sir."

        encoded = urllib.parse.quote_plus(clean)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return True, f"Playing {clean} on YouTube, Sir."

    def search_wikipedia(self, raw_query: str) -> tuple[bool, str]:
        """Searches Wikipedia using the official Wikipedia REST API."""
        clean = raw_query.lower()
        for trigger in [
            "wikipedia search for",
            "search wikipedia for",
            "wikipedia search",
            "search on wikipedia",
            "search about",
            "tell me about",
            "who was",
            "who is",
            "what was",
            "what is",
            "where was",
            "where is",
            "wikipedia",
        ]:
            if trigger in clean:
                clean = clean.replace(trigger, "").strip()

        clean = clean.strip()
        if not clean:
            return False, "What topic should I search on Wikipedia, Sir?"

        try:
            # 1. Try direct summary lookup (try title-cased first, then as-is)
            for candidate in [clean.title(), clean]:
                encoded_title = urllib.parse.quote(candidate.replace(" ", "_"))
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
                res = requests.get(summary_url, headers=self.headers, timeout=5)

                if res.status_code == 200:
                    data = res.json()
                    extract = data.get("extract")
                    if extract and data.get("type") != "disambiguation":
                        clean_summary = re.sub(r'\([^)]*\)', '', extract).strip()
                        sentences = [s.strip() for s in clean_summary.split('. ') if s.strip()]
                        short_summary = '. '.join(sentences[:2])
                        if short_summary and not short_summary.endswith('.'):
                            short_summary += '.'
                        return True, short_summary

            # 2. Search for closest matching article if direct lookup fails
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean)}&format=json"
            s_res = requests.get(search_url, headers=self.headers, timeout=5)
            if s_res.status_code == 200:
                s_data = s_res.json()
                results = s_data.get("query", {}).get("search", [])
                if results:
                    best_title = results[0]["title"]
                    best_title_encoded = urllib.parse.quote(best_title.replace(" ", "_"))
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{best_title_encoded}"
                    sum_res = requests.get(summary_url, headers=self.headers, timeout=5)
                    if sum_res.status_code == 200:
                        data = sum_res.json()
                        extract = data.get("extract")
                        if extract:
                            clean_summary = re.sub(r'\([^)]*\)', '', extract).strip()
                            sentences = [s.strip() for s in clean_summary.split('. ') if s.strip()]
                            short_summary = '. '.join(sentences[:2])
                            if short_summary and not short_summary.endswith('.'):
                                short_summary += '.'
                            return True, short_summary

            return False, f"Sorry Sir, I could not find information on '{clean}' on Wikipedia."

        except requests.exceptions.RequestException as e:
            return False, f"Sorry Sir, could not connect to Wikipedia: {e}"
        except Exception as ex:
            return False, f"Sorry Sir, an error occurred while searching Wikipedia: {ex}"

    def get_weather(self, city: str = "") -> tuple[bool, str]:
        """Fetches current weather for a city or current location using wttr.in."""
        try:
            target = urllib.parse.quote(city.strip()) if city and city.strip() else ""
            url = f"https://wttr.in/{target}?format=j1"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                current = data['current_condition'][0]
                temp_c = current['temp_C']
                desc = current['weatherDesc'][0]['value']
                humidity = current['humidity']
                loc_name = city if city else "your current location"
                msg = f"The weather in {loc_name} is currently {desc} at {temp_c}°C with {humidity}% humidity."
                return True, msg
        except Exception as e:
            print(f"[WebHandler] Weather error: {e}")
        return False, "Sorry Sir, I could not retrieve the weather information right now."


# Global instance
_web_handler_instance = None

def get_web_handler() -> WebHandler:
    global _web_handler_instance
    if _web_handler_instance is None:
        _web_handler_instance = WebHandler()
    return _web_handler_instance
