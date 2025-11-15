# main.py
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .model import DBConnectionCreate, AskRequest
from .db_manager import save_connection, test_connection, run_readonly_query
from .schema_fetcher import fetch_schema
from .llm_agent import generate_sql
from .sql_validator import is_safe_sql

# basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm-db-assistant")

app = FastAPI(title="LLM DB Assistant")


@app.post("/connect")
def connect(cfg: DBConnectionCreate):
    """
    Save a connection config (encrypted in memory for demo),
    then test the connection.
    NOTE: Connections are stored in-memory for this demo; re-run /connect
    after restarting the server or use persistent storage (recommended).
    """
    save_connection(cfg.name, cfg.dict())
    try:
        test_connection(cfg.name)
    except Exception as e:
        # remove saved connection if test fails (optional)
        raise HTTPException(status_code=400, detail=f"Connection test failed: {e}")
    return {"status": "connected", "name": cfg.name}


@app.get("/schema/{connection_name}")
def get_schema(connection_name: str):
    try:
        schema = fetch_schema(connection_name)
    except KeyError as e:
        # connection not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schema


@app.post("/ask")
def ask(req: AskRequest):
    """
    1) fetch schema (from cache or DB)
    2) ask LLM to generate SQL
    3) validate SQL safety
    4) execute read-only query and return results
    """
    # 1) schema
    try:
        schema = fetch_schema(req.connection_name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Connection not found: {req.connection_name}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch schema: {e}")

    # 2) generate SQL
    try:
        sql = generate_sql(schema, req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation error: {e}")

    if not sql or not isinstance(sql, str):
        raise HTTPException(status_code=500, detail="LLM did not return valid SQL.")

    logger.info("Generated SQL: %s", sql)

    # 3) safety check
    try:
        if not is_safe_sql(sql):
            raise HTTPException(status_code=400, detail="Generated SQL failed safety checks.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL safety check failed: {e}")

    # 4) execute
    try:
        result = run_readonly_query(req.connection_name, sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution error: {e}")

    # support both return shapes:
    # old: (cols, rows)
    # new: {"columns": [...], "rows": [...]}
    if isinstance(result, dict):
        cols = result.get("columns", [])
        rows = result.get("rows", [])
    elif isinstance(result, (list, tuple)) and len(result) == 2:
        cols, rows = result
    else:
        # last resort: try to coerce to JSON-able form
        raise HTTPException(status_code=500, detail="Unexpected query result format")

    # Ensure columns is list (not e.g. a SQLAlchemy KeyView)
    try:
        columns_list = list(cols)
    except Exception:
        columns_list = cols

    return {
        "sql": sql,
        "columns": columns_list,
        "rows": rows,
    }
