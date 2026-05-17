"""Message handler for pairenv.

Re-exports MessageHandler from router for backward compatibility and
convenience.
"""

from pairenv.router import MessageHandler

Handler = MessageHandler

__all__ = ["MessageHandler", "Handler"]
