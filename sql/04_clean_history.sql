/* ============================================================
   04_clean_history.sql
   Build one continuous sales history for the territory.
   - Before cutover: use Distributor A
   - Cutover and after: use Distributor B (A's overlap rows are dropped)
   - A week Distributor B never sent: estimate from the week before
     and after, and label it ESTIMATED so nobody mistakes it for actuals
   ============================================================ */

DROP TABLE IF EXISTS clean_sales;
CREATE TABLE clean_sales (week_ending TEXT, master_store_id TEXT, rb_sku TEXT, cases REAL,
                          data_source TEXT, is_estimated INTEGER);

INSERT INTO clean_sales
SELECT week_ending, master_store_id, rb_sku, cases, 'DISTRIBUTOR_A', 0
FROM old_sales_mapped
WHERE week_ending < (SELECT cutover_week FROM config);

INSERT INTO clean_sales
SELECT week_ending, master_store_id, rb_sku, cases, 'DISTRIBUTOR_B', 0
FROM new_sales_mapped
WHERE week_ending >= (SELECT cutover_week FROM config);

-- Weeks the owning distributor did not report at all
DROP TABLE IF EXISTS missing_weeks;
CREATE TABLE missing_weeks AS
SELECT c.week_ending, c.owner
FROM calendar c
WHERE NOT EXISTS (SELECT 1 FROM clean_sales s WHERE s.week_ending = c.week_ending);

-- Estimate = average of the week before and the week after (a missing side counts as 0)
INSERT INTO clean_sales
SELECT m.week_ending, s.master_store_id, s.rb_sku, ROUND(SUM(s.cases) / 2.0, 2), 'ESTIMATED', 1
FROM missing_weeks m
JOIN clean_sales s ON s.is_estimated = 0
                  AND s.week_ending IN (date(m.week_ending, '-7 days'), date(m.week_ending, '+7 days'))
GROUP BY m.week_ending, s.master_store_id, s.rb_sku;
