# Setup & Local Installation Guide
## Retail Demand Forecasting & Inventory Optimization Platform

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Git (optional)

---

### 2. Environment Setup

```bash
# 1. Clone repository or navigate to workspace directory
cd project2

# 2. (Optional) Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

---

### 3. Running the Complete Platform

#### Step 1: Run End-to-End Pipeline
Executes data generation/extraction, ETL cleaning, data quality validation checks, dbt data transformations, Prophet & LightGBM model training, holdout evaluation, multi-horizon forecast generation, and inventory replenishment optimization:

```bash
python run_pipeline.py
```

#### Step 2: Launch the Streamlit Dashboard
Launch the multi-page interactive web interface:

```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

### 4. Demo Login Credentials

The platform implements role-based access control (RBAC):

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access, re-run full pipeline, inventory overrides, exports |
| **Inventory Manager** | `manager` | `manager123` | Forecast explorer, replenishment planning, scenario simulations |
| **Viewer** | `viewer` | `viewer123` | Read-only executive dashboard, accuracy benchmarks, report downloads |

---

### 5. Running Automated Unit Tests
To verify all modules and unit test assertions:

```bash
python -m pytest tests/ -v
```
