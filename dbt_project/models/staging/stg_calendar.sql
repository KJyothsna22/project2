-- Staging model: stg_calendar
-- Standardizes calendar reference data from dim_calendar

WITH source AS (
    SELECT
        date_str,
        wm_yr_wk,
        weekday,
        wday,
        month,
        year,
        d_id,
        event_name_1,
        event_type_1,
        event_name_2,
        event_type_2,
        snap_CA,
        snap_TX,
        snap_WI,
        is_holiday
    FROM dim_calendar
)

SELECT
    date_str,
    CAST(wm_yr_wk AS INTEGER) AS wm_yr_wk,
    weekday,
    CAST(wday AS INTEGER) AS wday,
    CAST(month AS INTEGER) AS month,
    CAST(year AS INTEGER) AS year,
    d_id,
    COALESCE(event_name_1, 'None') AS event_name_1,
    COALESCE(event_type_1, 'None') AS event_type_1,
    COALESCE(event_name_2, 'None') AS event_name_2,
    COALESCE(event_type_2, 'None') AS event_type_2,
    CAST(COALESCE(snap_CA, 0) AS INTEGER) AS snap_CA,
    CAST(COALESCE(snap_TX, 0) AS INTEGER) AS snap_TX,
    CAST(COALESCE(snap_WI, 0) AS INTEGER) AS snap_WI,
    CAST(COALESCE(is_holiday, 0) AS INTEGER) AS is_holiday,
    CASE WHEN wday IN (1, 2) THEN 1 ELSE 0 END AS is_weekend
FROM source
