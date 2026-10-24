"""
generate_data.py

Creates FAKE sales data for one Red Bull territory that switches from an
independent distributor (Distributor A) to a company-owned RBDC branch
(Distributor B) on the week ending 2025-07-05.

All stores, IDs, addresses and sales numbers are made up. Product names are
based on Red Bull's public product lineup.

Problems added on purpose (the kind of things that break reporting):
  1. Overlap week  - both distributors report the cutover week (double counting)
  2. Gap week      - the new distributor's file for one week never arrives
  3. Store IDs     - each distributor uses its own store IDs and address formats
  4. Product codes - the old distributor uses its own item codes, and one new
                     item (Summer Edition) is missing from the code crosswalk
  5. Messy codes   - some new-distributor SKUs come in lowercase / with spaces
  6. Duplicates    - a few rows in the new distributor's file are sent twice

The "true" numbers are saved in data/answer_key so the pipeline can be checked.
"""
import csv
import datetime as dt
import math
import os
import random

random.seed(7)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")
KEY = os.path.join(ROOT, "data", "answer_key")

WEEKS = [dt.date(2025, 1, 4) + dt.timedelta(days=7 * i) for i in range(52)]
CUTOVER = 26          # index of week ending 2025-07-05
GAP = 29              # index of week ending 2025-07-26 (file never arrives)
OLD_OVERLAP_SHARE = 0.7

# rb_sku, name, size_oz, pack, units_per_case, old distributor item code, sales mix
PRODUCTS = [
    ("RB-1001", "Red Bull Energy Drink 8.4oz", 8.4, "Single", 24, "10084", 0.12),
    ("RB-1002", "Red Bull Energy Drink 8.4oz 4-Pack", 8.4, "4-Pack", 24, "10484", 0.13),
    ("RB-1003", "Red Bull Energy Drink 12oz", 12, "Single", 24, "10120", 0.17),
    ("RB-1004", "Red Bull Energy Drink 16oz", 16, "Single", 24, "10160", 0.08),
    ("RB-1005", "Red Bull Energy Drink 20oz", 20, "Single", 24, "10200", 0.05),
    ("RB-2001", "Red Bull Sugarfree 8.4oz", 8.4, "Single", 24, "20084", 0.08),
    ("RB-2002", "Red Bull Sugarfree 12oz", 12, "Single", 24, "20120", 0.08),
    ("RB-3001", "Red Bull Zero 12oz", 12, "Single", 24, "30120", 0.07),
    ("RB-4001", "Red Bull Red Edition 12oz", 12, "Single", 24, "40120", 0.06),
    ("RB-4002", "Red Bull Blue Edition 12oz", 12, "Single", 24, "40220", 0.05),
    ("RB-4003", "Red Bull Yellow Edition 12oz", 12, "Single", 24, "40320", 0.05),
    ("RB-4025", "Red Bull Summer Edition 2025 12oz", 12, "Single", 24, "42520", 0.06),
]
SEASONAL_SKU, SEASON_START, SEASON_END = "RB-4025", 18, 40
MISSING_FROM_XREF = {"42520"}

# chain name, typical weekly cases per store
CHAINS = [("QuickStop", 30), ("FuelMart", 24), ("Gulf Mart", 20), ("Corner Market", 12),
          ("FreshWay Grocery", 45), ("ValuDrug", 10), ("SpeedyGas", 26), ("Lone Star Food Store", 16)]

PLACES = [("Houston", "77084"), ("Houston", "77095"), ("Katy", "77449"), ("Katy", "77494"),
          ("Cypress", "77429"), ("Cypress", "77433"), ("Spring", "77379"), ("Tomball", "77375"),
          ("Houston", "77070"), ("Houston", "77041"), ("Humble", "77346"), ("Houston", "77064")]

