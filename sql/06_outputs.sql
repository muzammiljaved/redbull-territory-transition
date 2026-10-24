/* ============================================================
   06_outputs.sql
   Tables for the dashboard: raw vs. clean, week by week.
   "Raw" = what you'd see if you just loaded both files as-is.
   ============================================================ */

DROP TABLE IF EXISTS weekly_compare;
CREATE TABLE weekly_compare AS
WITH raw AS (
    SELECT week_ending, SUM(cases) AS cases, COUNT(DISTINCT store_id) AS stores
    FROM (SELECT week_ending, store_id, cases FROM stg_old_sales
          UNION ALL
          SELECT week_ending, TRIM(outlet_id), CAST(qty_cases AS REAL) FROM raw_new_sales)
    GROUP BY week_ending
),
clean AS (
    SELECT week_ending, SUM(cases) AS cases, COUNT(DISTINCT master_store_id) AS stores,
           MAX(is_estimated) AS is_estimated
    FROM clean_sales GROUP BY week_ending
)
SELECT c.week_ending,
       COALESCE(r.cases, 0)  AS raw_cases,
       cl.cases              AS clean_cases,
       COALESCE(r.stores, 0) AS raw_store_count,
       cl.stores             AS clean_store_count,
       CASE WHEN c.week_ending IN (SELECT week_ending FROM dq_issues WHERE check_name = 'OVERLAP_WEEK') THEN 1 ELSE 0 END AS is_overlap_week,
       COALESCE(cl.is_estimated, 0) AS is_estimated_week,
       c.owner AS territory_owner
FROM calendar c
LEFT JOIN raw r    ON r.week_ending = c.week_ending
LEFT JOIN clean cl ON cl.week_ending = c.week_ending
ORDER BY c.week_ending;

-- Store list with match details, for the store review page
DROP TABLE IF EXISTS store_match_report;
CREATE TABLE store_match_report AS
SELECT o.store_id AS old_store_id, o.store_name AS old_name, o.address AS old_address,
       n.store_id AS new_store_id, n.store_name AS new_name, n.address AS new_address,
       o.zip5, m.match_rule, m.confidence
FROM store_match m
JOIN stores_norm o ON o.source = 'OLD' AND o.store_id = m.old_id
JOIN stores_norm n ON n.source = 'NEW' AND n.store_id = m.new_id
UNION ALL
SELECT CASE WHEN source = 'OLD' THEN store_id END, CASE WHEN source = 'OLD' THEN store_name END,
       CASE WHEN source = 'OLD' THEN address END,
       CASE WHEN source = 'NEW' THEN store_id END, CASE WHEN source = 'NEW' THEN store_name END,
       CASE WHEN source = 'NEW' THEN address END,
       zip5, 'NO_MATCH', status
FROM unmatched_stores;
