# Issue Log: Northwest Houston Territory Switch (simulated)

Cutover week: **week ending July 5, 2025**. Distributor A (independent) to Distributor B (RBDC branch).

| # | Issue | Severity | Business impact | What was done | Next step / owner |
|---|---|---|---|---|---|
| 1 | Both distributors sent sales for week ending Jul 5 | High | Raw territory sales showed **+71%** that week (2,822 extra cases). Would inflate July and the YTD trend. | Kept Distributor B (territory owner), dropped A's rows for that week | Confirm with A that Jul 5 was their last delivery week |
| 2 | No file from Distributor B for week ending Jul 26 | High | Raw reports showed **zero** sales for the territory that week (about 3,700 cases missing) | Filled with an estimate from the weeks before and after (3,795 cases), labeled "estimated" | Request the file from B; replace the estimate when it arrives |
| 3 | Old item code 42520 (Summer Edition) not in the crosswalk | Medium | 2,015 cases over 9 weeks could not be reported by product. Summer Edition looked like it sold nothing before the switch. | Kept in totals as "UNMAPPED" | Ask A to confirm the SKU; add it to the crosswalk |
| 4 | 7 old stores and 7 new stores could not be matched, but all were active around the switch | Medium | Territory totals are correct, but these stores look like 7 stores "closed" and 7 "opened" on Jul 5. Store-level before/after is wrong for them. | Kept separate and listed for review | Sales rep or distributor to confirm which pairs are the same store |
| 5 | 17 stores matched on name + ZIP only (address didn't line up) | Low | Small risk of a wrong match | Accepted and listed | Spot check a few |
| 6 | 15 rows sent twice by Distributor B | Medium | 47 extra cases | Removed duplicates | Mention to B's IT contact |
| 7 | SKU codes in lowercase or with extra spaces | Low | Would have failed to match products | Cleaned automatically | None |
| 8 | 8 stores stopped buying before the switch, 6 new stores started after | Info | Real business changes, not data errors | No change | Confirm with sales team |

**Summary for stakeholders:** After cleanup, territory sales for the transition period match the true
numbers, except one estimated week that is within about 2%. Two follow-ups are needed from distributors
(missing file, item code), and 7 store pairs need a quick human check.
