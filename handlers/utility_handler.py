import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution or IDE resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import datetime
import re
import ast
import operator
import config


class UtilityHandler:
    """
    Handles Date, Time, dynamic greetings, math calculations, and notes.
    """
    def __init__(self):
        self.notes_file = config.NOTES_FILE

    def get_time(self) -> str:
        """Returns the current formatted time."""
        str_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"Sir, the time is {str_time}."

    def get_date(self) -> str:
        """Returns the current formatted date."""
        today = datetime.datetime.now().strftime("%d %B %Y")
        day_name = datetime.datetime.now().strftime("%A")
        return f"Sir, today is {day_name}, {today}."

    def get_greeting(self) -> str:
        """Dynamic greeting based on current hour."""
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            greeting = "Good Morning!"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"

        return f"{greeting} Jarvis here. Please tell me how may I help you."

    def calculate(self, expression_text: str) -> tuple[bool, str]:
        """Safely evaluates basic math queries like 'calculate 25 plus 40'."""
        clean = expression_text.lower()
        for prefix in ["calculate", "what is", "compute", "solve", "math"]:
            clean = clean.replace(prefix, "")

        # Word to symbol replacements
        replacements = {
            "plus": "+",
            "add": "+",
            "minus": "-",
            "subtract": "-",
            "multiplied by": "*",
            "times": "*",
            "into": "*",
            "x": "*",
            "divided by": "/",
            "divide by": "/",
            "over": "/",
            "to the power of": "**",
            "power": "**",
            "percent of": "/100*",
        }
        for word, sym in replacements.items():
            clean = clean.replace(word, sym)

        # Remove any character not part of standard math
        clean_expr = re.sub(r'[^0-9+\-*/().^]', '', clean).strip()

        if not clean_expr:
            return False, "Could not understand the calculation."

        try:
            # Safe evaluation using AST
            node = ast.parse(clean_expr, mode='eval')
            
            def eval_node(n):
                if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                    return n.value
                elif isinstance(n, ast.BinOp):
                    ops = {
                        ast.Add: operator.add,
                        ast.Sub: operator.sub,
                        ast.Mult: operator.mul,
                        ast.Div: operator.truediv,
                        ast.Pow: operator.pow,
                    }
                    op_type = type(n.op)
                    if op_type in ops:
                        return ops[op_type](eval_node(n.left), eval_node(n.right))
                elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
                    return -eval_node(n.operand)
                raise ValueError("Unsupported operation")

            result = eval_node(node.body)
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return True, f"The result is {result}."
        except Exception:
            return False, "Sorry Sir, I could not evaluate that mathematical expression."

    def add_note(self, note_text: str) -> tuple[bool, str]:
        """Saves a quick note to disk."""
        clean = note_text
        for prefix in ["take a note", "write note", "note down", "make a note", "remember that"]:
            if clean.lower().startswith(prefix):
                clean = clean[len(prefix):].strip()
                break

        if not clean:
            return False, "What would you like me to note down, Sir?"

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.notes_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {clean}\n")
            return True, f"I have noted that down, Sir."
        except Exception as e:
            return False, f"Could not save note: {e}"

    def read_notes(self) -> tuple[bool, str]:
        """Reads back saved notes."""
        if not self.notes_file.exists():
            return True, "You do not have any saved notes, Sir."

        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                return True, "Your notes file is empty, Sir."

            # Read last 3 notes
            recent = [line.strip() for line in lines[-3:] if line.strip()]
            summary = " Here are your most recent notes: " + " ... ".join(recent)
            return True, summary
        except Exception as e:
            return False, f"Could not read notes: {e}"


# Global instance
_utility_handler_instance = None

def get_utility_handler() -> UtilityHandler:
    global _utility_handler_instance
    if _utility_handler_instance is None:
        _utility_handler_instance = UtilityHandler()
    return _utility_handler_instance
