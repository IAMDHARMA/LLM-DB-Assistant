import os
import google.generativeai as genai

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

PROMPT_TEMPLATE = """
You are a SQL assistant that returns ONLY a safe read-only SQL query.
Use ONLY the tables and columns given in the schema.
Return a single SELECT query.
No explanations.

Schema:
{schema}

Question:
{question}

SQL:
"""

def clean_sql(text: str) -> str:
    """Remove markdown fences like ```sql ... ```."""
    cleaned = text.strip()

    # Remove markdown code fences
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```sql", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

    # Remove stray backticks
    cleaned = cleaned.strip("`").strip()

    return cleaned

def generate_sql(schema: dict, question: str) -> str:
    schema_lines = []
    for t, cols in schema.items():
        schema_lines.append(f"{t}: {', '.join(cols)}")
    schema_text = "\n".join(schema_lines)

    prompt = PROMPT_TEMPLATE.format(schema=schema_text, question=question)

    if not API_KEY:
        print("⚠️ GOOGLE_API_KEY not found → using fallback SQL")
        return "SELECT 1 AS demo;"

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_sql = response.text
        return clean_sql(raw_sql)
    except Exception as e:
        print("Gemini ERROR →", e)
        return "SELECT 1 AS demo;"
