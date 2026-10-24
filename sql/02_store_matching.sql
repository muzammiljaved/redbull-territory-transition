/* ============================================================
   02_store_matching.sql
   Link Distributor A store IDs to Distributor B store IDs.
   Rule 1: same cleaned address + same ZIP        -> HIGH confidence
   Rule 2: same cleaned store name + same ZIP     -> MEDIUM (spot check)
   Anything left over is sorted into closed, new, or needs review.
   ============================================================ */

DROP TABLE IF EXISTS store_match;
CREATE TABLE store_match (old_id TEXT, new_id TEXT, match_rule TEXT, confidence TEXT);

INSERT INTO store_match
SELECT o.store_id, n.store_id, 'R1_ADDRESS_ZIP', 'HIGH'
FROM stores_norm o
JOIN stores_norm n ON o.source = 'OLD' AND n.source = 'NEW'
                  AND o.addr_norm = n.addr_norm AND o.zip5 = n.zip5;

INSERT INTO store_match
SELECT o.store_id, n.store_id, 'R2_NAME_ZIP', 'MEDIUM'
FROM stores_norm o
JOIN stores_norm n ON o.source = 'OLD' AND n.source = 'NEW'
                  AND o.name_key = n.name_key AND o.zip5 = n.zip5
WHERE o.store_id NOT IN (SELECT old_id FROM store_match)
  AND n.store_id NOT IN (SELECT new_id FROM store_match);

-- First and last week each store had sales, by source
DROP TABLE IF EXISTS store_activity;
CREATE TABLE store_activity AS
SELECT 'OLD' AS source, store_id, MIN(week_ending) AS first_week, MAX(week_ending) AS last_week, SUM(cases) AS total_cases
FROM stg_old_sales GROUP BY store_id
UNION ALL
SELECT 'NEW', store_id, MIN(week_ending), MAX(week_ending), SUM(cases)
FROM stg_new_sales GROUP BY store_id;

-- Stores with no match: decide what they probably are
DROP TABLE IF EXISTS unmatched_stores;
CREATE TABLE unmatched_stores AS
SELECT s.source, s.store_id, s.store_name, s.address, s.zip5, a.first_week, a.last_week, a.total_cases,
       CASE
         WHEN s.source = 'OLD' AND a.last_week  < date((SELECT cutover_week FROM config), '-14 days') THEN 'LIKELY_CLOSED'
         WHEN s.source = 'NEW' AND a.first_week > date((SELECT cutover_week FROM config), '+14 days') THEN 'LIKELY_NEW_STORE'
         ELSE 'NEEDS_REVIEW'
       END AS status
FROM stores_norm s
LEFT JOIN store_activity a ON a.source = s.source AND a.store_id = s.store_id
WHERE (s.source = 'OLD' AND s.store_id NOT IN (SELECT old_id FROM store_match))
   OR (s.source = 'NEW' AND s.store_id NOT IN (SELECT new_id FROM store_match));

-- Every store ID from either distributor -> one master store ID.
-- Going forward the territory runs on Distributor B IDs, so those become the master.
DROP TABLE IF EXISTS store_xwalk;
CREATE TABLE store_xwalk AS
SELECT 'NEW' AS source, store_id, store_id AS master_store_id FROM stores_norm WHERE source = 'NEW'
UNION ALL
SELECT 'OLD', o.store_id, COALESCE(m.new_id, 'OLD-' || o.store_id)
FROM stores_norm o
LEFT JOIN store_match m ON m.old_id = o.store_id
WHERE o.source = 'OLD';
