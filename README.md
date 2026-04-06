# Personal Finance Dashboard Backend

A robust, type-safe API built with **FastAPI** for managing financial records and generating dashboard analytics.

## Tech Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL (with Asyncpg driver)
- **ORM:** SQLAlchemy (Async)
- **Migrations:** Alembic
- **Testing:** Pytest & HTTPx
- **Authentication:** JWT (Python-JOSE) with Bcrypt password hashing

## Architecture & Design Decisions

### 1. Robust Currency Storage
Floating point calculations often lead to precision errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). 
To prevent monetary loss or inaccuracies, the backend enforces the following standard:
- **Database Layer**: All monetary amounts are stored as integers (`cents`).
- **Application Layer**: Business logic correctly aggregates using integer/cents arithmetic.
- **REST API Layer**: Uses Python's exact `Decimal` module at the JSON boundaries to automatically format values into proper real-world constraints (e.g., `$10.50`), validated strictly to `max 2 decimal places`.

### 2. Role-Based Access Control (RBAC) & Data Scoping
To satisfy strict multi-tenant access:
- **Admins** have unimpeded access to list, view, edit, or soft-delete any user's records.
- **Viewers & Analysts** are restricted entirely to interacting with data tied to their own authenticated user ID. Any `GET` or aggregation request isolates their data efficiently at the repository SQL layer using `WHERE user_id = :id`.
- System operations such as modifying user roles or record destruction are guarded by strict access control scopes configured securely via an injectable generic FastAPI Dependency (`RequireRole`).

### 3. Safety-First Deletion
Soft deletion using a boolean `is_deleted` column prevents catastrophic data loss metrics and acts as an audit log. Active records are globally filtered automatically without compromising original references.

### 4. Advanced Enhancements (Full Coverage)
This backend implements **all** Optional Requirements suggested in the assignment parameters:
- **Authentication:** JWT scoping via custom middlewares.
- **Pagination:** Strict standard pagination limits enforcing `offset` and `limit`.
- **Search Support:** ILIKE queries exposed natively routing through `%search%` parameters.
- **Soft Delete:** `is_deleted` handling across the entire app.
- **Rate Limiting:** Globally deployed `slowapi` rate limits capping to 100 req/minute to stop abuse.
- **Tests:** Custom Pytests guaranteeing endpoint resolutions, math precision limits, and application health logic.

---

## Local Development & Setup

This repository uses local `Docker` and a `Makefile` to orchestrate setups.
A `.env.example` file is provided. Rename it to `.env` if custom configurations are needed. (Standard defaults will connect successfully on localhost).

### 1. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Services
Ensure Docker is installed, then build and mount the database system:
```bash
make docker-up
```

### 3. Run Migrations
Run Alembic upgrades to deploy the exact database schemas onto the running container:
```bash
alembic upgrade head
```

### 4. Run the API Server
```bash
make run
```
Access the Swagger documentation via `http://localhost:8000/docs`.

### 5. Run Tests
The test suite spans schemas, service logic functions, and database assertions.
```bash
make test
```

---

## API Endpoints

Interactive Swagger docs are available at `http://localhost:8000/docs` when the server is running.

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | — | Register a new user (default role: viewer) |
| POST | `/api/v1/auth/login` | — | Login and receive a JWT token |
| GET | `/api/v1/auth/me` | Bearer | Get the current authenticated user |

### User Management (Admin only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/` | List all users (filterable by role, status) |
| GET | `/api/v1/users/{id}` | Get a user by ID |
| PATCH | `/api/v1/users/{id}/role` | Change a user's role |
| PATCH | `/api/v1/users/{id}/status` | Activate or deactivate a user |

### Financial Records
| Method | Endpoint | Roles | Description |
|--------|----------|-------|-------------|
| POST | `/api/v1/records/` | Admin | Create a financial record |
| GET | `/api/v1/records/` | All | List records (paginated, filterable, searchable) |
| GET | `/api/v1/records/{id}` | All | Get a single record by ID |
| PATCH | `/api/v1/records/{id}` | Admin | Partially update a record |
| DELETE | `/api/v1/records/{id}` | Admin | Soft-delete a record |

### Dashboard
| Method | Endpoint | Roles | Description |
|--------|----------|-------|-------------|
| GET | `/api/v1/dashboard/summary` | All | Aggregated summary (income, expenses, trends) |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check (includes database connectivity) |

---

## Project Structure

```
app/
├── config.py                  # Environment and application settings
├── database.py                # Async SQLAlchemy engine and session factory
├── main.py                    # FastAPI application factory
├── core/
│   ├── jwt.py                 # JWT token creation and decoding
│   └── security.py            # Bcrypt password hashing and verification
├── errors/
│   ├── exceptions.py          # Custom exception hierarchy
│   └── handlers.py            # Global exception handlers
├── middleware/
│   ├── auth.py                # JWT authentication dependency
│   └── rbac.py                # Role-based access control dependency
├── models/
│   ├── user.py                # User ORM model
│   └── record.py              # FinancialRecord ORM model
├── repositories/
│   ├── user_repository.py     # User data access layer
│   ├── record_repository.py   # Record data access layer
│   └── dashboard_repository.py# Dashboard aggregation queries
├── routers/
│   ├── auth.py                # Authentication endpoints
│   ├── users.py               # User management endpoints
│   ├── records.py             # Financial record endpoints
│   ├── dashboard.py           # Dashboard summary endpoint
│   └── health.py              # Health check endpoint
├── schemas/
│   ├── common.py              # Shared response envelope (ApiResponse, Meta)
│   ├── user.py                # User request/response schemas
│   ├── record.py              # Record request/response schemas
│   └── dashboard.py           # Dashboard response schemas
└── utils/
    └── money.py               # Centralized currency conversion utilities
```

## Assumptions & Tradeoffs

- **New users default to the `viewer` role.** Admin accounts must be promoted by an existing admin via `PATCH /users/{id}/role`.
- **Amounts in API requests are Decimal strings** (e.g., `5000.50`), validated to max 2 decimal places. Internally stored as integer cents to guarantee precision.
- **Soft-delete is used over hard-delete** to preserve data integrity and enable future audit/recovery features.
- **Rate limiting is global** (100 req/min per IP) rather than per-endpoint, keeping the implementation simple while still preventing abuse.
- **JWT tokens encode the user's role at issuance time.** On each request, the user is re-fetched from the database to ensure role/status changes take effect immediately.
