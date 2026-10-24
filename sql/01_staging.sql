/* ============================================================
   01_staging.sql
   Clean up the raw distributor files into one standard format.
   Raw tables are loaded as plain text by run_pipeline.py.
   ============================================================ */

-- Settings for this territory switch
DROP TABLE IF EXISTS config;
CREATE TABLE config AS
SELECT 'Northwest Houston (Territory 14) - simulated' AS territory,
       '2025-07-05'                                 AS cutover_week,   -- first week Distributor B owns the territory
       'Distributor A (independent wholesaler)'     AS old_distributor,
       'Distributor B (RBDC branch, simulated)'     AS new_distributor;

-- Distributor A sales: dates come in as MM/DD/YYYY, cases as text
DROP TABLE IF EXISTS stg_old_sales;
CREATE TABLE stg_old_sales AS
SELECT substr(INV_WEEK, 7, 4) || '-' || substr(INV_WEEK, 1, 2) || '-' || substr(INV_WEEK, 4, 2) AS week_ending,
       TRIM(ACCT_NO)          AS store_id,
       TRIM(ITEM_CODE)        AS item_code,
       CAST(CASES AS REAL)    AS cases
FROM raw_old_sales;

-- Distributor B sales: fix messy SKU codes and remove rows that were sent twice
DROP TABLE IF EXISTS stg_new_sales;
CREATE TABLE stg_new_sales AS
SELECT week_ending,
       TRIM(outlet_id)                AS store_id,
       UPPER(TRIM(sku))               AS rb_sku,
       CAST(qty_cases AS REAL)        AS cases,
       MAX(CASE WHEN sku <> UPPER(TRIM(sku)) THEN 1 ELSE 0 END) AS sku_was_cleaned,
       COUNT(*)                       AS copies_received
FROM raw_new_sales
GROUP BY week_ending, TRIM(outlet_id), UPPER(TRIM(sku)), qty_cases;

-- Both store lists in one table, with a normalized address and name
-- so the two formats can be compared.
DROP TABLE IF EXISTS stores_norm;
CREATE TABLE stores_norm AS
WITH all_stores AS (
    SELECT 'OLD' AS source, ACCT_NO AS store_id, ACCT_NAME AS store_name, ADDR1 AS address,
           CITY AS city, SUBSTR(TRIM(ZIP), 1, 5) AS zip5
    FROM raw_old_stores
    UNION ALL
    SELECT 'NEW', outlet_id, outlet_name, street_address, city, SUBSTR(TRIM(zip_code), 1, 5)
    FROM raw_new_stores
),
step1 AS (   -- upper case, drop punctuation, pad with spaces so whole words can be swapped
    SELECT *, ' ' || REPLACE(REPLACE(REPLACE(UPPER(TRIM(address)), '.', ''), ',', ''), '#', '') || ' ' AS a
    FROM all_stores
)
SELECT source, store_id, store_name, address, UPPER(city) AS city, zip5,
       TRIM(
         REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(a,
           ' STREET ', ' ST '), ' AVENUE ', ' AVE '), ' ROAD ', ' RD '), ' BOULEVARD ', ' BLVD '),
           ' DRIVE ', ' DR '), ' PARKWAY ', ' PKWY '), ' FREEWAY ', ' FWY '), ' SUITE ', ' STE '),
           ' NORTH ', ' N '), ' SOUTH ', ' S ')
       ) AS addr_norm,
       UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(store_name, ' ', ''), '#', ''), '-', ''), '.', ''), '''', '')) AS name_key
FROM step1;

-- One row per week in the reporting period
DROP TABLE IF EXISTS calendar;
CREATE TABLE calendar AS
WITH RECURSIVE weeks(week_ending) AS (
    SELECT MIN(week_ending) FROM (SELECT week_ending FROM stg_old_sales UNION SELECT week_ending FROM stg_new_sales)
    UNION ALL
    SELECT date(week_ending, '+7 days') FROM weeks
    WHERE week_ending < (SELECT MAX(week_ending) FROM (SELECT week_ending FROM stg_old_sales UNION SELECT week_ending FROM stg_new_sales))
)
SELECT week_ending,
       CASE WHEN week_ending < (SELECT cutover_week FROM config) THEN 'OLD' ELSE 'NEW' END AS owner
FROM weeks;
