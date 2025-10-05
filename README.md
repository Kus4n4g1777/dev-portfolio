# README.md

# 🚀 Portfolio Fullstack Setup

This repository now includes backend + database + Angular frontend + React frontend.

I’m documenting everything here so deployment, testing, and future improvements are easier. This includes notes about version switching between different projects and environments, as well as troubleshooting steps for Windows Docker setups. 

---

## 📦 Requirements

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed
- Python 3.10+  
- Node.js (modern project version, switching between works)
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

# New variables for the Oracle database
ORACLE_PASSWORD=your_oracle_password
ORACLE_XE_DB=XEPDB1 # Default database for Oracle XE or yours

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

### Step 6: Check tables
```bash
docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
```

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

## 🖥 Frontend Setup Notes

We now have **two frontend projects** in this repo:
- `dashboard-admin/frontend` → Angular Dashboard
- `portfolio/frontend` → React Users View

### Notes on Node Versions & Switching
- The projects may require **different Node.js versions**.
- Use `nvm` to switch between versions when working across projects:

```bash
nvm install <version>
nvm use <version>
```

- Always install dependencies after switching:

```bash
npm install
```

### Angular Frontend (Dashboard)
1. Navigate to `apps/dashboard-admin/frontend`
2. Build production:
```bash
ng build --configuration production
```
3. Add Angular frontend to Docker Compose:
```yaml
services:
  dashboard_frontend:
    build: ./apps/dashboard-admin/frontend
    ports:
      - 4200:80
```

### React Frontend (Users View)
1. Navigate to `apps/portfolio/frontend`
2. Build production:
```bash
npm run build
```
3. Add React frontend to Docker Compose:
```yaml
services:
  portfolio_frontend:
    build: ./apps/portfolio/frontend
    ports:
      - 3000:80
```

💡 **Tip:** Build each frontend **before starting Docker Compose** to ensure images are up-to-date.

---

## ⚡ Version Switching Notes

- Node.js and Angular CLI versions may differ between projects.
- Use `nvm` to switch Node.js versions:
```bash
nvm use <version>
```
- Reinstall Angular CLI if switching projects with a different Node version:
```bash
npm install -g @angular/cli
```
- Always verify frontend builds after switching versions.

---

## 🔥 Troubleshooting / Notes from this Setup

- Docker Desktop must be running before building images.
- If you get `ng` not found, ensure Angular CLI is installed globally:
```bash
npm install -g @angular/cli
```
- Pay attention to the **correct Node.js version** per project.
- Check Docker logs for container health:
```bash
docker compose logs -f
```
- Sometimes container names and networks are automatically generated; verify `docker compose ps`.
- Windows CRLF issues can silently break builds; always convert `.env` and scripts to LF.
- Convert `.env` and shell scripts to **LF endings** (VSCode or `git config --global core.autocrlf input`).
- Use **double `$`** in docker-compose to escape variables:
```yaml
healthcheck:
  test: pg_isready -U $${DB_USER} -d $${DB_NAME} || exit 1
```
- Check logs for container health:
```bash
docker compose logs -f
```
---

# 📝 Git Line Endings & Normalization Guide

This guide explains how to handle **line endings (CRLF vs LF)** in a cross-platform project, ensuring Docker, backend, and frontend files work on **Windows and Linux** without Git or Docker breaking. It also includes the exact **sequence we use** to stage, normalize, and commit files safely.

---

## 1️⃣ Background: CRLF vs LF

- **Windows** uses **CRLF** (`\r\n`)  
- **Linux/macOS/Docker containers** expect **LF** (`\n`)  

If you commit CRLF files but your containers/scripts expect LF, you can see:

- Docker or shell scripts failing
- PostgreSQL / FastAPI not starting
- Errors like:

```
FATAL: role "-d" does not exist
```

This usually comes from a `.env` or shell script with CRLF endings.

---

## 2️⃣ `.gitattributes` Setup

To **force LF endings** for important files and **normalize line endings**, add a `.gitattributes` file at the repo root:

