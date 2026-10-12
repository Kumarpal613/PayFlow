# PayFlow

PayFlow is a learning project that simulates transfers between accounts. It uses
FastAPI for HTTP, Pydantic for request validation, SQLAlchemy for database
access, and PostgreSQL for persistent account balances.

> This is an educational simulation. It is not a real payment or UPI service and
> is not production-ready financial software.

## Requirements

- Python 3.11 or newer
- PostgreSQL installed and running locally
- PowerShell on Windows (commands below use PowerShell syntax)

## Install dependencies

From the project root, create a virtual environment if you do not already have
one, then install the packages from `requirements.txt`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment already exists, run only the install command.

## Configure PostgreSQL

Create a database and a dedicated local development user. Open `psql` as a
PostgreSQL administrator and run:

```sql
CREATE USER payflow WITH PASSWORD 'replace_with_a_local_password';
CREATE DATABASE payflow OWNER payflow;
```

Set the connection URL in the same PowerShell window where you will initialize
the database and run the application:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://payflow:replace_with_a_local_password@localhost:5432/payflow"
```

The application reads `DATABASE_URL` from the process environment. `.env.example`
is an example only; the project does not automatically load `.env` files. Do not
commit real database passwords.

## Create the database table

With `DATABASE_URL` set, create the account table:

```powershell
.\.venv\Scripts\python.exe -m app.db.init_db
```

The initializer creates the table if it does not already exist. It is a simple
development initializer, not a database migration tool; it does not update
existing tables when model definitions change.

## Add sample accounts

The project does not seed sample accounts automatically. With PostgreSQL's
`psql` installed and `DATABASE_URL` set, insert local development accounts:

```powershell
psql -h localhost -U payflow -d payflow -c "INSERT INTO accounts (name, balance) VALUES ('alice', 1000.00), ('bob', 500.00);"
```

Account names are unique. Run the insert only once, or PostgreSQL will reject
duplicate names.

## Run the API

Keep `DATABASE_URL` set in this PowerShell window, then start the development
server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive request
documentation is at `http://127.0.0.1:8000/docs`.

## Transfer endpoint

`POST /transfer` moves a positive amount with up to two decimal places between
two existing accounts. The request identifies accounts by name:

```json
{
  "sender": "alice",
  "receiver": "bob",
  "amount": "100.00"
}
```

Successful response (`200 OK`):

```json
{
  "message": "Transfer Successful",
  "sender_balance": "900.00",
  "receiver_balance": "600.00"
}
```

The API returns `422` for malformed requests, `400` when sender and receiver
are the same account, `404` when an account is missing, `409` when the sender
does not have enough funds, and `500` for unexpected failures. Internal
database exception details are not returned to the client.

Transfers run inside a database transaction. PostgreSQL row locks serialize
updates to the participating accounts, and the transaction rolls back if the
transfer fails.

## Project structure

```text
app/
  api/routes/          HTTP routes and status-code mapping
  controllers/         Request-to-service coordination
  db/                  SQLAlchemy engine, sessions, table initialization
  models/               SQLAlchemy database models
  repositories/         Account database queries
  schemas/              Pydantic request and response models
  services/             Transfer rules and transaction handling
tests/
  unit/                 Service tests with mocked database access
  integration/          SQLAlchemy persistence and rollback tests
  test_api.py           FastAPI endpoint tests
  conftest.py           Isolated in-memory SQLite fixtures
app/main.py              FastAPI application entry point
requirements.txt        Python dependencies
```

A transfer request flows through the route, controller, service, repository,
and database. The route handles HTTP details; the controller maps input and
results; the service enforces transfer rules; the repository loads and updates
accounts; and SQLAlchemy persists changes in a transaction.

## Run tests

Tests use an isolated in-memory SQLite database. They do not connect to the
PostgreSQL database configured by `DATABASE_URL` and do not delete development
database data.

Run all tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run one test group:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\unit
.\.venv\Scripts\python.exe -m pytest -q tests\integration
.\.venv\Scripts\python.exe -m pytest -q tests\test_api.py
```

The SQLite tests cover service rules, persistence, constraints, rollback, and
API responses. SQLite does not implement PostgreSQL's `SELECT FOR UPDATE` row
locking, so those tests do not verify PostgreSQL concurrency behavior. A
separate PostgreSQL-backed concurrency test suite is needed to validate
production-database locking semantics.
