# Stranger Beers

A monorepo for the Stranger Beers ecosystem - connecting strangers over beers.

## Project Structure

```
stranger_beers_app/
├── apps/
│   ├── ingestion_api/      # FastAPI webhook receiver for Tally forms
│   ├── matching_service/   # Service for pairing participants
│   ├── comms_service/      # WhatsApp/email notifications
│   ├── admin_dashboard/    # Web UI (Next.js - future)
│   └── icebreaker_game/    # Static frontend app (future)
├── packages/
│   ├── shared/             # Shared Python utilities
│   └── db/                 # Database schema and migrations
├── infra/
│   └── docker/             # Docker configurations
├── docs/                   # Documentation
└── tests/                  # Integration tests
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Install dependencies
make setup

# Or manually with uv
uv sync --all-packages
```

### Development

```bash
# Run linting
make lint

# Format code
make format

# Run type checks
make type-check

# Run tests
make test

# Run all checks
make check
```

### Running Services

```bash
# Start the ingestion API
make run-ingestion

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `TALLY_SIGNING_SECRET` | Webhook signing secret from Tally |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Apps

### Ingestion API

FastAPI service that receives Tally form submissions via webhooks and stores registrations in the database.

**Endpoints:**
- `GET /health` - Health check
- `POST /webhooks/tally` - Receive Tally form submissions
- `GET /docs` - OpenAPI documentation

### Matching Service

(Coming soon) Batch job that reads registrations and creates matches between participants.

### Communications Service

(Coming soon) Service for sending WhatsApp messages and emails to matched participants.

## Packages

### shared

Common utilities used across all services:
- Phone number normalization (E.164 format)
- Pydantic types for validation
- Logging configuration

### db

Database schema definitions and migrations. Single source of truth for all database models.

## Tech Stack

- **Python 3.11+** - Primary language
- **FastAPI** - API framework
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **PostgreSQL** - Database
- **uv** - Package management
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **pytest** - Testing
