# Playbook: Data Checks When a Territory Changes Distributors

A simple checklist for the data team. Goal: the switch should be invisible in the reports.

## Before the switch (2–4 weeks out)

- [ ] Confirm the exact cutover week with sales and both distributors
- [ ] Get the new distributor's store list and product codes
- [ ] Run store matching between old and new store lists; send the "needs review" list to the sales rep early
- [ ] Check that every item the old distributor sells is in the item crosswalk, especially new and seasonal items
- [ ] Agree on who reports the cutover week

## Week 1 (cutover week)

- [ ] Check if both distributors sent data for this week (overlap). Keep only the owner's data
- [ ] Compare territory total to the prior 4 weeks. Flag anything more than ±25%
- [ ] Check store count. A jump close to 2x usually means double reporting

## Weeks 2–4

- [ ] Confirm a file arrives every week from the new distributor. Follow up the same day if one is late
- [ ] Look for stores that sold under the old distributor but never appear under the new one
- [ ] Look for "new" stores that appear right at the cutover. They are often the same stores under new IDs
- [ ] Check for unknown or messy SKU codes from the new distributor

## Week 5–8 (close out)

- [ ] Replace any estimated weeks with real data once it's received
- [ ] Resolve every "needs review" store
- [ ] Compare the territory's trend before and after. It should look like one smooth line
- [ ] Send a short summary to stakeholders: what was found, what was fixed, what's still open

## Rules of thumb

- Never drop sales just because a store or product doesn't match. Keep it and label it.
- Never show a missing week as zero. Estimate it and label it, or leave it blank on purpose.
- Only auto-match stores when confident. A wrong match is worse than no match.
