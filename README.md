# TeamFlowAPI

[![CI](https://github.com/Dubne/TeamFLowAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/Dubne/TeamFLowAPI/actions/workflows/ci.yml)

A REST API for team and project management, featuring role-based access control, task management, SLA tracking, comments, attachments, activity logs, and project statistics.

Built with Django REST Framework as a portfolio project.

## Features

- **Authentication:** JWT authentication with registration, login, token refresh, and logout with token blacklisting (Djoser + SimpleJWT).
- **Teams and roles:** Team management with `OWNER`, `ADMIN`, `MEMBER`, and `VIEWER` roles; invitations with acceptance, rejection, and expiration; ownership transfer.
- **Projects and tasks:** Project and task management, priorities, SLA deadlines calculated based on task priority, member-based task assignment, and status transitions.
- **Statistics:** Project statistics using Django ORM aggregation, cached in Redis.
- **Filtering and pagination:** Filtering, search, ordering, and pagination for list endpoints.
- **Background processing:** Asynchronous notification tasks with Celery and periodic SLA checks with Celery Beat.
- **Rate limiting:** Request throttling backed by Redis.
- **API documentation:** OpenAPI schema and interactive Swagger UI powered by drf-spectacular.
- **Code quality:** Pytest test suite, Ruff linting, GitHub Actions CI, and Docker Compose.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Programming language |
| Django | Backend framework |
| Django REST Framework | REST API development |
| PostgreSQL | Relational database |
| Redis | Caching and message broker |
| Celery | Background task processing |
| Celery Beat | Periodic task scheduling |
| Djoser | Authentication endpoints |
| SimpleJWT | JWT authentication |
| django-filter | API filtering |
| drf-spectacular | OpenAPI documentation |
| Gunicorn | WSGI application server |
| WhiteNoise | Static file serving |
| Pytest | Automated testing |
| Docker Compose | Local development environment |
| GitHub Actions | CI automation |

## Architecture

The application uses a modular architecture with business logic separated from HTTP handling and database queries.

### Request flow

```text
HTTP Request
    |
    v
View / ViewSet
    |
    v
Permissions
    |
    v
Serializer
    |
    v
Service
    |
    v
Selector
    |
    v
Django ORM
    |
    v
PostgreSQL
```

- **Views / ViewSets:** Handle HTTP requests and responses.
- **Permissions:** Enforce access restrictions at the API level.
- **Serializers:** Validate input data and define response representations.
- **Services:** Contain business logic, role checks, transactions, and activity logging.
- **Selectors:** Encapsulate database read operations and query optimizations.
- **Models:** Define the database structure and relationships.

Redis is used for caching and as a message broker. Celery workers process background tasks, while Celery Beat schedules periodic jobs.

### Project structure

```text
TeamFlowAPI/
├── apps/
│   ├── users/          # Custom user model and user-related functionality
│   ├── teams/          # Teams, memberships, and invitations
│   ├── projects/       # Projects and project statistics
│   ├── tasks/          # Tasks, comments, tags, and attachments
│   ├── activity/       # Activity log
│   └── notifications/  # Background notification tasks
├── core/               # Shared permissions and utilities
├── deploy/             # Deployment scripts and configuration
├── tests/              # Automated tests
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

## Roles and Permissions

| Action | Owner | Admin | Member | Viewer |
|---|---|---|---|---|
| Read team data | Yes | Yes | Yes | Yes |
| Create tasks, comments, tags, and attachments | Yes | Yes | Yes | No |
| Assign tasks, create projects, and invite members | Yes | Yes | No | No |
| Remove members (excluding privileged roles) | Yes | Yes* | No | No |
| Change roles and transfer ownership | Yes | No | No | No |

*Admins can remove members and viewers, but cannot remove the owner or other admins.*

## Design Decisions

### Services and selectors instead of business logic in views

Business logic is separated into services, while selectors handle database read operations. This keeps views focused on HTTP handling and makes business logic easier to test and maintain.

### Separate API permissions from business-level role checks

API permissions handle general access restrictions, such as team membership. Services enforce role-based business rules for individual operations. This separation keeps authorization logic organized and reusable.

### Activity logging within the same database transaction

Activity log entries are created within the same transaction as the corresponding operation. This ensures that an action and its log entry are committed or rolled back together.

## API Overview

Interactive API documentation is available at `/api/docs/`.

| Resource | Main endpoints |
|---|---|
| Authentication | `/api/auth/users/`, `/api/auth/jwt/create/`, `/api/auth/jwt/refresh/`, `/api/auth/logout/` |
| Teams | `/api/teams/`, `/api/teams/{id}/members/`, `/api/teams/{id}/invitations/` |
| Projects | `/api/projects/`, `/api/projects/{id}/statistic/` |
| Tasks | `/api/tasks/`, `/api/tasks/{id}/assign/`, `/api/tasks/{id}/change-status/` |
| Collaboration | `/api/tasks/{id}/comments/`, `/api/tasks/{id}/attachments/`, `/api/tasks/{id}/activity/` |

See the Swagger documentation for available operations, request parameters, and response schemas.

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Dubne/TeamFLowAPI.git TeamFlowAPI
cd TeamFlowAPI
```

2. Create the environment configuration:

```bash
cp .env.example .env
```

3. Configure the required environment variables in `.env`.

4. Build and start the services:

```bash
docker compose up --build -d
```

5. Apply database migrations (if they are not applied automatically during startup):

```bash
docker compose exec web python manage.py migrate
```

6. Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

### Access the application

- **API:** `http://localhost:8000/`
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **Django Admin:** `http://localhost:8000/admin/`

## Configuration

Copy `.env.example` to `.env` and configure the required variables.

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Enables or disables debug mode |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_HOST` | Database host |
| `POSTGRES_PORT` | Database port |
| `REDIS_URL` | Redis connection URL |

Docker Compose provides the appropriate internal service hostnames and connection settings for the application containers.

Never commit your actual `.env` file or production secrets to the repository.

## Running Tests

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=apps
```

Tests use PostgreSQL as the database backend. Redis-dependent functionality is configured to use an in-memory cache, and Celery tasks run in eager mode during tests.

Make sure the required PostgreSQL test database is available and the test environment is configured correctly.

## CI/CD

GitHub Actions runs the following checks on pushes and pull requests:

- Ruff linting.
- Django migration consistency checks.
- Pytest suite against PostgreSQL.
- Docker Compose smoke test.

On pushes to `main`, the Docker image is published to GitHub Container Registry (GHCR).

A deployment job using SSH and Docker Compose is implemented but currently disabled because the application is not deployed to a remote server. Enabling it requires configuring the necessary GitHub Actions variables and secrets, as well as preparing the target server.

## Limitations and Future Improvements

- Uploaded files are stored but are not served directly by the application. A production deployment would require a dedicated solution such as Nginx or object storage.
- Project statistics use TTL-based caching, so returned values may be temporarily stale.
- The application has not been deployed to a live server.
- Potential future improvements:
  - WebSocket support for real-time task updates.
  - Full-text search.
  - Object storage integration for attachments.
  - Production deployment and monitoring.