# street name, street type, direction
STREETS = [("Barker Cypress", "Road", ""), ("Westheimer", "Road", ""), ("Clay", "Road", ""),
           ("Fry", "Road", ""), ("Mason", "Road", ""), ("Spring Cypress", "Road", ""),
           ("Louetta", "Road", ""), ("Kuykendahl", "Road", ""), ("Grant", "Road", ""),
           ("Telge", "Road", ""), ("Huffmeister", "Road", ""), ("Jones", "Road", ""),
           ("Eldridge", "Parkway", "North"), ("Katy", "Freeway", ""), ("Northwest", "Freeway", ""),
           ("Tomball", "Parkway", ""), ("Gessner", "Drive", ""), ("Main", "Street", "South"),
           ("Memorial", "Drive", ""), ("Fairfield", "Boulevard", ""), ("Cypress Creek", "Parkway", ""),
           ("Copperfield", "Drive", ""), ("Greenhouse", "Road", ""), ("Peek", "Road", ""),
           ("Cinco Ranch", "Boulevard", ""), ("Mason Creek", "Avenue", ""), ("Bellaire", "Boulevard", "")]
ABBR = {"Road": "RD", "Street": "ST", "Avenue": "AVE", "Boulevard": "BLVD",
        "Drive": "DR", "Parkway": "PKWY", "Freeway": "FWY"}
DIR_ABBR = {"North": "N", "South": "S"}

# How many stores of each kind
N_EASY, N_MEDIUM, N_HARD, N_CLOSED, N_NEW = 108, 17, 7, 8, 6


def poisson(lam):
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= random.random()
        if p <= limit:
            return k
        k += 1


def typo(word):
    i = random.randint(1, len(word) - 2)
    return word[:i] + word[i + 1:]


def make_stores():
    used_numbers, used_old, used_new = set(), set(), set()
    store_nos = {c: random.sample(range(100, 999), 60) for c, _ in CHAINS}
    stores = []
    kinds = (["easy"] * N_EASY + ["medium"] * N_MEDIUM + ["hard"] * N_HARD +
             ["closed"] * N_CLOSED + ["new"] * N_NEW)
    random.shuffle(kinds)
    for kind in kinds:
        chain, size = random.choice(CHAINS)
        no = store_nos[chain].pop()
        city, zip5 = random.choice(PLACES)
        street, stype, direction = random.choice(STREETS)
        while True:
            num = random.randint(1000, 25999)
            if (num, street) not in used_numbers:
                used_numbers.add((num, street))
                break
        suite = random.choice([100, 110, 120, 200, 210, 300, 450]) if random.random() < 0.3 else None

        def acct():
            while True:
                a = f"C{random.randint(10000, 99999)}"
                if a not in used_old:
                    used_old.add(a)
                    return a

        def outlet():
            while True:
                o = f"RBDC-HOU-{random.randint(1000, 9999)}"
                if o not in used_new:
                    used_new.add(o)
                    return o

        s = dict(kind=kind, chain=chain, no=no, city=city, zip5=zip5, street=street,
                 stype=stype, direction=direction, num=num, suite=suite,
                 base=size * random.uniform(0.6, 1.5),
                 old_id=acct() if kind != "new" else "",
                 new_id=outlet() if kind != "closed" else "")

        # --- Old distributor format: ALL CAPS, abbreviations, sometimes ZIP+4
        d = DIR_ABBR[direction] + " " if direction else ""
        s["old_name"] = f"{chain.upper()} #{no}"
        s["old_addr"] = f"{num} {d}{street.upper()} {ABBR[stype]}" + (f" STE {suite}" if suite else "")
        s["old_city"] = city.upper()
        s["old_zip"] = zip5 + (f"-{random.randint(1000, 9999)}" if random.random() < 0.3 else "")

        # --- New distributor format: Title Case, full words
        new_num, new_street, new_dir, new_name = num, street, direction, f"{chain} {no}"
        if random.random() < 0.3:
            new_name = f"{chain} - {no}"
        if kind == "medium":
            change = random.choice(["typo", "dir", "number"]) if direction else random.choice(["typo", "number"])
            if change == "typo":
                new_street = typo(street)
            elif change == "dir":
                new_dir = ""
            else:
                new_num = num + random.choice([-2, 2, 10])
        if kind == "hard":
            new_name = f"{chain} Express {no}"
            new_num = num + random.choice([-4, 4, 20])
        nd = new_dir + " " if new_dir else ""
        s["new_name"] = new_name
        s["new_addr"] = f"{new_num} {nd}{new_street} {stype}" + (f", Suite {suite}" if suite else "")
        s["new_city"] = city
        s["new_zip"] = zip5

        # --- Weeks the store is open
        if kind == "closed":
            s["open"] = range(0, random.randint(8, 22))
        elif kind == "new":
            s["open"] = range(random.randint(31, 45), 52)
        else:
            s["open"] = range(0, 52)
        stores.append(s)
    return stores


