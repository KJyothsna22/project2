# Enterprise Cloud Deployment & Migration Guide
## Retail Demand Forecasting & Inventory Optimization Platform

This guide details migrating the local prototype to enterprise cloud data platforms (Snowflake, Google BigQuery, AWS / PostgreSQL).

---

### 1. Cloud Warehouse Migration

#### A. PostgreSQL / Amazon RDS / Aurora
1. Apply the DDL schema in `warehouse/migrations/postgresql_schema.sql`.
2. Configure environment variables:
   ```bash
   export DB_DIALECT="postgresql"
   export PG_HOST="your-db-host.rds.amazonaws.com"
   export PG_PORT="5432"
   export PG_DATABASE="retail_warehouse"
   export PG_USER="admin_user"
   export PG_PASSWORD="your_secure_password"
   ```

#### B. Snowflake Enterprise Data Cloud
1. Execute `warehouse/migrations/snowflake_schema.sql` in Snowsight or via SnowSQL CLI.
2. In `dbt_project/profiles.yml`, switch active target to `snowflake_prod`.
3. Leverage Snowpark Python or AWS ECS / EKS tasks to run `forecasting/train_and_forecast.py`.

#### C. Google Cloud BigQuery
1. Execute `warehouse/migrations/bigquery_schema.sql` in BigQuery console.
2. Utilize BigQuery partitioned tables (`PARTITION BY PARSE_DATE('%Y-%m-%d', date_str)` and clustering on `store_id, cat_id, item_id`) for cost-efficient petabyte-scale queries.

---

### 2. CI/CD & Production Orchestration
- **Airflow / Prefect / Dagster**: Schedule daily runs of `ETLPipeline.run()` and `ForecastingPipeline.run()` at 02:00 UTC after nightly POS sales transactions settle.
- **Containerization**: Use standard Dockerfile:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
  ```
