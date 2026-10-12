
import os
import re
import sqlite3
from pathlib import Path

import streamlit as st
from google import genai

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "financial_demo.db"
MODEL = "gemini-3.5-flash-lite"
MAX_RETRIES = 2

# --------------------------------------------------
# ILLUSTRATIVE DEMO DATA
# --------------------------------------------------

SAMPLE_ROWS = [
    ("Apple", 2022, "Revenue", 394328.0, "USD millions", "Consolidated"),
    ("Apple", 2023, "Revenue", 383285.0, "USD millions", "Consolidated"),
    ("Apple", 2024, "Revenue", 391035.0, "USD millions", "Consolidated"),
    ("Apple", 2022, "Net Income", 99803.0, "USD millions", "Consolidated"),
    ("Apple", 2023, "Net Income", 96995.0, "USD millions", "Consolidated"),
    ("Apple", 2024, "Net Income", 93736.0, "USD millions", "Consolidated"),
    ("Microsoft", 2022, "Revenue", 198270.0, "USD millions", "Consolidated"),
    ("Microsoft", 2023, "Revenue", 211915.0, "USD millions", "Consolidated"),
    ("Microsoft", 2024, "Revenue", 245122.0, "USD millions", "Consolidated"),
    ("Microsoft", 2022, "Net Income", 72738.0, "USD millions", "Consolidated"),
    ("Microsoft", 2023, "Net Income", 72361.0, "USD millions", "Consolidated"),
    ("Microsoft", 2024, "Net Income", 88136.0, "USD millions", "Consolidated"),
    ("NVIDIA", 2022, "Revenue", 26914.0, "USD millions", "Consolidated"),
    ("NVIDIA", 2023, "Revenue", 26974.0, "USD millions", "Consolidated"),
    ("NVIDIA", 2024, "Revenue", 60922.0, "USD millions", "Consolidated"),
    ("NVIDIA", 2022, "Net Income", 9752.0, "USD millions", "Consolidated"),
    ("NVIDIA", 2023, "Net Income", 4368.0, "USD millions", "Consolidated"),
    ("NVIDIA", 2024, "Net Income", 29760.0, "USD millions", "Consolidated"),
]

SCHEMA = """
Table: financials
Columns:
- company TEXT: company name
- fiscal_year INTEGER: fiscal year label in this demo dataset
- metric TEXT: financial metric (Revenue or Net Income)
- value REAL: financial amount
- unit TEXT: unit for the value (USD millions)
- reporting_type TEXT: Consolidated or Standalone

This is a small demonstration dataset, not a live SEC feed.
Only use the table and columns listed above.
"""

# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS financials (
                company TEXT NOT NULL,
                fiscal_year INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                reporting_type TEXT NOT NULL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM financials"
        ).fetchone()[0]

        if count == 0:
            conn.executemany(
                "INSERT INTO financials VALUES (?, ?, ?, ?, ?, ?)",
                SAMPLE_ROWS
            )

        conn.commit()


# --------------------------------------------------
# SQL VALIDATION
# --------------------------------------------------

def validate_sql(sql: str):
    """Basic demo safety checks; not production-grade SQL security."""

    sql = sql.strip()

    # Remove optional Markdown code fences.
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(r"\s*```$", "", sql).strip()

    if not sql:
        return False, "", "The model returned an empty query."

    # Allow at most one SQL statement.
    if ";" in sql.rstrip(";"):
        return False, sql, "Multiple SQL statements are not allowed."

    # Only SELECT and WITH queries are permitted.
    if not re.match(
        r"^(SELECT|WITH)\b",
        sql,
        flags=re.IGNORECASE
    ):
        return False, sql, "Only SELECT or WITH queries are allowed."

    forbidden = (
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|"
        r"ATTACH|DETACH|PRAGMA|VACUUM|TRIGGER)\b"
    )

    if re.search(forbidden, sql, flags=re.IGNORECASE):
        return False, sql, "The query contains a blocked SQL operation."

    return True, sql.rstrip(";"), ""


# --------------------------------------------------
# GEMINI TEXT-TO-SQL GENERATION AND CORRECTION
# --------------------------------------------------

