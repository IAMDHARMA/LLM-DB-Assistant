# models.py
from pydantic import BaseModel
from typing import Optional

class DBConnectionCreate(BaseModel):
    name: str
    dialect: str  # 'postgres', 'mysql', 'sqlite'
    host: Optional[str]
    port: Optional[int]
    username: Optional[str]
    password: Optional[str]
    database: Optional[str]
    sqlite_path: Optional[str]

class AskRequest(BaseModel):
    connection_name: str
    question: str
    visualize: bool = False