```text
# Force LF for shell scripts, Dockerfiles, env files
*.sh text eol=lf
*.env text eol=lf
Dockerfile text eol=lf
docker-compose*.yml text eol=lf

# Optional: force LF for JSON/TS/JS (frontend)
*.json text eol=lf
*.ts text eol=lf
*.js text eol=lf
*.html text eol=lf
*.css text eol=lf
```

**Why:**  
- Ensures everyone (Windows/Linux) commits files with LF endings  
- Prevents silent Docker/DB/backend errors  
- Avoids git warnings when staging and committing  

---

## 3️⃣ Normalization Sequence (Safe Commit)

When you have mixed line endings or CRLF warnings, do the following:

### Step 1: Unstage everything

```bash
git reset
```

This moves all staged changes back to the working directory.  

### Step 2: Apply `.gitattributes` rules to all files

```bash
git add --renormalize .
```

**What this does:**  
- Forces Git to re-check all files according to `.gitattributes`  
- Converts files with CRLF → LF automatically (if the rules say `eol=lf`)  
- Prepares them for a clean commit  

### Step 3: Stage frontend, Dockerfiles, and Compose

```bash
git add apps/dashboard-admin/frontend/
git add apps/portfolio/Dockerfile
git add .gitattributes docker-compose.yml
```

**Note:** You may see warnings like:

```
warning: in the working copy of 'apps/dashboard-admin/frontend/package.json', LF will be replaced by CRLF the next time Git touches it
```

✅ This is normal and **safe**, because `.gitattributes` will enforce LF on commit.

### Step 4: Verify staged files

```bash
git status
```

You should see:

- **Changes to be committed** → `.gitattributes`, Dockerfiles, docker-compose.yml, all frontend files  
- **No unintentional CRLF files left behind**

### Step 5: Commit

```bash
git commit -m "Add frontend files, update docker-compose, normalize line endings"
```

---

## 4️⃣ Tips & Best Practices

- Always commit `.gitattributes` **before adding new files**
- Convert `.env` and shell scripts to LF manually if editing on Windows
- Use VSCode **“LF” line endings** option
- Set Git globally to avoid CRLF problems:

```bash
git config --global core.autocrlf input
```

- For Docker Compose healthchecks, escape variables on Windows:

```yaml
healthcheck:
  test: pg_isready -U $${DB_USER} -d $${DB_NAME} || exit 1
```

- After this normalization, future commits **won’t trigger CRLF warnings**  

---

### ✅ Bottom Line

This process ensures:

- All scripts, Dockerfiles, env files, and frontend files have **LF endings**
- Docker, PostgreSQL, FastAPI, and Oracle containers run **without errors**
- Cross-platform development is smooth (Windows ↔ Linux)

### Healthchecks & Initialization

- Ensure DB containers are healthy before backend starts.
- If migrations fail, check `.env` and line endings.
- Always confirm container ports do not conflict.

### 💾 Git Notes

- Commit only `.env.example`, **not real `.env`**.
- Commit any config fixes (docker-compose.yml, scripts with LF endings).
- Do **not commit secrets** — it’s dangerous.

---

## Quick TL;DR Start

```bash
# Clone repo
git clone <repo> && cd dev-portfolio

# Copy env
cp .env.example .env

# Build & run all containers
docker compose up -d --build

# Run backend migrations
docker compose run --rm dashboard_backend alembic upgrade head

# Verify tables
docker compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"

# Access API docs
http://localhost:8000/docs
```

---

### ✅ Notes for recent implementations.

- Frontend Angular → `dashboard_frontend` (port 4200)
- Frontend React → `portfolio_frontend` (port configured in docker-compose)
- Backend FastAPI → `dashboard_backend` (port 8000)
- DBs healthy and containers linked via Docker Compose network
- Oracle-DB → `oracle-db` pending user creation script. 

---

🎉 All services are now running, ready for testing, development, and commits.

# Oracle XE Setup

- Container runs Oracle XE with PDB `XEPDB1`.
- Includes initial script for user creation.
- Pending: automatic execution of user creation script at container startup.

## Flutter and React integration with Fast API

This part of the README consolidates **everything we did** to achieve the Flutter and React frontend connections with FastAPI backend, including Docker setup, styling adjustments, login handling, challenges, troubleshooting, and temporary workarounds.

---

## Flutter Frontend

