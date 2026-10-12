# Financial Text-to-SQL Prototype — Member 2

## What this prototype demonstrates
1. A user asks a financial question in plain English.
2. Gemini generates SQLite SQL using the provided schema.
3. A safety gate permits only one read-only `SELECT`/`WITH` query.
4. The query executes against a local SQLite database.
5. The generated SQL and result rows are displayed.

## Setup (Windows / VS Code)
1. Install Python 3.10+.
2. Extract this folder and open it in VS Code.
3. Open Terminal in VS Code and run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use Command Prompt in VS Code or run:
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

4. Get a Gemini API key from Google AI Studio and enter it in the app's sidebar.
5. Try:
   - `What was Apple's revenue in 2024?`
   - `Compare Apple's revenue in 2022 and 2024.`
   - `Show Microsoft's revenue and net income for 2023.`

## Important limitations to say honestly
- The database contains a small illustrative sample, not a live SEC EDGAR/XBRL feed.
- The year field is a demo fiscal-year label; this prototype does not yet resolve fiscal vs calendar periods.
- The SQL validator is a basic demo guard, not production-grade security.
- Financial restatements, XBRL tag mapping, consolidated vs standalone selection, and robust evaluation are future work.

## Suggested next increments
- Add bounded retry using database error messages.
- Add a schema catalog/retriever.
- Add a small gold test set and measure execution success / answer correctness.
- Replace illustrative rows with a documented SEC-derived dataset.
