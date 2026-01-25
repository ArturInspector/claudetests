# Dev commands

default:
    @just --list

# Start all services
up:
    docker-compose up -d

# Stop all services
down:
    docker-compose down

# View logs
logs service="api":
    docker-compose logs -f {{service}}

# Rebuild and start
rebuild:
    docker-compose up -d --build

# Run backend tests
test:
    cd backend && pytest -v

# Run migrations
migrate:
    docker-compose exec api alembic upgrade head

# Create new migration
migration name:
    docker-compose exec api alembic revision --autogenerate -m "{{name}}"

# Open psql shell
psql:
    docker-compose exec postgres psql -U app -d socratic

# Install CLI locally
cli-install:
    cd cli && pip install -e .

# Format code
fmt:
    cd backend && ruff format .
    cd backend && ruff check --fix .

# Lint
lint:
    cd backend && ruff check .
    cd backend && mypy app/

# Clean
clean:
    docker-compose down -v
    rm -rf backend/__pycache__ backend/.pytest_cache
    rm -rf frontend/node_modules frontend/.next