### 1. Initial Setup & API Service
- Created `ApiService` class to handle login, token storage, and protected route requests.
- Base URL set dynamically for Android emulator and local environment:
```dart
static String get baseUrl {
  if (Platform.isAndroid) return "http://10.0.2.2:8000";
  return "http://127.0.0.1:8000";
}
```
- Used `SharedPreferences` to store JWT token locally.
- Added console prints for debugging connection issues.

### 2. Connecting to FastAPI
- Added CORS origins to allow connections from emulators and frontend:
```python
origins = [
    "http://localhost",
    "http://127.0.0.1:5173",
    "http://10.0.2.2:8000",   # Flutter emulator
    "http://127.0.0.1:8000"
]
```
- Initial issue: `404` or `401` due to incorrect URL or token usage.
- Verified endpoints with ping tests and prints.

### 3. Emulator & Disk Space Challenges
- Android Studio emulator was moved to a different drive due to small disk space.
- Docker volumes and container sizes monitored to avoid filling up disk.
- Temporary solution: manual cleanup using:
```bash
docker system prune -af --volumes
```
- Pending improvement: automated Python script for safe volume cleanup.

### 4. Key Learnings
- Localhost vs emulator IP (`127.0.0.1` vs `10.0.2.2`) is critical.
- Always log network requests and token values for debugging.
- Flutter + FastAPI integration requires careful CORS configuration.

---

## React Frontend

### 1. Initial Setup
- Project created using Vite with TailwindCSS and React Router.
- `AuthContext` implemented for login, token management, and protected routes.
- Routing configured for `/login`, `/dashboard`, `/blog`, `/projects`, `/tests`.

### 2. Login Screen
- Improved styling using Tailwind:
  - Centered card layout
  - Rounded inputs with hover/focus states
  - Error messages displayed below the form
- Attempted icon usage (`lucide-react`), faced Node version compatibility issues.
- Resolved temporarily by adjusting Node version in Docker for frontend.

### 3. Header & Navigation Styling
- Issues with navigation bar appearance (small centered box).
- Adjustments:
  - Added width, padding, and flex spacing
  - Hover effects for `.nav-item` and `.nav-link`
  - Custom colors for improved contrast

### 4. Connecting to FastAPI
- URL handling for dev and Docker:
```js
const baseUrl = Platform.isAndroid ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000";
```
- CORS configuration in FastAPI to allow React local ports.
- `401 Unauthorized` fixed by fetching token correctly on component mount:
```js
useEffect(() => {
  const tokenFromStorage = localStorage.getItem('token');
  if (tokenFromStorage) fetchUserFromToken(tokenFromStorage);
}, []);
```

### 5. Docker & Disk Space Issues
- Containers sometimes failed to start due to low disk space.
- Commands used for cleanup:
```bash
docker system prune -af --volumes
```
- Recommendation: move Docker virtual disk to larger drive, monitor volume usage.
- Pending: safe Python cleanup script for production.

### 6. Tailwind Styling Tips
- Ensure `@tailwind base; @tailwind components; @tailwind utilities;` in `index.css`.
- Check `className` strings for spacing/margin/padding conflicts.
- Add console logs to debug class application.

### 7. Key Learnings
- React + Tailwind + FastAPI integration requires correct CORS and URL handling.
- `useEffect` dependencies are critical to fetch data after login/token update.
- Disk space issues in Docker can silently break builds.
- Console logging is essential for debugging API requests and token flows.

---

## General Docker Notes

### Issues Encountered
- Containers failed with `commit failed: write ... input/output error` due to disk space.
- Docker Desktop froze; manual restart was required.
- Some services (e.g., `com.docker.service`) could not be stopped via PowerShell.

### Temporary Solutions
- Closed Docker Desktop from taskbar and restarted.
- Pruned volumes, containers, and images manually.
- Confirmed frontend connection after cleanup.

### Recommendations for Production
- Bind a safe cleanup script inside Docker Compose to remove unused volumes and images.
- Monitor disk space to avoid failed container builds.
- Ensure Node and npm versions inside Docker match frontend dependency requirements.

