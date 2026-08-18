import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import config


class FileHandler:
    """
    Fast and safe file locator for Windows.
    Applies directory exclusions, depth limits, and permission checks.
    """
    def __init__(self):
        self.search_dirs = [d for d in config.SEARCH_DIRECTORIES if d.exists()]
        self.ignored_dirs = config.SEARCH_IGNORE_DIRS
        self.max_depth = config.MAX_SEARCH_DEPTH

    def search_file(self, filename: str, limit: int = 5) -> list[str]:
        """
        Searches for files matching filename across configured user folders.
        Returns a list of matching absolute file paths.
        """
        if not filename or not filename.strip():
            return []

        filename_clean = filename.strip().lower()
        matches = []

        for base_dir in self.search_dirs:
            base_depth = len(base_dir.parts)

            try:
                for root, dirs, files in os.walk(base_dir):
                    # Filter out ignored directories in-place to prevent traversing them
                    dirs[:] = [
                        d for d in dirs
                        if d not in self.ignored_dirs
                        and not d.startswith(".")
                        and not d.startswith("$")
                    ]

                    # Enforce max depth limit
                    current_depth = len(Path(root).parts) - base_depth
                    if current_depth > self.max_depth:
                        dirs.clear()
                        continue

                    for file in files:
                        if filename_clean in file.lower():
                            full_path = os.path.join(root, file)
                            matches.append(full_path)
                            if len(matches) >= limit:
                                return matches
            except (PermissionError, OSError):
                continue

        return matches

    def find_and_open_file(self, filename: str) -> tuple[bool, str]:
        """Finds a file and opens it with the default Windows application."""
        matches = self.search_file(filename, limit=1)

        if matches:
            target = matches[0]
            try:
                os.startfile(target)
                basename = os.path.basename(target)
                return True, f"Found and opened {basename}, Sir."
            except Exception as e:
                return False, f"Found the file at {target}, but could not open it: {e}"
        else:
            return False, f"Sorry Sir, I could not find any file named '{filename}'."


# Global instance & legacy helper
_file_handler_instance = None

def get_file_handler() -> FileHandler:
    global _file_handler_instance
    if _file_handler_instance is None:
        _file_handler_instance = FileHandler()
    return _file_handler_instance

def searchFile(filename: str) -> str | None:
    """Backwards-compatible searchFile function."""
    handler = get_file_handler()
    results = handler.search_file(filename, limit=1)
    return results[0] if results else None
