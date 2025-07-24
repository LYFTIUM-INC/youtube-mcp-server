"""
Error handler implementation for YouTube MCP server.

Re-exports the ErrorHandler from cache_manager for convenience.
"""

from .cache_manager import ErrorHandler

__all__ = ['ErrorHandler']