### Recommendations to remove warnings about what we setup at gitattributes to handle clrf and lf lines issue
- Set Git to automatically handle line endings
```On Windows
git config --global core.autocrlf true
```
- This converts LF → CRLF on checkout, CRLF → LF on commit.
- After this, the warnings will mostly disappear.
---

# Dashboard Admin Backend - Docker & Python Upgrade Guide

This document explains the steps taken to upgrade the backend Docker container to Python 3.11, pin dependencies, and ensure reproducible builds. It also includes tests, issues found, and recommendations for future improvements.

---

## 1. Upgrade Python Version

**Current:** 3.12 (was used in some containers previously)

**Action:** Downgraded to Python 3.11 to ensure compatibility with `bcrypt` and FastAPI dependencies.

```dockerfile
# Use official Python image
FROM python:3.11-slim

WORKDIR /app
```

**Reasoning:**
- `bcrypt` had issues with Python 3.12.
- 3.11 is stable and widely supported by current dependencies.

---

## 2. Pinning Dependencies

**Action:** After building the container and verifying versions:
```bash
pip freeze > requirements_frozen.txt
```
- This file captures the exact versions installed in the container.

**Example pinned versions (partial):**
```
bcrypt==4.0.1
fastapi==0.118.0
passlib==1.7.4
SQLAlchemy==2.0.43
```

**Recommendation:** Pin all major dependencies to avoid future breaking changes.

**Update `requirements.txt` in backend:**
```powershell
Move-Item -Path requirements_frozen.txt -Destination requirements.txt -Force
```

---

## 3. Rebuild Docker Container

```bash
docker compose build --no-cache dashboard_backend
docker compose up -d
```

**Test:**
- Access `http://localhost:8000/docs` to ensure FastAPI server runs.
- Check logs:
```bash
docker logs dashboard_backend
```
- Verify bcrypt hashing works (test creating a user via POST `/users/`).

**Issue found:**
- `ValueError: password cannot be longer than 72 bytes` when using bcrypt.
  - Solution: truncate passwords to 72 characters in backend before hashing.

---

## 4. Tests & Verification

**Check Python & bcrypt version in container:**
```bash
docker exec -it dashboard_backend bash
python --version
python -m pip show bcrypt
```

**Ensure requirements are frozen:**
```bash
pip freeze > requirements_frozen.txt
```
- Compare with current `requirements.txt` to ensure consistency.

**API test:**
POST to `/users/` with:
```json
{
  "username": "kus4n4g1",
  "email": "sunny071282gmail.com",
  "password": "Ethan0410",
  "role": "admin"
}
```
- Verify 200 OK and hashed password in DB.

---

## 5. Issues & Recommendations

**Issues found:**
1. `bcrypt` incompatible with Python 3.12.
2. Password length restriction (72 bytes) not handled.
3. `requirements.txt` not pinned initially.

**Recommendations:**
- Always pin dependency versions using `pip freeze` after installing in container.
- Use a separate frozen requirements file (`requirements_frozen.txt`) as backup.
- Add a CI/CD check to rebuild Docker image and verify API endpoints automatically.
- Optionally, add a pre-commit hook to run `pip freeze > requirements_frozen.txt` whenever dependencies are updated.
- Truncate or validate password length before hashing to avoid bcrypt errors.

---

## 6. Summary for Future Reference

- Python 3.11 is stable for this project.
- All dependencies are now pinned and reproducible.
- Docker container can be rebuilt with `--no-cache` to verify fresh installs.
- Tests include API POST request and checking container logs.
- Recommendations ensure future developers (or recruiters reviewing this) can follow the steps easily.

## Summary & Next Steps
- **Flutter frontend:** successfully connected to FastAPI with proper token handling and CORS configuration.
- **React frontend:** login, navigation, styling, and FastAPI connection fully functional.
- **Challenges faced:** Node version compatibility, Tailwind styling, emulator IP vs localhost, Docker disk space, frozen Docker Desktop.
- **Pending:** integration of automated tests, automated cleanup script, integration of ML/AI, Node upgrade in Docker, further UI improvements (icons, enhanced login styling), integration with rest of the services, .

---

This README serves as a complete record of integration steps, troubleshooting, and lessons learned from our last commits for both Flutter and React frontends with Docker + FastAPI backend.