def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(KEY, exist_ok=True)
    stores = make_stores()

    # True sales: one row per week / store / product
    truth = []
    for s in stores:
        for w in s["open"]:
            season = 1 + 0.18 * math.sin(2 * math.pi * (w - 10) / 52)
            trend = 1 + 0.002 * w
            for sku, *_rest, mix in PRODUCTS:
                if sku == SEASONAL_SKU and not (SEASON_START <= w <= SEASON_END):
                    continue
                c = poisson(s["base"] * mix * season * trend)
                if c > 0:
                    truth.append((w, s, sku, c))

    old_code = {p[0]: p[5] for p in PRODUCTS}

    # Old distributor file (weeks up to AND including cutover week = overlap)
    old_rows = []
    for w, s, sku, c in truth:
        if s["kind"] == "new" or w > CUTOVER:
            continue
        cases = c if w < CUTOVER else round(c * OLD_OVERLAP_SHARE)
        if cases > 0:
            old_rows.append([WEEKS[w].strftime("%m/%d/%Y"), s["old_id"], old_code[sku], f"{cases:.2f}"])

    # New distributor file (cutover week onward, gap week missing)
    new_rows = []
    for w, s, sku, c in truth:
        if s["kind"] == "closed" or w < CUTOVER or w == GAP:
            continue
        code = sku
        r = random.random()
        if r < 0.03:
            code = sku.lower()
        elif r < 0.05:
            code = sku + " "
        new_rows.append([WEEKS[w].isoformat(), s["new_id"], code, str(c)])
    for row in random.sample(new_rows, 15):
        new_rows.append(list(row))          # same row sent twice
    random.shuffle(new_rows)

    def write(path, header, rows):
        with open(path, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
            wr.writerows(rows)

    write(os.path.join(RAW, "distributor_a_sales.csv"), ["INV_WEEK", "ACCT_NO", "ITEM_CODE", "CASES"], old_rows)
    write(os.path.join(RAW, "distributor_b_sales.csv"), ["week_ending", "outlet_id", "sku", "qty_cases"], new_rows)
    write(os.path.join(RAW, "distributor_a_stores.csv"), ["ACCT_NO", "ACCT_NAME", "ADDR1", "CITY", "ST", "ZIP"],
          [[s["old_id"], s["old_name"], s["old_addr"], s["old_city"], "TX", s["old_zip"]]
           for s in stores if s["kind"] != "new"])
    write(os.path.join(RAW, "distributor_b_stores.csv"),
          ["outlet_id", "outlet_name", "street_address", "city", "state", "zip_code"],
          [[s["new_id"], s["new_name"], s["new_addr"], s["new_city"], "TX", s["new_zip"]]
           for s in stores if s["kind"] != "closed"])
    write(os.path.join(RAW, "distributor_a_item_xref.csv"), ["old_item_code", "old_item_description", "rb_sku"],
          [[p[5], p[1].upper().replace("RED BULL ", "RB "), p[0]] for p in PRODUCTS if p[5] not in MISSING_FROM_XREF])
    write(os.path.join(RAW, "product_master.csv"), ["rb_sku", "product_name", "size_oz", "pack_type", "units_per_case"],
          [list(p[:5]) for p in PRODUCTS])

    # Answer key (for checking the pipeline only - not used by the SQL)
    weekly = {}
    for w, s, sku, c in truth:
        weekly[w] = weekly.get(w, 0) + c
    write(os.path.join(KEY, "true_weekly_cases.csv"), ["week_ending", "true_cases"],
          [[WEEKS[w].isoformat(), weekly.get(w, 0)] for w in range(52)])
    write(os.path.join(KEY, "true_store_map.csv"), ["old_store_id", "new_store_id", "store_type"],
          [[s["old_id"], s["new_id"], s["kind"]] for s in stores])

    print(f"Stores: {len(stores)} | Distributor A rows: {len(old_rows)} | Distributor B rows: {len(new_rows)}")


if __name__ == "__main__":
    main()
