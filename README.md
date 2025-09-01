# README.md

# 🚀 Portfolio Backend Setup

This is the backend part of my portfolio project.  
I’m documenting everything here so deployment, testing, and future improvements are easier.  

Later I’ll add instructions for the **React frontend, Angular frontend, and Flutter ML parts**.  
For now, this is focused on the **backend + database setup**.

---

## 📦 Requirements

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed
- Python 3.10+  
- Git
- Optional: Virtualenv for running scripts locally (`venv/`)

---

## ⚙️ Environment Setup

First, copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` to set your own values:  

```env
# For Docker Compose to configure the database container
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=portfolio_db
DB_HOST=dashboard_db

# For the FastAPI backend to connect to the database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}
SECRET_KEY=change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

👉 **Tip:** Keep the `.env.example` file. That way anyone who clones the repo knows exactly what to set.

---

## 🐳 Docker Commands (Cheat Sheet)

```bash
# Build and start containers
docker compose up --build -d

# List running containers
docker compose ps

# Follow logs
docker compose logs -f

# Stop and remove containers + volumes
docker compose down -v
docker system prune -a --volumes

# Enter backend container
docker compose exec dashboard_backend bash

# Enter PostgreSQL container
docker exec -it dashboard_db sh
```

---

## 🔧 PostgreSQL Commands

Once inside the container:

```bash
# Connect to DB
psql -U $POSTGRES_USER -d $POSTGRES_DB

# List tables
\dt

# Describe a table
\d <table_name>

# Exit psql
\q
```

Or from host (with env variables loaded):

```bash
docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
```

---

## 📜 Alembic Migrations

```bash
# Show current DB revision
alembic current

# Create new migration from models
alembic revision --autogenerate -m "migration message"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Sync DB with head/base without running migrations
alembic stamp head
alembic stamp base
```

---

## 🐍 Python & FastAPI

- Run Python script inside container:
  ```bash
  python test_insert_user.py
  ```

- API docs:  
  [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3️⃣ What Actually Needs to Do to Start

Here’s the clean workflow:

### Step 0: Clone repo
```bash
git clone <repo>
cd ~/dev-portfolio/
```

### Step 1: Setup (venv optional if you use containers only)

```bash
alias workon="source venv/bin/activate"
cd ~/dev-portfolio/apps/dashboard-admin/backend
workon
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Build & Run Docker
```bash
cd ~/dev-portfolio
docker compose up --build -d
```

### Step 3: Run migrations
```bash
docker compose run --rm dashboard_backend alembic upgrade head
```

### Step 4: (If no tables exist) Generate migration
```bash
docker compose run --rm dashboard_backend alembic revision --autogenerate -m "create users table"
```

### Step 5: Apply migration
```bash
docker compose run --rm dashboard_backend alembic upgrade head
```

You should see something like:

```
INFO  [alembic.runtime.migration] Running upgrade -> c49e82f2d940, create users table
```

### Step 6: Check tables
```bash
docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
```

You should see `users` and `alembic_version`.

### Step 7: Test FastAPI

Create a user:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/users/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "kus4n4g1",
  "email": "sunny071282@gmail.com",
  "password": "Ethan0410",
  "role": "admin"
}'
```

Login for token:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=kus4n4g1&password=Ethan0410'
```

Get current user with token:

```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/users/me/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_token>'
```

---

## ⚡ Quick Start (TL;DR)

1. Install Docker & Docker Compose  
2. Clone repo:  
   ```bash
   git clone ... && cd dev-portfolio
   ```
3. Copy env:  
   ```bash
   cp .env.example .env
   ```
4. Start containers:  
   ```bash
   docker compose up -d --build
   ```
5. Run migrations:  
   ```bash
   docker compose run --rm dashboard_backend alembic upgrade head
   ```
6. Verify DB:  
   ```bash
   docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
   ```
7. Open API docs:  
   [http://localhost:8000/docs](http://localhost:8000/docs)

---

💡 If you get errors:  
- Check `.env` is set correctly  
- Make sure `alembic/versions/` has a valid migration file (`.py`, not `.py~`)  
- Use `docker compose logs dashboard_backend` for debugging  
- Inside container:  
  ```bash
  echo $DB_USER && echo $DB_NAME
  ```

