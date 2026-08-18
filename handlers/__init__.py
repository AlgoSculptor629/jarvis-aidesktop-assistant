"""
JARVIS Command Handlers
Modular intent handling for Applications, Files, Web, System, Utilities, and Dispatching.
"""
from handlers.dispatcher import CommandDispatcher, dispatch_command

__all__ = ["CommandDispatcher", "dispatch_command"]
