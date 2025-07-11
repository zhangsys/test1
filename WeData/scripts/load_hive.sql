-- 加载数据到 Hive
INSERT INTO hive_table SELECT * FROM staging_table; 