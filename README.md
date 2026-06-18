# PrepOS

Monorepo for PrepOS - a preparation operating system built with FastAPI, PostgreSQL, Redis, and React.

## Architecture

```
prepos/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # Route handlers (v1)
│   │   ├── core/     # Config, security, database, logging
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic v2 schemas
│   │   ├── services/ # Business logic
│   │   ├── repositories/ # Data access layer
│   │   └── tests/    # Backend tests
│   ├── alembic/      # Database migrations
│   └── requirements/ # Python dependencies
├── frontend/         # React + Vite + TypeScript
│   └── src/
│       ├── api/      # API client & endpoints
│       ├── components/ # UI & layout components
│       ├── pages/    # Route pages
│       ├── store/    # Zustand state management
│       └── hooks/    # Custom React hooks
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and set up environment files:**

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. **Start infrastructure (PostgreSQL + Redis):**

```bash
docker compose up -d postgres redis
```

3. **Backend setup:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements/dev.txt
alembic upgrade head 
uvicorn app.main:app --reload
```

4. **Frontend setup:**

```bash
cd frontend
npm install
npm run dev
```

5. Open http://localhost:5173

### Docker (full stack)

```bash
docker compose up -d --build
```

### Run tests

```bash
cd backend && pytest
```

### Lint & format

```bash
# Backend
cd backend && ruff check . && ruff format .

# Frontend
cd frontend && npx tsc --noEmit && npx prettier --check "src/**/*.{ts,tsx}"
```

## API Endpoints

| Method | Path                | Description        |
| ------ | ------------------- | ------------------ |
| GET    | /api/v1/health      | Health check       |
| POST   | /api/v1/auth/register | Register user   |
| POST   | /api/v1/auth/login    | Login user      |
| POST   | /api/v1/auth/refresh  | Refresh tokens  |
| GET    | /api/v1/users/me      | Current profile  |
| PATCH  | /api/v1/users/me      | Update profile   |

## Deployment

The stack is designed for AWS deployment with:

- **ECS / Fargate** for container orchestration
- **RDS Aurora PostgreSQL** for database
- **ElastiCache Redis** for caching
- **ALB** for load balancing
- **S3 + CloudFront** for static assets
