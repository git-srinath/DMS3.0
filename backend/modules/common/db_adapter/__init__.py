"""Database adapter package."""
from .registry import get_db_adapter

__all__ = ["get_db_adapter"]
