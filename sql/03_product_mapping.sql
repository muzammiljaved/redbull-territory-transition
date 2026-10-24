/* ============================================================
   03_product_mapping.sql
   Put both distributors on Red Bull SKUs and master store IDs.
   Old item codes with no crosswalk entry are kept (so totals stay
   right) but labeled UNMAPPED so they show up in the issue list.
   ============================================================ */

DROP TABLE IF EXISTS old_sales_mapped;
CREATE TABLE old_sales_mapped AS
SELECT s.week_ending,
       x.master_store_id,
       COALESCE(p.rb_sku, 'UNMAPPED:' || s.item_code) AS rb_sku,
       s.item_code,
       s.cases
FROM stg_old_sales s
JOIN store_xwalk x           ON x.source = 'OLD' AND x.store_id = s.store_id
LEFT JOIN raw_old_item_xref p ON p.old_item_code = s.item_code;

DROP TABLE IF EXISTS new_sales_mapped;
CREATE TABLE new_sales_mapped AS
SELECT s.week_ending,
       x.master_store_id,
       CASE WHEN pm.rb_sku IS NULL THEN 'UNKNOWN:' || s.rb_sku ELSE s.rb_sku END AS rb_sku,
       s.cases
FROM stg_new_sales s
JOIN store_xwalk x          ON x.source = 'NEW' AND x.store_id = s.store_id
LEFT JOIN raw_product_master pm ON pm.rb_sku = s.rb_sku;
