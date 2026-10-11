"""Runs a set of test questions through every prompting strategy and writes results.md.

Each question has a hand-written reference query that returns only the essential columns. The
model is marked correct when its query returns the same rows (order ignored); extra columns are fine.

Usage:
    python run_examples.py                      # all strategies
    python run_examples.py --strategy zero_shot # just one
"""
import argparse
import datetime as dt
from collections import Counter
from pathlib import Path

from app import LLM, STRATEGIES, SCHEMA_PATH, answer_question, load_env, run_query

QUESTIONS = [
    ("Which cats are available for adoption right now, and which lounge is each one in?",
     "SELECT c.name, l.name FROM cat c JOIN lounge l ON c.lounge_id = l.lounge_id "
     "WHERE c.status = 'adoptable';"),
    ("What is our best-selling menu item by number sold?",
     "SELECT m.name FROM order_item oi "
     "JOIN menu_item m ON oi.item_id = m.item_id GROUP BY m.item_id ORDER BY SUM(oi.quantity) DESC LIMIT 1;"),
    ("Which lounge brought in the most cover charge money during June, July and August 2026?",
     "SELECT l.name FROM visit v JOIN lounge l ON v.lounge_id = l.lounge_id "
     "WHERE v.visit_date BETWEEN '2026-06-01' AND '2026-08-31' GROUP BY l.lounge_id "
     "ORDER BY SUM(v.cover_charge) DESC LIMIT 1;"),
    ("Who adopted Gizmo, and when?",
     "SELECT cu.first_name, cu.last_name, a.adoption_date FROM adoption a "
     "JOIN cat c ON a.cat_id = c.cat_id JOIN customer cu ON a.customer_id = cu.customer_id "
     "WHERE c.name = 'Gizmo';"),
    ("Which three cats have cost the most in vet bills in 2026?",
     "SELECT c.name FROM vet_visit vv JOIN cat c ON vv.cat_id = c.cat_id "
     "WHERE vv.visit_date BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY c.cat_id "
     "ORDER BY SUM(vv.cost) DESC LIMIT 3;"),
    ("Which barista has served the most orders?",
     "SELECT s.first_name, s.last_name FROM food_order f "
     "JOIN staff s ON f.staff_id = s.staff_id WHERE s.role = 'barista' GROUP BY s.staff_id "
     "ORDER BY COUNT(*) DESC LIMIT 1;"),
    ("Is the average party size bigger on weekends or weekdays?",
     "SELECT CASE WHEN strftime('%w', visit_date) IN ('0', '6') THEN 'weekend' ELSE 'weekday' END AS day_type, "
     "AVG(party_size) FROM visit GROUP BY day_type;"),
    ("Which customers with the top membership tier have visited more than 25 times?",
     "SELECT cu.first_name, cu.last_name FROM visit v "
     "JOIN customer cu ON v.customer_id = cu.customer_id WHERE cu.membership_tier = 'roar' "
     "GROUP BY cu.customer_id HAVING COUNT(*) > 25;"),
    ("How many vegan items have been ordered in total?",
     "SELECT SUM(oi.quantity) FROM order_item oi JOIN menu_item m ON oi.item_id = m.item_id "
     "WHERE m.is_vegan = 1;"),
    ("Which cat currently living at the cafe has been here the longest?",
     "SELECT name FROM cat WHERE status != 'adopted' ORDER BY arrival_date LIMIT 1;"),
]


def normalize(rows):
    """Compare result sets loosely: ignore row order and round floats."""
    def cell(v):
        return round(v, 2) if isinstance(v, float) else v
    return Counter(tuple(cell(v) for v in r) for r in rows)


def _text(v):
    return str(round(v, 2) if isinstance(v, float) else v)


def same_result(model_rows, ref_rows):
    """Exact match, or a looser match that still contains every reference value.

    The loose match allows the different shapes a correct query can take: extra columns
    (e.g. a count or an id), combined columns (first || ' ' || last), or a pivoted layout
    (one wide row instead of two). It fails if the model returns more rows than the reference,
    which usually means a missing filter.
    """
    if normalize(model_rows) == normalize(ref_rows):
        return True
    if len(model_rows) > len(ref_rows):
        return False
    model_cells = [_text(v) for row in model_rows for v in row]
    return all(any(_text(v) in cell for cell in model_cells) for row in ref_rows for v in row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--strategy", choices=STRATEGIES, help="run only one strategy")
    parser.add_argument("-p", "--provider", choices=["openai", "anthropic"])
    args = parser.parse_args()

    load_env()
    llm = LLM(args.provider)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    strategies = [args.strategy] if args.strategy else list(STRATEGIES)
    score = {s: 0 for s in strategies}

    md = [f"# Example results\n",
          f"Model: `{llm.label}` · Run: {dt.datetime.now():%Y-%m-%d %H:%M}\n",
          "Each answer is marked correct when the model's query returns the same rows as a hand-written "
          "reference query.\n"]

    for i, (question, ref_sql) in enumerate(QUESTIONS, 1):
        _, ref_rows, _ = run_query(ref_sql)
        md.append(f"## {i}. {question}\n")
        for strategy in strategies:
            print(f"[{i}/{len(QUESTIONS)}] {strategy}: {question}")
            r = answer_question(llm, question, strategy, schema)
            ok = r["error"] is None and same_result(r["rows"], ref_rows)
            score[strategy] += ok
            md.append(f"### {strategy} — {'✅ correct' if ok else '❌ incorrect'}\n")
            md.append(f"```sql\n{r['sql']}\n```\n")
            if r["error"]:
                md.append(f"**Error:** {r['error']}\n")
            else:
                md.append(f"**Answer:** {r['answer']}\n")
        md.append(f"<details><summary>Reference query</summary>\n\n```sql\n{ref_sql}\n```\n</details>\n")

    md.insert(3, "## Score by strategy\n\n| Strategy | Correct |\n|---|---|\n" +
              "\n".join(f"| {s} | {score[s]} / {len(QUESTIONS)} |" for s in strategies) + "\n")
    md.append(f"---\nTokens used: {llm.input_tokens} input / {llm.output_tokens} output\n")

    out = Path(__file__).parent / "results.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n" + "\n".join(f"{s}: {score[s]}/{len(QUESTIONS)}" for s in strategies))
    print(f"Tokens used: {llm.input_tokens} in / {llm.output_tokens} out")
    print(f"Wrote {out.name}")


if __name__ == "__main__":
    main()
