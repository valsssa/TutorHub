"""
Value objects for the users domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attributes, not by ID.
"""

from typing import NewType

# Type aliases for IDs - provides type safety without runtime overhead
UserId = NewType("UserId", int)

# User preference value types
Currency = NewType("Currency", str)
Timezone = NewType("Timezone", str)
Language = NewType("Language", str)

# Avatar related
AvatarKey = NewType("AvatarKey", str)
