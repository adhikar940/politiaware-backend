# Adhikar - Politiaware Backend

Welcome to the **Adhikar (Politiaware Backend)** project!  
This repository provides the backend API and services for the Politiaware platform.

---

## 📚 Documentation Sections

| Topic | Description |
|---|---|
| [Execution Steps](#-execution-steps) | Quick start guide for local and Docker setup |
| [Requirements Guide](readme/requirements.md) | Python dependencies and compilation instructions |
| [Changelog](changelog.md) | Detailed record of changes across versions |
| [GIS & Boundaries](readme/gis.md) | Spatial data, shapefiles, and PostGIS documentation |
| [Database Documentation](docs/db_readme.md) | Database backup, restore, and dump instructions |
| [Release Plan](releaseplan.md) | Release phases and milestones |
| [Roadmap](roadmap.md) | Future features and development roadmap |
| [Generic GraphQL & Introspection](politiaware_backend/generic_graphql/README.md) | GraphQL queries, dynamic filters, mutations, and introspection guide |

---

## 🚀 Execution Steps

### 1. Prerequisites
- **Python**: Python 3.14+ 
- **Database**: PostgreSQL with PostGIS extension enabled
- **System Libraries** (for GeoDjango / GIS support):
  - Ubuntu/Debian: `sudo apt-get install binutils libproj-dev gdal-bin libgdal-dev`
- **Docker & Docker Compose** *(Optional, if running via containers)*

---

### 2. Local Environment Setup

#### Step 1: Clone and Navigate to Repository Root
```bash
cd politiaware-backend
```

#### Step 2: Create and Activate Virtual Environment
- **Linux / macOS:**
  ```bash
  python3 -m venv env
  source env/bin/activate
  ```
- **Windows:**
  ```cmd
  python -m venv env
  env\Scripts\activate
  ```

#### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r p3.14requirements.txt
```
> **Tip:** You can also install in editable mode with `pip install -e .` or generate/update requirements using `pip-tools` (see [Requirements Guide](readme/requirements.md)).

#### Step 4: Configure Environment Variables
Ensure a `.env` file exists in the project root directory with your database and environment settings:
```env
ENVIRONMENT=local
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=adhikar_local
POSTGRES_SCHEMA=public
```

#### Step 5: Run Database Migrations
You can run migrations either from the repository root or from the `politiaware_backend` directory:

- **Option A (From Project Root):**
  ```bash
  python politiaware_backend/manage.py migrate
  ```
- **Option B (From `politiaware_backend/` Directory):**
  ```bash
  cd politiaware_backend
  python manage.py migrate
  ```

#### Step 6: Create Admin User (Optional)
```bash
# From project root:
python politiaware_backend/manage.py createsuperuser

# Or inside politiaware_backend directory:
python manage.py createsuperuser
```

#### Step 7: Start Development Server
- **From Project Root:**
  ```bash
  python politiaware_backend/manage.py runserver
  # Or specify host and port:
  python politiaware_backend/manage.py runserver 0.0.0.0:8000
  ```
- **From `politiaware_backend/` Directory:**
  ```bash
  cd politiaware_backend
  python manage.py runserver 0.0.0.0:8000
  ```

#### Step 8: Run with Gunicorn (Production / WSGI)
```bash
cd politiaware_backend
gunicorn --bind 0.0.0.0:8000 m.wsgi:application
```

---

### 3. Running with Docker

#### Option A: Using Docker Compose (Recommended)
Docker Compose starts the backend service along with pgAdmin:

```bash
# Build and run containers
docker compose up --build

# Run in detached (background) mode
docker compose up -d

# Stop running containers
docker compose down
```

- **Backend API:** `http://localhost:8000`
- **pgAdmin 4:** `http://localhost:5050` (Login: `admin@example.com` / `admin`)

#### Option B: Standalone Docker Build & Run
```bash
# 1. Build the Docker image
docker build -t politiaware-backend .

# 2. Run the Docker container
docker run -d --name politiaware_container \
  -p 8000:8000 \
  --env-file .env \
  politiaware-backend
```

---

## 🛠 Useful Django Commands

| Action | Command (from root) | Command (inside `politiaware_backend/`) |
|---|---|---|
| Create Migrations | `python politiaware_backend/manage.py makemigrations` | `python manage.py makemigrations` |
| Apply Migrations | `python politiaware_backend/manage.py migrate` | `python manage.py migrate` |
| Collect Static Files | `python politiaware_backend/manage.py collectstatic --noinput` | `python manage.py collectstatic --noinput` |
| Load App Data | `python politiaware_backend/manage.py loaddata data.json` | `python manage.py loaddata data.json` |
| Load Party Fixtures | `python politiaware_backend/manage.py loaddata party_fixture.json` | `python manage.py loaddata party_fixture.json` |
| Load States & Districts Fixtures | `python politiaware_backend/manage.py loaddata state_fixture.json state_map_fixture.json districts_fixture.json district_map_fixture.json` | `python manage.py loaddata state_fixture.json state_map_fixture.json districts_fixture.json district_map_fixture.json` |
| Load Lok Sabha Fixtures | `python politiaware_backend/manage.py loaddata loksabha_constituency_fixture.json loksabha_constituency_map_fixture.json loksabhamp_fixture.json` | `python manage.py loaddata loksabha_constituency_fixture.json loksabha_constituency_map_fixture.json loksabhamp_fixture.json` |
| Load All Fixtures | `python politiaware_backend/manage.py loaddata party_fixture.json state_fixture.json state_map_fixture.json districts_fixture.json district_map_fixture.json loksabha_constituency_fixture.json loksabha_constituency_map_fixture.json loksabhamp_fixture.json` | `python manage.py loaddata party_fixture.json state_fixture.json state_map_fixture.json districts_fixture.json district_map_fixture.json loksabha_constituency_fixture.json loksabha_constituency_map_fixture.json loksabhamp_fixture.json` |
| Run Django Shell | `python politiaware_backend/manage.py shell` | `python manage.py shell` |

---

## 📦 Installed Apps Overview

- `area_pop`: Administrative regions and boundaries (State, District, City, etc.)
- `assembly`: Legislative assembly constituency data
- `citizen`: Citizen services and user profiles
- `cm`: Chief Minister office records and metadata
- `council`: Council administrative data
- `executive_leaders`: Information on executive leaders
- `governor`: Governor office details
- `loksabha`: Lok Sabha parliamentary constituency data
- `maps`: Spatial mapping and GeoJSON / GIS services
- `party`: Political parties details and data
- `person`: Profiles and biographical records
- `president` / `vicepresident`: Presidential and Vice-Presidential offices data
- `rajyasabha`: Rajya Sabha members and constituency information
- `session_info`: Legislative session and assembly sessions tracking