# schema_fetcher.py
from sqlalchemy import inspect
from .db_manager import get_engine

SCHEMA_CACHE = {}


def fetch_schema(connection_name: str, refresh: bool = False) -> dict:
    if not refresh and connection_name in SCHEMA_CACHE:
        return SCHEMA_CACHE[connection_name]
    engine = get_engine(connection_name)
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        cols = inspector.get_columns(table_name)
        schema[table_name] = [c['name'] + ' (' + str(c.get('type')) + ')' for c in cols]
    SCHEMA_CACHE[connection_name] = schema
    return schema