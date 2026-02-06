"""
Value objects for the favorites domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attributes, not by ID.
"""

from typing import NewType

# Type aliases for IDs - provides type safety without runtime overhead
FavoriteId = NewType("FavoriteId", int)
UserId = NewType("UserId", int)
TutorProfileId = NewType("TutorProfileId", int)
