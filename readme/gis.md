...existing code...

## PostGIS (local / Ubuntu) — quick setup

If migrations fail with "extension 'postgis' is not available", install PostGIS and enable the extension:

```bash
sudo apt update
sudo apt install postgis postgresql-16-postgis-3
sudo systemctl restart postgresql
sudo -u postgres psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"
python manage.py migrate
```

If you run PostgreSQL in Docker, use a PostGIS-enabled image (e.g. `postgis/postgis:16-3.4`) and run inside the DB container:

```bash
docker-compose up -d db
docker-compose exec db psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
python manage.py migrate
```

...existing code...