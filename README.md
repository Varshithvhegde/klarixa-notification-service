# Notipy - Advanced Async Notification Engine

**Notipy** is a production-ready, fully asynchronous notification microservice built with **FastAPI**, **SQLAlchemy (Async)**, and **Jinja2**. It is designed to orchestrate high-throughput delivery across Email, SMS, and Push channels with built-in reliability and intelligence.

---

## Key Features

### 1. High-Performance Core
*   **Fully Asynchronous**: Uses `asyncpg` (PostgreSQL) and `aiosqlite` (SQLite) for non-blocking database operations.
*   **Priority Queue**: A native `asyncio.PriorityQueue` based worker system that processes jobs based on priority (`CRITICAL`, `HIGH`, `NORMAL`, `LOW`).
*   **Atomic Batch API**: Send personalized notifications to hundreds of users in a single request.

### 2. Multi-Channel Reliability
*   **Strategy Pattern**: Clean provider abstraction allowing easy swaps between Twilio, SendGrid, or Mock providers.
*   **Retries & Error Tracking**: Exponential backoff for transient failures with detailed error logging per job.
*   **Idempotency Locks**: Prevent double-firing notifications for duplicate requests using unique keys.

### 3. Intelligence & Control
*   **Template Library**: DB-backed Jinja2 templates with real-time variable injection.
*   **User Preferences**: Global opt-out registry per user-channel pair.
*   **Sliding Window Rate Limiting**: Per-user quota enforcement (100 notifications/hour).

### 4. Enterprise Observability
*   **Real-time Analytics**: Aggregate throughput stats (sent/failed/pending) grouped by channel and time period.
*   **Webhooks**: Register HTTP callback endpoints for `SENT` or `FAILED` notification events.
*   **Paginated Telemetry**: Full historical audit trail for every user ID.

---

## Architecture & Assumptions

### User Identity
This service uses a **Lazy User Model**. A `user_id` is simply a unique string representing an identity. You do **not** need to register a user before sending a notification.
*   **Assumption**: If no preference is found in the database, the user is considered **Opted-In** to all channels by default.

### Workers
The engine starts **2 concurrent async workers** within the same process under the FastAPI lifespan. It automatically handles table creation (`metadata.create_all`) on startup.

### Other Assumptions
*   Authentication/authorization is handled by an upstream API gateway (not implemented here).
*   User data exists in a separate service; this service only stores `user_id`.
*   External email/SMS/push providers are mocked with a 20% simulated failure rate for testing.
*   The `delivered` status is set immediately after successful provider delivery (mock providers don't have a separate delivery confirmation step).

---

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Framework | FastAPI | Native async support, automatic OpenAPI docs, Pydantic validation |
| ORM | SQLAlchemy 2.0 (async) | Industry-standard ORM with async engine support |
| Database | PostgreSQL (asyncpg) | Production-grade RDBMS; SQLite (aiosqlite) for testing |
| Queue | asyncio.PriorityQueue | Zero-dependency priority queue for single-process deployment |
| Templates | Jinja2 | Industry-standard Python templating engine |
| Testing | pytest + httpx | Async test support with in-memory test client |

---

## Getting Started

### 1. Local Setup
```bash
cd notipy_AI_Backend-Assignment

# Setup Virtual Environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configure Database
Update the `.env` file with your PostgreSQL credentials:
```env
# DATABASE_URL=sqlite+aiosqlite:///./test.db # For SQLite
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notipy_db
```

### 3. Run the Engine
```bash
uvicorn app.main:app --reload --port 8000
```

API docs are available at `http://127.0.0.1:8000/docs` (Swagger UI) or `/openapi.json` (raw spec).

---

## Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t notipy-engine .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/db \
  notipy-engine
```

### Docker Compose (with PostgreSQL)
```bash
docker-compose up
```
This starts both the application and a PostgreSQL database.

---

## Testing

### Core Test Suite (Pytest)
Run the full test suite:
```bash
python -m pytest tests/ -v
```

### Live Diagnostics CLI
Run the interactive diagnostic tool:
```bash
python test_api_live.py
```

---

## API Reference

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| POST | `/notifications/` | Send a notification to a user via one or more channels |
| POST | `/notifications/batch` | Send notifications to multiple users in one request |
| GET | `/notifications/{id}` | Get notification status by ID |

### User Notifications & Preferences

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/{userId}/notifications` | Get notification history for a user (paginated) |
| POST | `/users/{userId}/preferences` | Set a single channel preference |
| GET | `/users/{userId}/preferences` | Get all channel preferences for a user |
| POST | `/users/{userId}/preferences-bulk` | Set all channel preferences at once |

### Templates

| Method | Endpoint | Description |
|---|---|---|
| POST | `/templates/` | Create a new template |
| GET | `/templates/` | List all templates |
| GET | `/templates/{id}` | Get a template by ID |
| DELETE | `/templates/{id}` | Delete a template |

### Webhooks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhooks/` | Register a webhook |
| GET | `/webhooks/` | List all webhooks |
| DELETE | `/webhooks/{id}` | Delete a webhook |
| PATCH | `/webhooks/{id}/toggle` | Pause/resume a webhook |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/stats` | Get system-wide statistics (optional `start`/`end` query params) |

### Health Check

| Method | Endpoint | Description |
|---|---|---|
| GET | `/ping` | Health check |

### Example: Send Notification
```bash
curl -X POST "http://127.0.0.1:8000/notifications/" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "cust_123",
       "channels": ["email", "sms"],
       "message_body": "Hello {{name}}!",
       "template_vars": {"name": "Varshith"},
       "priority": "critical"
     }'
```

### Example: Batch Dispatch
```bash
curl -X POST "http://127.0.0.1:8000/notifications/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "notifications": [
         {"user_id": "u1", "channels": ["email"], "message_body": "User 1 msg"},
         {"user_id": "u2", "channels": ["sms"], "message_body": "User 2 msg"}
       ]
     }'
```

### Example: Analytics
```bash
curl "http://127.0.0.1:8000/analytics/stats?start=2024-01-01T00:00:00"
```
