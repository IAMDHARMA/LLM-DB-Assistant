# sql_validator.py
import re

# Very simple blacklist-based validator. Strengthen for production.
DANGEROUS = re.compile(r"\b(DELETE|UPDATE|DROP|TRUNCATE|ALTER|CREATE|REPLACE|GRANT|REVOKE)\b", re.I)


def is_safe_sql(sql: str) -> bool:
    if DANGEROUS.search(sql):
        return False
    # Force single statement (no semicolons)
    if ';' in sql.strip().rstrip(';'):
        # allow trailing ; but no multiple statements
        parts = [p for p in sql.split(';') if p.strip()]
        if len(parts) > 1:
            return False
    return True