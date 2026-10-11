"""Whisker Lounge Cat Cafe - ask questions about the cafe in plain English.

Flow for each question:
  1. Send the question + database schema to the LLM and ask for a SQLite query.
  2. Run that query against cat_cafe.db (read-only).
  3. Send the question + query + results back to the LLM and ask for a plain-English answer.

Usage:
    python app.py                                  # interactive, default strategy
    python app.py --strategy zero_shot             # pick a prompting strategy
    python app.py -q "Which cats can be adopted?"  # ask one question and exit
"""
import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "cat_cafe.db"
SCHEMA_PATH = HERE / "schema.sql"
MAX_RESULT_ROWS = 100   # rows sent back to the LLM for the answer step


# ---------------------------------------------------------------------------
# Configuration (.env)
# ---------------------------------------------------------------------------

def load_env(path=HERE / ".env"):
    """Minimal .env reader so no extra package is needed. Real env vars win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# ---------------------------------------------------------------------------
# LLM providers
# ---------------------------------------------------------------------------

class LLM:
    """Wraps OpenAI or Anthropic behind one ask() method and tracks token usage."""

    def __init__(self, provider=None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
        self.input_tokens = 0
        self.output_tokens = 0

        if self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY", "")
            if not key or key.startswith("sk-your"):
                sys.exit("OPENAI_API_KEY is missing. Copy .env.example to .env and paste your key in.")
            from openai import OpenAI
            self.client = OpenAI(api_key=key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        elif self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY", "")
            if not key or key.startswith("sk-ant-your"):
                sys.exit("ANTHROPIC_API_KEY is missing. Add it to .env.")
            import anthropic
            self.client = anthropic.Anthropic(api_key=key)
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
        else:
            sys.exit(f"Unknown LLM_PROVIDER '{self.provider}'. Use 'openai' or 'anthropic'.")

    def ask(self, system, user):
        if self.provider == "openai":
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
            )
            if resp.usage:
                self.input_tokens += resp.usage.prompt_tokens
                self.output_tokens += resp.usage.completion_tokens
            return resp.choices[0].message.content or ""
        else:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            self.input_tokens += resp.usage.input_tokens
            self.output_tokens += resp.usage.output_tokens
            return "".join(b.text for b in resp.content if b.type == "text")

    @property
    def label(self):
        return f"{self.provider}:{self.model}"


# ---------------------------------------------------------------------------
# Prompting strategies (from Chang & Fosler-Lussier 2023, arXiv:2305.11853)
# ---------------------------------------------------------------------------

SQL_SYSTEM = ("You translate questions into SQLite queries. Reply with exactly one SQLite SELECT "
              "statement and nothing else - no explanation, no markdown.")

# Single-domain: demonstration question/SQL pairs from THIS database.
SINGLE_DOMAIN_EXAMPLES = [
    ("Which cats are Siamese?",
     "SELECT name FROM cat WHERE breed = 'Siamese';"),
    ("How many visits did each lounge have in March 2026?",
     "SELECT l.name, COUNT(*) AS visits\n"
     "FROM visit v JOIN lounge l ON v.lounge_id = l.lounge_id\n"
     "WHERE v.visit_date BETWEEN '2026-03-01' AND '2026-03-31'\n"
     "GROUP BY l.name;"),
]

# Cross-domain: demonstrations from a DIFFERENT database (a small library).
CROSS_DOMAIN_SCHEMA = """CREATE TABLE author (author_id INTEGER PRIMARY KEY, name TEXT, country TEXT);
CREATE TABLE book (book_id INTEGER PRIMARY KEY, title TEXT, author_id INTEGER REFERENCES author(author_id), published_year INTEGER, genre TEXT);
CREATE TABLE member (member_id INTEGER PRIMARY KEY, name TEXT, join_date DATE);
CREATE TABLE loan (loan_id INTEGER PRIMARY KEY, book_id INTEGER REFERENCES book(book_id), member_id INTEGER REFERENCES member(member_id), loan_date DATE, return_date DATE);"""

CROSS_DOMAIN_EXAMPLES = [
    ("Which books were written by authors from Japan?",
     "SELECT b.title FROM book b JOIN author a ON b.author_id = a.author_id WHERE a.country = 'Japan';"),
    ("Which member borrowed the most books in 2025?",
     "SELECT m.name, COUNT(*) AS loans\n"
     "FROM loan l JOIN member m ON l.member_id = m.member_id\n"
     "WHERE l.loan_date BETWEEN '2025-01-01' AND '2025-12-31'\n"
     "GROUP BY m.member_id ORDER BY loans DESC LIMIT 1;"),
]

STRATEGIES = {
    "zero_shot": "Schema + question only, no examples.",
    "single_domain": "Schema + example questions/SQL from the cat cafe database itself.",
    "cross_domain": "Example questions/SQL from a different (library) database, then the cat cafe schema + question.",
}
DEFAULT_STRATEGY = "single_domain"


def build_sql_prompt(strategy, schema, question):
    def block(schema_text, pairs, q):
        out = f"### SQLite database schema:\n{schema_text}\n\n"
        for ex_q, ex_sql in pairs:
            out += f"### Question: {ex_q}\n{ex_sql}\n\n"
        out += f"### Question: {q}\n"
        return out

    if strategy == "zero_shot":
        return block(schema, [], question)
    if strategy == "single_domain":
        return block(schema, SINGLE_DOMAIN_EXAMPLES, question)
    if strategy == "cross_domain":
        demo = block(CROSS_DOMAIN_SCHEMA, CROSS_DOMAIN_EXAMPLES[:-1], CROSS_DOMAIN_EXAMPLES[-1][0])
        demo += CROSS_DOMAIN_EXAMPLES[-1][1] + "\n\n"
        return demo + block(schema, [], question)
    raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {', '.join(STRATEGIES)}")


ANSWER_SYSTEM = ("You are the friendly assistant for the Whisker Lounge Cat Cafe. Answer the "
                 "customer's or staff member's question in plain, conversational English using only "
                 "the query results provided. Do not mention SQL, tables or queries. If the results "
                 "are empty, say you couldn't find anything. Keep it to a few sentences.")


def build_answer_prompt(question, sql, columns, rows, truncated):
    lines = [" | ".join(columns)] + [" | ".join("" if v is None else str(v) for v in r) for r in rows]
    note = f"\n(Only the first {len(rows)} rows are shown.)" if truncated else ""
    return (f"Question: {question}\n\nSQL used: {sql}\n\n"
            f"Results ({len(rows)} rows):\n" + "\n".join(lines) + note)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def extract_sql(text):
    """Pull the SQL out of the model's reply (handles ```sql fences and extra chatter)."""
    fence = re.search(r"```(?:sql|sqlite)?\s*(.*?)```", text, re.S | re.I)
    if fence:
        text = fence.group(1)
    match = re.search(r"\b(WITH|SELECT)\b.*", text, re.S | re.I)
    sql = match.group(0) if match else text
    return sql.strip().split(";")[0].strip() + ";"


