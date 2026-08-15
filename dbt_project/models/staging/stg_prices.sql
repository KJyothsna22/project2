-- Staging model: stg_prices
-- Standardizes weekly sell prices from fact_prices

WITH source AS (
    SELECT
        store_id,
        item_id,
        wm_yr_wk,
        sell_price
    FROM fact_prices
)

SELECT
    store_id,
    item_id,
    CAST(wm_yr_wk AS INTEGER) AS wm_yr_wk,
    CAST(sell_price AS NUMERIC(10, 2)) AS sell_price
FROM source
