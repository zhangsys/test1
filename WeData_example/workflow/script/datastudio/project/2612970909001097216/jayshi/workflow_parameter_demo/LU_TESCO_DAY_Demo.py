#******************************************************************#
##author: jayshi@tencent.com
##create time: 2025-03-12 18:12:48
#******************************************************************#
from pyspark.sql import SparkSession
from typing import Dict, List

# Import common transformation functions
from fw.cmmn.bin.module.fw_cmmn_tnfm_func import (
    backup_spark_configs,
    apply_spark_configs, 
    export_to_synapse,
    restore_spark_configs
)

def main():
    # Initialize Spark session
    spark = SparkSession.builder.appName("LU_TESCO_DAY").getOrCreate()

    # Job parameters 
    dp_data_dt = "2021-01-20"
    YEAR = '2021'
    trgt_db_nm = "DXWV_PROD_TH_MSTR_VIEW_ACCESS"
    trgt_tbl_nm = "LU_TESCO_DAY"

    # Job specific spark config
    spark_configs: Dict[str, str] = {}

    # DataFrameWriter Options
    write_options: Dict[str, str] = {}

    # Set UPSERT keys
    upsert_keys: List[str] = []
      
    # Insert mode
    truncate_insert = False

    # Take a backup and apply the job specific spark configurations
    default_spark_config = backup_spark_configs(spark_configs.keys())
    apply_spark_configs(spark_configs)

    # Transformation Logic
    transformation_sql = f"""
    --Setup base table
    WITH Calendar AS (
      SELECT 
        CalendarId
      FROM stdm.calendar
    ),
    
    CalendarYear AS (
      SELECT
        CalendarId,
        CalendarYearId,
        CalendarYearNumber
      FROM stdm.calendaryear
    ),
    
    Calendarperiod AS (
      SELECT
        CalendarId,
        CalendarYearId,
        CalendarPeriodNumber
      FROM stdm.calendarperiod
    ),
    
    CalendarQuarter AS (
      SELECT
        CalendarId,
        CalendarYearId,
        CalendarQuarterId,
        CalendarQuarterNumber
      FROM stdm.calendarquarter
    ),
    
    CalendarWeek AS (
      SELECT
        CalendarId,
        CalendarYearId,
        CalendarQuarterId,
        CalendarWeekId,
        CalendarWeekNumber
      FROM stdm.calendarweek
    ),
    
    CalendarDate AS (
      SELECT
        Date,
        CalendarYearId,
        CalendarQuarterId,
        CalendarWeekId,
        DayOfWeekId
      FROM stdm.calendardate
    ),
    
    DayOfWeek AS (
      SELECT
        DayOfWeekName,
        CAST(DayNumber AS SHORT) AS DayNumber,
        CAST(DayOfWeekId AS SHORT) AS DayOfWeekId
      FROM stdm.dayofweek
    )

    --final
    SELECT 
      CAST(11 AS SHORT) AS company_code,
      cd.Date AS Tesco_Day,
      dow.DayNumber AS Day_Number_In_Week,
      CAST(DATE_FORMAT('d', cd.Date) AS SHORT) AS Day_Number_In_Period,
      CAST(DATE_FORMAT('dy', cd.Date) AS SHORT) AS Day_Number_In_Year,
      dow.DayOfWeekName AS Day_Of_The_Week_Local,
      dow.DayOfWeekName AS Day_Of_The_Week,
      CASE WHEN DAY(cd.Date) IN (1, 21, 31) THEN CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'st ', DATE_FORMAT(cd.Date, 'MMMM yyyy'))
        WHEN DAY(cd.Date) IN (2, 22) THEN CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'nd ', DATE_FORMAT(cd.Date, 'MMMM yyyy'))
        WHEN DAY(cd.Date) IN (3, 23) THEN CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'rd ', DATE_FORMAT(cd.Date, 'MMMM yyyy'))
        ELSE CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'th ', DATE_FORMAT(cd.Date, 'MMMM yyyy')) END Date_Description_Local,
        
      CASE WHEN DAY(cd.Date) IN (1, 21, 31) THEN CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'st ', DATE_FORMAT(cd.Date, 'MMMM yyyy'))
        WHEN DAY(cd.Date) IN (2, 22) THEN CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'nd ', DATE_FORMAT(cd.Date, 'MMMM yyyy'))
        WHEN DAY(cd.Date) IN (3, 23) THEN CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'rd ', DATE_FORMAT(cd.Date, 'MMMM yyyy'))
        ELSE CONCAT(DATE_FORMAT(cd.Date, 'EEEE, dd'), 'th ', DATE_FORMAT(cd.Date, 'MMMM yyyy')) END AS Date_Description,
        
      CASE WHEN cw.CalendarWeekNumber < 10 THEN CONCAT(cy.CalendarYearNumber, '0', cw.CalendarWeekNumber)
         ELSE CONCAT(cy.CalendarYearNumber, cw.CalendarWeekNumber) END AS Tesco_week, 
         
      CASE WHEN MONTH(cd.Date) < 10 THEN CONCAT(cy.CalendarYearNumber, '0', MONTH(cd.Date))
         ELSE CONCAT(cy.CalendarYearNumber, MONTH(cd.Date)) END AS Tesco_period,
         
       CONCAT(cy.CalendarYearNumber, '0', cq.CalendarQuarterNumber) AS Tesco_Quarter,
       CONCAT(cy.CalendarYearNumber, cp.CalendarPeriodNumber) AS Tesco_Half_Year,
       cy.CalendarYearNumber AS Tesco_Year,
       date_add(cd.Date, -1) AS Previos_Day,
       date_add(cd.Date, -7) AS Same_Day_Last_Week,
       date_add(cd.Date, -364) AS Same_Day_Last_Year,
       CAST(NULL AS SHORT) AS Relative_Day,
       CAST(NULL AS SHORT) AS Relative_Week,
       CAST(NULL AS SHORT) AS Relative_Period,
       date_format(CURRENT_TIMESTAMP, 'yyyy-mm-dd') AS DP_DATA_DT,
       CURRENT_TIMESTAMP AS DP_LOAD_TS
    FROM Calendar c 
    INNER JOIN CalendarYear cy
    ON cy.CalendarId = c.CalendarId
    INNER JOIN CalendarPeriod cp
    ON cy.CalendarYearId = cp.CalendarYearId
    AND c.CalendarId = cp.CalendarId
    INNER JOIN CalendarQuarter cq
    ON cy.CalendarYearId = cq.CalendarYearId
    AND c.CalendarId = cq.CalendarId
    INNER JOIN CalendarWeek cw
    ON cq.CalendarQuarterId = cw.CalendarQuarterId
    AND cy.CalendarYearId = cw.CalendarYearId
    AND c.CalendarId = cq.CalendarId
    INNER JOIN CalendarDate cd
    ON cw.CalendarWeekId = cd.CalendarWeekId
    AND cq.CalendarQuarterId = cd.CalendarQuarterId
    AND cy.CalendarYearId = cd.CalendarYearId
    AND c.CalendarId = cq.CalendarId
    INNER JOIN DayOfWeek dow
    ON cd.DayOfWeekId = dow.DayOfWeekId
    """

    df = spark.sql(transformation_sql)

    try:
        # Export data to Synapse
        export_to_synapse(
            sdf=df,
            target_schema=trgt_db_nm,
            target_table=trgt_tbl_nm,
            dfw_options=write_options,
            truncate_insert=truncate_insert,
            upsert_keys=upsert_keys
        )
    finally:
        # Restore the Spark configurations
        restore_spark_configs(default_spark_config)
        
    spark.stop()

if __name__ == "__main__":
    main()