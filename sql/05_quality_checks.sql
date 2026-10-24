/* ============================================================
   05_quality_checks.sql
   One table listing every issue found, how serious it is,
   and how many cases it touches (the business impact).
   ============================================================ */

DROP TABLE IF EXISTS dq_issues;
CREATE TABLE dq_issues (check_name TEXT, severity TEXT, week_ending TEXT, entity TEXT,
                        detail TEXT, cases_impacted REAL, action_taken TEXT);

-- 1. Both distributors reported the same week
INSERT INTO dq_issues
SELECT 'OVERLAP_WEEK', 'HIGH', o.week_ending, 'Territory',
       'Both distributors sent sales for this week. Loading both would double count.',
       SUM(o.cases), 'Kept Distributor B (territory owner); dropped Distributor A rows for this week'
FROM stg_old_sales o
WHERE o.week_ending IN (SELECT week_ending FROM stg_new_sales)
GROUP BY o.week_ending;

-- 2. No data at all from the distributor that owned the territory that week
INSERT INTO dq_issues
SELECT 'MISSING_WEEK', 'HIGH', m.week_ending, 'Territory',
       'No file received from the owning distributor (' || m.owner || ').',
       (SELECT SUM(cases) FROM clean_sales WHERE week_ending = m.week_ending AND is_estimated = 1),
       'Estimated from surrounding weeks and labeled ESTIMATED; request the file from distributor'
FROM missing_weeks m;

-- 3. Old item codes not in the crosswalk
INSERT INTO dq_issues
SELECT 'UNMAPPED_PRODUCT', 'MEDIUM', NULL, 'Item ' || item_code,
       'Distributor A item code has no Red Bull SKU in the crosswalk. Sold ' ||
       COUNT(DISTINCT week_ending) || ' weeks (' || MIN(week_ending) || ' to ' || MAX(week_ending) || ').',
       SUM(cases), 'Kept in totals as UNMAPPED; ask distributor to confirm the SKU and update crosswalk'
FROM old_sales_mapped
WHERE rb_sku LIKE 'UNMAPPED:%'
GROUP BY item_code;

-- 4. Unknown SKUs from the new distributor
INSERT INTO dq_issues
SELECT 'UNKNOWN_SKU', 'MEDIUM', NULL, rb_sku, 'SKU not found in product master.', SUM(cases),
       'Kept in totals; check against product master'
FROM new_sales_mapped WHERE rb_sku LIKE 'UNKNOWN:%' GROUP BY rb_sku;

-- 5. Stores that could not be linked and might be the same store under two IDs
INSERT INTO dq_issues
SELECT 'STORE_NEEDS_REVIEW', 'MEDIUM', NULL, source || ' ' || store_id || ' - ' || store_name,
       'No match found, but store was active around the cutover. Could be the same store with different name/address. '
       || 'Active ' || first_week || ' to ' || last_week || '.',
       total_cases, 'Totals are correct; store-level history is split until someone confirms the match'
FROM unmatched_stores WHERE status = 'NEEDS_REVIEW';

-- 6. Matched on name + ZIP only (address did not line up)
INSERT INTO dq_issues
SELECT 'PROBABLE_MATCH', 'LOW', NULL, m.old_id || ' -> ' || m.new_id,
       'Matched on store name + ZIP. Addresses differ: "' || o.address || '" vs "' || n.address || '".',
       NULL, 'Accepted; spot check'
FROM store_match m
JOIN stores_norm o ON o.source = 'OLD' AND o.store_id = m.old_id
JOIN stores_norm n ON n.source = 'NEW' AND n.store_id = m.new_id
WHERE m.match_rule = 'R2_NAME_ZIP';

-- 7. Informational: closed and new stores
INSERT INTO dq_issues
SELECT CASE status WHEN 'LIKELY_CLOSED' THEN 'LIKELY_CLOSED_STORE' ELSE 'LIKELY_NEW_STORE' END, 'INFO', NULL,
       source || ' ' || store_id || ' - ' || store_name,
       'Active ' || first_week || ' to ' || last_week || '.', total_cases, 'No action; confirm with sales team'
FROM unmatched_stores WHERE status IN ('LIKELY_CLOSED', 'LIKELY_NEW_STORE');

-- 8. Duplicate rows sent by Distributor B
INSERT INTO dq_issues
SELECT 'DUPLICATE_ROWS', 'MEDIUM', NULL, 'Distributor B file',
       COUNT(*) || ' rows were received more than once.',
       SUM(cases * (copies_received - 1)), 'Removed duplicates'
FROM stg_new_sales WHERE copies_received > 1
HAVING COUNT(*) > 0;

-- 9. SKU codes that needed cleanup (lowercase / extra spaces)
INSERT INTO dq_issues
SELECT 'MESSY_SKU_CODES', 'LOW', NULL, 'Distributor B file',
       COUNT(*) || ' rows had SKU codes with lowercase letters or extra spaces.',
       SUM(cases), 'Cleaned automatically'
FROM stg_new_sales WHERE sku_was_cleaned = 1
HAVING COUNT(*) > 0;
