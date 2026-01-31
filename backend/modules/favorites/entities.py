"""Favorites domain entities.

Note: FavoriteTutor model is defined in models/students.py and exported via models/__init__.py.
This module re-exports it for backward compatibility.
"""

from models import FavoriteTutor

__all__ = ["FavoriteTutor"]
