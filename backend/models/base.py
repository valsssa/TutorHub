"""Base models and custom types for SQLAlchemy."""

import json

from sqlalchemy import Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB as PG_JSONB
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


class JSONType(TypeDecorator):
    """
    JSONB type that works for both PostgreSQL (native JSONB)
    and SQLite (JSON-encoded string).

    Use this for JSON columns to get proper type support and query capabilities
    in PostgreSQL while maintaining SQLite compatibility for tests.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
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
            return None
        if dialect.name == "postgresql":
            return value
        return json.loads(value) if value else None
