"""
run_pipeline.py

1. Loads the raw distributor CSVs into a SQLite database (as plain text)
2. Runs the SQL files in /sql in order
3. Exports the result tables to data/output/ (ready for Power BI or Excel)
4. Checks the results against the answer key and prints a short summary
"""
import csv
import glob
import os
import sqlite3

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "output")
KEY = os.path.join(ROOT, "data", "answer_key")
DB = os.path.join(ROOT, "data", "territory_transition.db")

RAW_TABLES = {
    "raw_old_sales": "distributor_a_sales.csv",
    "raw_new_sales": "distributor_b_sales.csv",
    "raw_old_stores": "distributor_a_stores.csv",
    "raw_new_stores": "distributor_b_stores.csv",
    "raw_old_item_xref": "distributor_a_item_xref.csv",
    "raw_product_master": "product_master.csv",
}
EXPORTS = ["weekly_compare", "clean_sales", "dq_issues", "store_match_report"]


def load_csv(con, table, path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"CREATE TABLE {table} ({', '.join(c + ' TEXT' for c in header)})")
    con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(header))})", body)


def export(con, table):
    cur = con.execute(f"SELECT * FROM {table}")
    with open(os.path.join(OUT, f"{table}.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([d[0] for d in cur.description])
        w.writerows(cur.fetchall())


def main():
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)

    for table, file in RAW_TABLES.items():
        load_csv(con, table, os.path.join(RAW, file))
    for sql_file in sorted(glob.glob(os.path.join(ROOT, "sql", "*.sql"))):
        with open(sql_file) as f:
            con.executescript(f.read())
        print(f"ran {os.path.basename(sql_file)}")
    con.commit()
    for t in EXPORTS:
        export(con, t)

    # ---------- Summary ----------
    print("\nISSUES FOUND")
    for name, sev, n, cases in con.execute(
            "SELECT check_name, severity, COUNT(*), ROUND(SUM(cases_impacted)) FROM dq_issues "
            "GROUP BY check_name, severity ORDER BY CASE severity WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 "
            "WHEN 'LOW' THEN 3 ELSE 4 END"):
        print(f"  {sev:<6} {name:<22} count={n:<4} cases={cases}")

    # ---------- Check against the answer key ----------
    true = {r["week_ending"]: float(r["true_cases"]) for r in csv.DictReader(open(os.path.join(KEY, "true_weekly_cases.csv")))}
    comp = {r[0]: (r[1], r[2]) for r in con.execute("SELECT week_ending, raw_cases, clean_cases FROM weekly_compare")}
    raw_err = sum(abs(comp[w][0] - true[w]) for w in true) / sum(true.values())
    clean_err = sum(abs(comp[w][1] - true[w]) for w in true) / sum(true.values())
    worst_raw = max(true, key=lambda w: abs(comp[w][0] - true[w]) / true[w])
    print("\nACCURACY VS. ANSWER KEY")
    print(f"  Raw data:   total weekly error {raw_err:.1%} | worst week {worst_raw} off by "
          f"{(comp[worst_raw][0] - true[worst_raw]) / true[worst_raw]:+.0%}")
    print(f"  Clean data: total weekly error {clean_err:.1%}")
    for w in true:
        if abs(comp[w][1] - true[w]) > 0.5:
            print(f"    {w}: clean {comp[w][1]:.0f} vs true {true[w]:.0f} ({(comp[w][1] - true[w]) / true[w]:+.1%})")

    key = list(csv.DictReader(open(os.path.join(KEY, "true_store_map.csv"))))
    true_pairs = {(k["old_store_id"], k["new_store_id"]) for k in key if k["old_store_id"] and k["new_store_id"]}
    found = set(con.execute("SELECT old_id, new_id FROM store_match").fetchall())
    correct = len(found & true_pairs)
    wrong = len(found - true_pairs)
    print(f"\nSTORE MATCHING: {correct} of {len(true_pairs)} same-store pairs linked automatically, "
          f"{wrong} wrong links, {len(true_pairs) - correct} left for review")
    con.close()


if __name__ == "__main__":
    main()
