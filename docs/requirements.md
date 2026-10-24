# Requirements: Territory Transition Reporting

## The request (as a sales manager might say it)

> "We're moving the Northwest Houston territory from our independent distributor to RBDC on July 5.
> Last time we did one of these, the region's numbers looked crazy for a month and nobody trusted the
> reports. I need sales for this territory to look like one continuous history, so I can compare this
> year to last year and see how each store is doing before and after the switch."

## What that means in plain terms

1. Weekly sales for the territory should not jump or drop just because the data source changed.
2. Each store should have one history, not one under the old ID and another under the new ID.
3. Sales should be reported by Red Bull product, no matter which distributor sold it.
4. If something can't be fixed automatically, someone should know about it and how big it is.

## Technical requirements

| # | Requirement | How it's met |
|---|---|---|
| 1 | Set a cutover week. Before it, use Distributor A. From it on, use Distributor B. | `config.cutover_week`, applied in `04_clean_history.sql` |
| 2 | If both distributors report the same week, do not add them together. | Overlap rows from A are dropped and logged |
| 3 | If the owning distributor sends no data for a week, do not show zero. Fill with an estimate and label it. | Average of the weeks before and after, `is_estimated = 1` |
| 4 | Link old store IDs to new store IDs. Only link automatically when confident. | Rule 1 address + ZIP (high), Rule 2 name + ZIP (medium) |
| 5 | Never drop sales because a store or product couldn't be matched. | Unmatched stores and items stay in totals with a label |
| 6 | Map old item codes to Red Bull SKUs using the distributor's crosswalk. | `03_product_mapping.sql` |
| 7 | Clean common formatting problems automatically (dates, case, spaces, duplicates). | `01_staging.sql` |
| 8 | Give one list of every issue, how serious it is, and how many cases it touches. | `dq_issues` table |
| 9 | Show the before and after so stakeholders can see the impact. | `weekly_compare` table and dashboard |

## Out of scope (for this version)

- Comparing distributor sales to Red Bull shipments
- Fuzzy matching for hard-to-match stores
- Automatic alerts when a file is late
