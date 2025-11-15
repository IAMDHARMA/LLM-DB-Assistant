# db_manager.py
import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Dict
from cryptography.fernet import Fernet
import os

# For demo only: key from env (persist securely in production)
FERNET_KEY = os.getenv('FERNET_KEY') or Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

# Simple in-memory store of encrypted connection strings per user (demo). Replace with DB.
CONNECTIONS: Dict[str, str] = {}


def build_uri(cfg: Dict) -> str:
    dialect = cfg['dialect']
    if dialect == 'sqlite':
        return f"sqlite:///{cfg['sqlite_path']}"
    if dialect == 'postgres':
        return f"postgresql+psycopg2://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    if dialect == 'mysql':
        return f"mysql+mysqlconnector://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    raise ValueError('Unsupported dialect')


def save_connection(name: str, cfg: Dict):
    uri = build_uri(cfg)
    token = fernet.encrypt(uri.encode()).decode()
    CONNECTIONS[name] = token


def get_engine(name: str):
    token = CONNECTIONS.get(name)
    if not token:
        raise KeyError('Connection not found')
    uri = fernet.decrypt(token.encode()).decode()
    engine = create_engine(uri, pool_pre_ping=True, pool_size=3, max_overflow=5)
    return engine


def test_connection(name: str):
    engine = get_engine(name)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    return True


def run_readonly_query(name: str, sql: str, params=None, timeout=30):
    # Caller must ensure SQL is validated (read-only)
    engine = get_engine(name)
    with engine.connect() as conn:
        result = conn.execution_options(stream_results=False).execute(text(sql), params or {})
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return columns, rows