def run_query(sql):
    """Run a query read-only. Returns (columns, rows, truncated)."""
    if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.I):
        raise ValueError("Only SELECT queries are allowed.")
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    try:
        cur = conn.execute(sql)
        columns = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(MAX_RESULT_ROWS + 1)
    finally:
        conn.close()
    truncated = len(rows) > MAX_RESULT_ROWS
    return columns, rows[:MAX_RESULT_ROWS], truncated


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def answer_question(llm, question, strategy=DEFAULT_STRATEGY, schema=None):
    """Returns a dict with the sql, rows, answer and any error."""
    schema = schema or SCHEMA_PATH.read_text(encoding="utf-8")
    result = {"question": question, "strategy": strategy, "sql": None,
              "columns": [], "rows": [], "answer": None, "error": None}
    raw = llm.ask(SQL_SYSTEM, build_sql_prompt(strategy, schema, question))
    result["sql"] = extract_sql(raw)
    try:
        columns, rows, truncated = run_query(result["sql"])
    except Exception as e:  # bad SQL from the model
        result["error"] = f"{type(e).__name__}: {e}"
        return result
    result["columns"], result["rows"] = columns, rows
    result["answer"] = llm.ask(ANSWER_SYSTEM,
                               build_answer_prompt(question, result["sql"], columns, rows, truncated)).strip()
    return result


def print_result(r, show_rows=True):
    print(f"\nSQL ({r['strategy']}):\n  " + r["sql"].replace("\n", "\n  "))
    if r["error"]:
        print(f"\nThe query failed: {r['error']}")
        return
    if show_rows:
        print(f"\nRows returned: {len(r['rows'])}")
        for row in r["rows"][:5]:
            print("  ", row)
        if len(r["rows"]) > 5:
            print("   ...")
    print(f"\nAnswer: {r['answer']}\n")


def main():
    parser = argparse.ArgumentParser(description="Ask the cat cafe database questions in plain English.")
    parser.add_argument("-q", "--question", help="ask one question and exit")
    parser.add_argument("-s", "--strategy", default=DEFAULT_STRATEGY, choices=STRATEGIES)
    parser.add_argument("-p", "--provider", choices=["openai", "anthropic"], help="overrides LLM_PROVIDER")
    args = parser.parse_args()

    load_env()
    if not DB_PATH.exists():
        sys.exit("cat_cafe.db not found. Run: python setup_db.py")
    llm = LLM(args.provider)
    strategy = args.strategy

    if args.question:
        try:
            print_result(answer_question(llm, args.question, strategy))
        except Exception as e:
            sys.exit(f"Something went wrong talking to the model: {e}")
    else:
        print(f"Whisker Lounge Cat Cafe  ({llm.label}, strategy: {strategy})")
        print("Ask a question, or type ':strategy <name>' to switch, ':quit' to exit.")
        print("Strategies: " + ", ".join(STRATEGIES) + "\n")
        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question:
                continue
            if question in (":q", ":quit", "exit", "quit"):
                break
            if question.startswith(":strategy"):
                name = question.split(maxsplit=1)[-1]
                if name in STRATEGIES:
                    strategy = name
                    print(f"Strategy is now {strategy}.\n")
                else:
                    print("Choose one of: " + ", ".join(STRATEGIES) + "\n")
                continue
            try:
                print_result(answer_question(llm, question, strategy))
            except Exception as e:
                print(f"Something went wrong talking to the model: {e}\n")

    print(f"Tokens used this session: {llm.input_tokens} in / {llm.output_tokens} out")


if __name__ == "__main__":
    main()
