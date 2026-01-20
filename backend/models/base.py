"""Base models and custom types for SQLAlchemy."""

import json

from sqlalchemy import Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()


class JSONEncodedArray(TypeDecorator):
    """
    Array type that works for both PostgreSQL (native ARRAY)
    and SQLite (JSON-encoded string).
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(Text))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if dialect.name == "postgresql":
            return value if value else []
        return json.loads(value) if value else []
