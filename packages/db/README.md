# Database Package

This package is the **single source of truth** for all database schema definitions and migrations in the Stranger Beers ecosystem.

## Structure

```
db/
├── migrations/     # Database migrations (Alembic or similar)
├── schema/         # Schema definitions, models, and SQL files
├── pyproject.toml  # Package dependencies
└── README.md
```

## Purpose

- **Centralized Schema**: All apps in the monorepo reference this package for database models
- **Migration Management**: Database migrations are managed here and applied consistently across environments
- **Type Safety**: Shared SQLAlchemy models ensure type consistency across services

## Usage

Other apps in the monorepo can depend on this package:

```toml
[project.dependencies]
stranger-beers-db = { path = "../../packages/db", develop = true }
```

## Migrations

```bash
# Create a new migration
make db-migrate message="Add users table"

# Apply migrations
make db-upgrade

# Rollback
make db-downgrade
```

## Guidelines

1. **Never modify schema directly in app code** - always update here first
2. **Test migrations** in a local environment before deploying
3. **Document breaking changes** in migration files
