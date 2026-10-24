# Power BI Dashboard Guide

Load these files from `data/output/`: `weekly_compare.csv`, `clean_sales.csv`, `dq_issues.csv`,
`store_match_report.csv`, plus `data/raw/product_master.csv`.

Relationship: `clean_sales[rb_sku]` -> `product_master[rb_sku]` (many to one).

## Page 1: Before and After

- Line chart: `week_ending` on the X axis, `raw_cases` and `clean_cases` as two lines
  (red for raw, dark blue for clean)
- Cards: overlap week % error, missing weeks fixed, stores auto-matched
- Short text box: "Loading both distributor files as-is makes July look 71% higher one week and zero another."

## Page 2: Issue List

- Table from `dq_issues`: check_name, severity, entity, cases_impacted, action_taken
- Bar chart: cases_impacted by check_name
- Slicer: severity
- Conditional formatting: HIGH red, MEDIUM orange, LOW grey

## Page 3: Store Matching

- Donut or bar: count of stores by `match_rule` (R1_ADDRESS_ZIP, R2_NAME_ZIP, NO_MATCH)
- Table filtered to NO_MATCH + NEEDS_REVIEW, showing old and new names and addresses side by side

## Page 4: Product View (optional)

- Stacked column: `clean_sales` cases by week and `product_name`
- Shows the "UNMAPPED" item appearing before cutover

## Useful DAX measures

```
Clean Cases = SUM(clean_sales[cases])
Estimated Cases = CALCULATE([Clean Cases], clean_sales[is_estimated] = 1)
Raw vs Clean % = DIVIDE(SUM(weekly_compare[raw_cases]) - SUM(weekly_compare[clean_cases]),
                        SUM(weekly_compare[clean_cases]))
High Issues = CALCULATE(COUNTROWS(dq_issues), dq_issues[severity] = "HIGH")
```