def generate_sql(
    question: str,
    api_key: str,
    previous_sql: str = "",
    error_message: str = ""
):
    client = genai.Client(api_key=api_key)

    correction_context = ""

    if previous_sql and error_message:
        correction_context = f"""
The previous SQL attempt failed.

Previous SQL:
{previous_sql}

Validation or database error:
{error_message}

Correct the query using the error information.
Return a complete replacement SQL query only.
"""

    prompt = f"""
You generate SQLite SQL for a financial analytics demo.

Return exactly one SQL query, without Markdown or explanations.

Database schema:
{SCHEMA}

User question:
{question}

Rules:
- Use only the financials table.
- Use only the listed columns.
- Use exact metric strings when possible.
- Values are in USD millions.
- fiscal_year is a fiscal-year label in this demo.
- Use SELECT or WITH only.
- Never modify the database.
- Do not invent data, tables, or columns.
- For comparisons, include the requested years.
- Correct previous errors if error feedback is provided.

{correction_context}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()


# --------------------------------------------------
# SQL EXECUTION
# --------------------------------------------------

def run_sql(sql: str):
    # Query-only mode provides an additional read-only safeguard.
    uri = DB_PATH.resolve().as_uri() + "?mode=ro"

    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row

        # Enforce a read-only SQLite connection at the database level.
        conn.execute("PRAGMA query_only = ON")

        cursor = conn.execute(sql)

        rows = [dict(row) for row in cursor.fetchall()]
        columns = [
            description[0]
            for description in (cursor.description or [])
        ]

        return rows, columns


# --------------------------------------------------
# STREAMLIT USER INTERFACE
# --------------------------------------------------

st.set_page_config(
    page_title="Financial Text-to-SQL Prototype",
    page_icon="📊",
    layout="wide"
)

init_db()

st.title("📊 Financial Text-to-SQL Prototype")
st.caption("Member 2 — LLM & SQL Generation | Prototype v0.2")

st.warning(
    "Demo limitation: uses a small local sample dataset, "
    "not live SEC EDGAR/XBRL data. Values are illustrative."
)

with st.sidebar:
    st.subheader("Configuration")

    api_key = st.text_input(
        "Gemini API key",
        type="password",
        help="Enter your key from Google AI Studio. Do not share it."
    )

    st.write(f"Model: `{MODEL}`")
    st.write(f"Automatic correction retries: {MAX_RETRIES}")

    st.divider()

    st.subheader("Supported sample data")
    st.write("Companies: Apple, Microsoft, NVIDIA")
    st.write("Metrics: Revenue, Net Income")
    st.write("Fiscal-year labels: 2022–2024")
    st.write("Reporting type: Consolidated")
    st.caption("All amounts are in USD millions.")

examples = [
    "What was Apple's revenue in 2024?",
    "Compare Apple's revenue in 2022 and 2024.",
    "Show Microsoft's revenue and net income for 2023.",
    "Which company had the highest revenue in 2024?",
    "What was NVIDIA's net income in 2024?"
]

question = st.text_area(
    "Ask a financial question in plain English",
    value=examples[0],
    height=90
)

st.caption("Example questions:")
for example in examples:
    if st.button(example, key=f"example_{example}"):
        st.session_state["selected_question"] = example
        st.rerun()

# Restore selected example after rerun.
if "selected_question" in st.session_state:
    question = st.session_state["selected_question"]
    del st.session_state["selected_question"]

if st.button(
    "Generate SQL and Execute",
    type="primary",
    use_container_width=True
):
    if not api_key:
        st.error("Enter your Gemini API key in the sidebar first.")

    elif not question.strip():
        st.error("Enter a financial question first.")

    else:
        previous_sql = ""
        error_message = ""
        succeeded = False

        # One initial attempt plus at most two retries.
        for attempt in range(MAX_RETRIES + 1):

            # Step 1: Ask Gemini to generate or correct SQL.
            try:
                with st.spinner(
                    f"Generating SQL — attempt {attempt + 1} "
                    f"of {MAX_RETRIES + 1}..."
                ):
                    generated = generate_sql(
                        question=question.strip(),
                        api_key=api_key,
                        previous_sql=previous_sql,
                        error_message=error_message
                    )

                st.subheader(f"SQL attempt {attempt + 1}")
                st.code(generated, language="sql")

            except Exception as exc:
                st.error(f"Gemini request failed: {exc}")
                st.info(
                    "Check your API key, model availability, "
                    "network connection, and account quota."
                )
                break

            # Step 2: Validate before every execution.
            valid, clean_sql, reason = validate_sql(generated)

            if not valid:
                previous_sql = generated
                error_message = f"SQL validation failed: {reason}"

                if attempt < MAX_RETRIES:
                    st.warning(
                        f"{reason} Requesting a corrected query..."
                    )
                    continue

                st.error(
                    "The SQL did not pass validation after "
                    "the allowed attempts. It was not executed."
                )
                break

            st.success("Read-only SQL validation passed.")

            # Step 3: Execute SQL against the local database.
            try:
                with st.spinner("Executing SQL against SQLite..."):
                    rows, columns = run_sql(clean_sql)

            except sqlite3.Error as exc:
                previous_sql = clean_sql
                error_message = f"SQLite execution error: {exc}"

                if attempt < MAX_RETRIES:
                    st.warning(
                        "SQL execution failed. Sending the error "
                        "back to Gemini for correction..."
                    )
                    continue

                st.error(
                    "SQL execution failed after the allowed "
                    "attempts. No further retries will be made."
                )
                st.code(error_message)
                break

            # Step 4: Display results.
            st.subheader("Query results")

            if rows:
                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True
                )
                st.caption(f"{len(rows)} row(s) returned.")
            else:
                st.info(
                    "Query executed successfully but returned no rows."
                )

            with st.expander("Execution details"):
                st.write("Database: Local SQLite demo")
                st.write("Query status: Success")
                st.write("Successful attempt:", attempt + 1)
                st.write("Rows returned:", len(rows))
                st.write("Columns:", columns)

            succeeded = True
            break

        if not succeeded:
            st.info(
                "Review the error above. Successful SQL execution "
                "does not by itself guarantee financial correctness."
            )


# --------------------------------------------------
# SCHEMA AND SAMPLE DATA
# --------------------------------------------------

with st.expander("View demo database schema"):
    st.code(SCHEMA, language="text")

with st.expander("View sample data"):
    st.dataframe(
        SAMPLE_ROWS,
        use_container_width=True,
        hide_index=True
    )
