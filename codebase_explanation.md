# Supply Chain Project: Complete File-by-File Documentation

This document provides a comprehensive description of **every single file** in your project, categorized by its role in the application.

---

## 📂 Root Directory (Configuration & Infrastructure)

| File / Folder | Description |
| :--- | :--- |
| [.env](file:///c:/Users/HP/OneDrive/Desktop/supplychain/.env) | Stores environment variables like database URLs, JWT secrets, and API keys. |
| [.gitignore](file:///c:/Users/HP/OneDrive/Desktop/supplychain/.gitignore) | Lists files and folders that Git should ignore (like `venv/` or `.pyc` files). |
| [alembic.ini](file:///c:/Users/HP/OneDrive/Desktop/supplychain/alembic.ini) | Configuration file for Alembic, used for database migrations. |
| [Dockerfile](file:///c:/Users/HP/OneDrive/Desktop/supplychain/Dockerfile) | Instructions for building a Docker image of the backend. |
| [docker-compose.yml](file:///c:/Users/HP/OneDrive/Desktop/supplychain/docker-compose.yml) | Orchestrates the backend and potentially database containers for development. |
| [requirements.txt](file:///c:/Users/HP/OneDrive/Desktop/supplychain/requirements.txt) | Lists all Python packages required to run the project. |
| [supplychain.db](file:///c:/Users/HP/OneDrive/Desktop/supplychain/supplychain.db) | The main SQLite database file where all your data is stored. |
| [full_schema.db](file:///c:/Users/HP/OneDrive/Desktop/supplychain/full_schema.db) | A backup or alternative version of the database schema. |
| `cd backend.txt` | A simple text file, likely a reminder of the command to enter the backend folder. |
| [email_watcher.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/email_watcher.py) | A background script that monitors an email inbox for CSV attachments to process automatically. |
| [evaluate_model.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/evaluate_model.py) | Script used to test and evaluate the performance of the machine learning models. |
| [seed_inventory.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/seed_inventory.py) | A utility script to populate the database with initial sample inventory data for testing. |
| [upgrade_saas.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/upgrade_saas.py) | A script likely used for upgrading database schemas or migrating data to new versions. |
| [Untitled.ipynb](file:///c:/Users/HP/OneDrive/Desktop/supplychain/Untitled.ipynb) / [Untitled1.ipynb](file:///c:/Users/HP/OneDrive/Desktop/supplychain/Untitled1.ipynb) | Jupyter Notebooks used for data exploration, cleaning, and model prototyping. |
| `*.csv` files | Datasets (e.g., `startup data.csv`, `Supply_list...csv`) used for training models or seeding data. |
| `*.joblib` files | Serialized Machine Learning models (e.g., [funding_predictor.joblib](file:///c:/Users/HP/OneDrive/Desktop/supplychain/funding_predictor.joblib)) ready for prediction. |

---

## 📁 `backend/` (Core Application)

### Top-Level Files
- [app.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/app.py): The main entry point for the FastAPI application. It sets up routes, middleware, and static file serving.
- [auth_utils.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/auth_utils.py): Provides basic password hashing and verification using `bcrypt`.
- [limiter.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/limiter.py): Configures the `slowapi` rate limiter to prevent API abuse.
- [mail_utils.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/mail_utils.py): Contains functions to send emails (OTPs and success confirmations) using SMTP.
- [schemas.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/schemas.py): Defines Pydantic data models for verifying data sent to/from the API.
- [settings.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/settings.py): Centralized configuration management using `pydantic-settings`.
- [create_database.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/create_database.py): A script to initialize the database and create tables from models.

### 📁 `backend/database/` (DB Connection)
- `database.py`: Sets up the SQLAlchemy engine and `SessionLocal` for DB interactions.
- `fix_db.py` / `update_db.py`: Utility scripts for fixing data issues or updating the schema manually.

### 📁 `backend/models/` (Database Tables)
Each file corresponds to a table in the database:
- `user_model.py`: Users, hashed passwords, and company associations.
- `company_model.py`: Basic details about the company using the platform.
- `inventory_model.py`: Products, current stock levels, and reorder points.
- `supplier_model.py` / `customer_model.py`: Details of business partners.
- `sales_model.py` / `invoice_model.py`: Records of sales transactions and billing.
- `logistics_model.py`: Tracking shipments, status, and delivery dates.
- `activity_model.py`: Logs of user activities within the system.
- `automation_model.py`: Settings for automated workflows (like email ingestion).
- `team_invite_model.py`: Tracks pending invites for team members.

### 📁 `backend/routes/` (API Endpoints)
These files define the URLs you visit and what they do:
- `auth_routes.py`: Login, sign-up, and token management.
- `auth_utils.py` (Local): Handles JWT (JSON Web Token) creation for session security.
- `google_auth_routes.py`: Logic for logging in using Google accounts.
- `ai_routes.py`: The "brain" of the app, handling complex analysis and viability checks.
- `inventory_routes.py`: Managing stock (Add/Remove/Update items).
- `sales_routes.py` / `finance_routes.py`: Handling sales data and financial reports.
- `logistics_routes.py`: Updating and tracking shipment statuses.
- `upload_routes.py`: Logic for importing data from CSV files.
- `main_routes.py`: General dashboard statistics and overview data.
- `alert_routes.py`: Managing system alerts and notifications.
- `automation_routes.py`: Configuring and checking background automation status.

---

## 📁 `backend/ml/` (Machine Learning Engine)

- [predict.py](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/ml/predict.py): The core script that takes user input, runs it through the model, and returns a success probability.
- `train_model.py`: The script used to train the Random Forest model on CSV data.
- `analysis.py` / `scoring.py`: Additional logic for analyzing data trends and scoring business performance.
- `features.py`: Defines how raw data is transformed into "features" the model can understand.
- `business_success_model.joblib`: The actual trained intelligence of the app.
- `industry_encoder.joblib`: A helper file that converts industry names (like "Retail") into numbers for the model.

---

## 📁 `backend/static/` (Frontend UI)

- `index.html`: The main dashboard page (requires login).
- `login.html` / `register.html`: The entry points for the system.
- [style.css](file:///c:/Users/HP/OneDrive/Desktop/supplychain/backend/static/style.css): A comprehensive stylesheet that gives the dashboard its modern look.
- `script.js`: The "brain" of the frontend; it handles all interactivity and API calls.
- `illustration.png`: Visual asset used on the login/landing page.

---

## 📁 `tests/` (Verification)

- `conftest.py`: Configuration for Pytest, providing shared "fixtures" for tests.
- `test_auth.py`: Verifies that login, registration, and logout work correctly.
- `test_ai_logic.py`: Ensures the ML prediction logic returns valid results.
- `test_rate_limit.py` / `test_lockout.py`: Security tests to ensure the rate limiter and account lockout logic are functional.

---

## ⚙️ How it Works Internally
The system follows a **FastAPI + SQLAlchemy + Scikit-Learn** pattern:
1. **Frontend Request**: Your browser (`script.js`) sends data to a specific route.
2. **API Layer**: `backend/routes/` receives it, validates the user's token, and checks the data format.
3. **Data Layer**: If saving data, it uses `backend/models/` to write to `supplychain.db`.
4. **AI Layer**: if analyzing data, it sends information to `backend/ml/predict.py`, which uses the pre-trained `joblib` models.
5. **Response**: The result (Success/Fail/Data) is sent back as JSON, which the frontend uses to update the UI instantly.
