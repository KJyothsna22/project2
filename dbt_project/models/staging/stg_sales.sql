-- Staging model: stg_sales
-- Standardizes raw sales records from fact_sales

WITH source AS (
    SELECT
        id,
        item_id,
        dept_id,
        cat_id,
        store_id,
        state_id,
        date_str,
        sales_units
    FROM fact_sales
)

SELECT
    id,
    item_id,
    dept_id,
    cat_id,
    store_id,
    state_id,
    date_str,
    CAST(sales_units AS INTEGER) AS sales_units,
    CASE WHEN sales_units > 0 THEN 1 ELSE 0 END AS is_active_sale
FROM source
