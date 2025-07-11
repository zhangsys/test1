--DLC SQL
--******************************************************************--
--author: supasate.vorathammathorn@lotuss.com
--create time: 2025-06-19T09:47:48+07:00
--******************************************************************--
SET spark.sql.sources.partitionOverwriteMode=DYNAMIC;
 
-- DROP TABLE t0_lotuss.item_cube_ft;
-- DROP TABLE t1_lotuss_mnf.item_cube_ft;

--- CREATE TABLE T0 ---
CREATE EXTERNAL TABLE IF NOT EXISTS t0_lotuss.item_cube_ft (
  `item` STRING,
  `supplier` DECIMAL(10,0),
  `length` DECIMAL(4,2),
  `width` DECIMAL(4,2),
  `height` DECIMAL(4,2),
  `lwh_uom` STRING
) USING csv
OPTIONS ('inferSchema'='false', 'header'='true', 'dataAddress'="'Sheet1'!A1")
PARTITIONED BY (country STRING, source STRING, dp_data_dt STRING)
LOCATION 'cosn://${t0_lotuss_cos_bucket}/t0_lotuss_mnf/item_cube_ft';
 
--- ADD TABLE T0 PARTITION ---
ALTER TABLE t0_lotuss.item_cube_ft
ADD IF NOT EXISTS PARTITION (country = '${country}', source = '${source}', dp_data_dt = '${dp_data_dt}')
LOCATION 'cosn://${t0_lotuss_cos_bucket}/t0_lotuss_mnf/item_cube_ft/${country}/${source}/${dp_data_dt}';
 
--- CREATE TABLE ---
CREATE TABLE IF NOT EXISTS t1_lotuss_mnf.item_cube_ft (
  `item` STRING,
  `supplier` DECIMAL(10,0),
  `length` DECIMAL(4,2),
  `width` DECIMAL(4,2),
  `height` DECIMAL(4,2),
  `lwh_uom` STRING
, `dp_load_ts` TIMESTAMP
, `country` STRING
, `source` STRING
, `dp_data_dt` DATE
) USING ICEBERG
PARTITIONED BY (country,source,dp_data_dt)
TBLPROPERTIES (
'format-version' = '2',
'write.upsert.enabled' = 'true',
'write.update.mode' = 'merge-on-read',
'write.merge.mode' = 'merge-on-read',
'write.distribution-mode' = 'hash',
'write.metadata.delete-after-commit.enabled' = 'true',
'write.metadata.previous-versions-max' = '100',
'write.metadata.metrics.default' = 'full',
'smart-optimizer.inherit' = 'default'
);
 
--- INSERT OVERWRITE TABLE T1 ---
INSERT OVERWRITE TABLE t1_lotuss_mnf.item_cube_ft
SELECT
  CAST(`item` AS STRING)
, CAST(`supplier` AS DECIMAL(10,0))
, CAST(`length` AS DECIMAL(4,2))
, CAST(`width` AS DECIMAL(4,2))
, CAST(`height` AS DECIMAL(4,2))
, CAST(`lwh_uom` AS STRING)
, current_timestamp() as dp_load_ts
, CAST(`country` AS STRING)
, CAST(`source` AS STRING)
, TO_DATE(dp_data_dt, 'yyyy-MM-dd')
FROM t0_lotuss.item_cube_ft
WHERE country = '${country}'
AND source = '${source}'
AND dp_data_dt = '${dp_data_dt}';