"""Learned Context SDK - Python Client

A wrapper around the Letta client that provides learned context capabilities.
"""

from .client import LearnedContextClient, SubconsciousAgent, ConversationalMemoryClient, Run
from .database import SubconsciousDatabase, Message, File, MessageCreate, DatabaseStats
from .prompt_formatter import format_messages, format_files

__all__ = [
    "LearnedContextClient",
    "SubconsciousAgent", 
    "ConversationalMemoryClient",
    "Run",
    "SubconsciousDatabase",
    "Message",
    "File", 
    "MessageCreate",
    "DatabaseStats",
    "format_messages",
    "format_files",
]

__version__ = "0.1.0"