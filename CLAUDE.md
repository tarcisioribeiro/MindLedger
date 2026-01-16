# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PersonalHub is a full-stack financial management system with Django REST Framework backend and React + TypeScript frontend. The system manages bank accounts, credit cards, expenses, revenues, loans, and includes additional modules for security (password management), library (book tracking), and AI assistance.

## Architecture

### Monorepo Structure
```
PersonalHub/
├── api/              # Django backend (port 8002)
├── frontend/         # React frontend (port 3000)
├── docker-compose.yml
└── .env              # Root environment variables
```

### Backend Apps (Django)
- **Core Financial**: accounts, credit_cards, expenses, revenues, loans, transfers, dashboard
- **System**: authentication, members, app (core config)
- **Extended**: security (passwords), library (books), ai_assistant (experimental)

### AI Assistant Module

**Overview**:
- RAG (Retrieval Augmented Generation) service for semantic search across all modules
- Uses sentence-transformers for embeddings via dedicated microservice
- Uses Groq API for text generation (`llama-3.3-70b-versatile`)

**How it works**:
1. User submits a natural language question
2. System extracts content from Finance, Security, and Library modules
3. Generates embeddings via HTTP call to embeddings service (`all-MiniLM-L6-v2`)
4. Ranks results by cosine similarity using pgvector
5. Sends top-k results to Groq for answer generation

**Configuration**:
- Requires `GROQ_API_KEY` in .env for text generation
- `EMBEDDING_SERVICE_URL`: URL of embeddings service (default: http://embeddings:8080)
- Embeddings service runs in separate container (faster builds, reusable)

**Cost**:
- Embeddings: FREE (runs locally via embeddings-service container)
- Groq LLM: FREE tier with generous limits (6,000 requests/minute)

**Technical Details**:
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- 5x faster than larger models
- Supports multilingual text (including Portuguese)
- Uses ~80MB RAM in embeddings container
- No external API calls for embeddings = better privacy and zero cost

### Embeddings Service (Microservice)

**Overview**:
- Dedicated container for embedding generation using sentence-transformers
- Runs as independent service, reusable by other projects
- Model pre-downloaded during build for instant startup

**Architecture Benefits**:
- Faster API container builds (no model download)
- Independent scaling of embedding workloads
- Shareable infrastructure across projects
- Model cached in persistent Docker volume

**Endpoints**:
- `POST /embeddings`: Generate embeddings for list of texts
- `GET /health`: Health check (returns model loaded status)
- `GET /info`: Model information and service limits
- `GET /docs`: OpenAPI/Swagger documentation

**Configuration**:
- `EMBEDDING_PORT`: Host port (default: 8080)
- Model: `all-MiniLM-L6-v2` (384 dimensions, L2 normalized)
- Max batch size: 128 texts per request
- Memory limit: 512MB

### Key Backend Architecture Patterns

**Authentication Flow**:
- JWT tokens stored in HttpOnly cookies (access_token, refresh_token)
- Custom middleware `authentication/middleware.py:JWTCookieMiddleware` extracts tokens from cookies and adds to Authorization header
- Frontend never handles tokens directly - browser sends cookies automatically
- User data and permissions stored in separate non-HttpOnly cookies for client-side access

**Field Encryption**:
- `app/encryption.py:FieldEncryption` uses Fernet symmetric encryption
- Sensitive data (card numbers, CVVs, passwords) encrypted before database storage
- ENCRYPTION_KEY in .env must be 44-char base64 Fernet key
- CRITICAL: Never change ENCRYPTION_KEY after encrypting data (unrecoverable)

**API Versioning**: All endpoints under `/api/v1/`

**Custom Management Commands**:
- `update_balances`: Recalculate account balances
- `setup_permissions`: Configure user groups and permissions
- `process_existing_transfers`: Process transfer records

### Frontend Architecture

**State Management**:
- Zustand for global state (`stores/auth-store.ts`)
- React Hook Form + Zod for form validation
- Local state with React hooks for component-specific data

**API Client Pattern**:
- Singleton `api-client.ts` wraps axios with interceptors
- Automatic token refresh on 401 responses
- Service layer pattern: each feature has dedicated service file (e.g., `accounts-service.ts`)
- Custom error classes: AuthenticationError, ValidationError, NotFoundError, PermissionError

**Authentication**:
- HttpOnly cookies managed by backend
- Frontend checks `hasValidToken()` with 5-second cache
- Auto-refresh on 401 except for auth endpoints

## Development Commands

### Initial Setup

```bash
# 1. Create environment file
cp .env.example .env
# Edit .env and generate keys:
# - SECRET_KEY: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# - ENCRYPTION_KEY: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Start with Docker (recommended)
docker-compose up -d

# 3. Run migrations
docker-compose exec api python manage.py migrate

# 4. Create superuser (optional - entrypoint.sh creates one from .env)
docker-compose exec api python manage.py createsuperuser
```

### Daily Development

**Docker workflow**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f           # all services
docker-compose logs -f api       # backend only
docker-compose logs -f frontend  # frontend only

# Execute backend commands
docker-compose exec api python manage.py <command>
docker-compose exec api bash     # shell access

# Rebuild after dependency changes
docker-compose up -d --build

# Stop
docker-compose down
```

**Local development** (without Docker):
```bash
# Backend
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8002

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Database Operations

```bash
# Migrations
docker-compose exec api python manage.py makemigrations
docker-compose exec api python manage.py migrate
docker-compose exec api python manage.py showmigrations

# Backup
docker-compose exec db pg_dump -U $DB_USER personalhub_db > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
docker-compose exec -T db psql -U $DB_USER personalhub_db < backups/your_backup.sql

# Access PostgreSQL shell
docker-compose exec db psql -U $DB_USER -d personalhub_db
```

### Testing

```bash
# Backend tests
docker-compose exec api python manage.py test           # all tests
docker-compose exec api python manage.py test accounts  # specific app
docker-compose exec api pytest                          # with pytest
docker-compose exec api pytest --cov                    # with coverage

# Frontend tests
cd frontend
npm run test         # unit tests
npm run lint         # linting
npm run build        # production build (checks TypeScript)
```

### Code Quality

```bash
# Backend
cd api
black .              # format code
isort .              # sort imports
flake8 .             # lint

# Frontend
cd frontend
npm run lint         # ESLint
npm run build        # TypeScript type check
```

## Important Patterns and Conventions

### Backend

**Model Pattern**: Each app follows standard Django structure:
- `models.py`: Database models
- `serializers.py`: DRF serializers for validation/serialization
- `views.py`: ViewSets for API endpoints
- `urls.py`: URL routing
- `permissions.py`: Custom permission classes (if needed)

**Encrypted Fields**: When adding encrypted fields:
```python
from app.encryption import FieldEncryption

# In save()
self.encrypted_field = FieldEncryption.encrypt_data(plain_value)

# In property/method
return FieldEncryption.decrypt_data(self.encrypted_field)
```

**URL Pattern**: Use `/api/v1/<resource>/` for all endpoints

### Frontend

**Service Pattern**: Each service exports functions using apiClient:
```typescript
import { apiClient } from './api-client';

export const resourceService = {
  getAll: () => apiClient.get<Resource[]>('/api/v1/resources/'),
  create: (data: CreateData) => apiClient.post('/api/v1/resources/', data),
  // ...
};
```

**Component Organization**:
- `components/ui/`: Reusable UI components (Radix-based)
- `components/<feature>/`: Feature-specific components
- `components/layout/`: Layout components
- `pages/`: Page components (routes)

**Import Aliases**:
- `@/`: Points to `frontend/src/`
- Example: `import { Button } from '@/components/ui/button'`

## Environment Variables

### Critical Variables (must be set)

**Backend (.env in root)**:
- `SECRET_KEY`: Django secret (50+ chars random)
- `ENCRYPTION_KEY`: Fernet key (44 chars base64) - NEVER change after encrypting data
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`: PostgreSQL credentials
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`: Auto-created superuser
- `GROQ_API_KEY`: Groq API key for AI Assistant text generation (get at https://console.groq.com/keys)

**Frontend (build-time)**:
- `VITE_API_BASE_URL`: Backend URL (default: http://localhost:8002)

### Common Settings
- `DEBUG=True`: Development mode (MUST be False in production)
- `DB_HOST=db`: Use 'db' for Docker, 'localhost' for local
- `DB_PORT=39102`: External port (internal is 5432)
- `LOG_FORMAT=json`: Structured logging format
- `EMBEDDING_SERVICE_URL`: URL of embeddings service (default: http://embeddings:8080)
- `EMBEDDING_PORT`: Host port for embeddings service (default: 8080)

## Health and Debugging

**Health Check Endpoints**:
- `/health/`: Database connectivity check
- `/ready/`: Readiness probe
- `/live/`: Liveness probe

**Common Issues**:

1. **Database connection fails**:
   - Wait for healthcheck: `docker-compose logs db`
   - Check credentials in .env
   - Verify port 5435 not in use

2. **Encryption errors**:
   - Verify ENCRYPTION_KEY is set
   - Check key is valid base64 Fernet format
   - If data already encrypted, CANNOT change key

3. **CORS errors**:
   - Verify `CORS_ALLOWED_ORIGINS` in settings
   - Ensure frontend uses `withCredentials: true` (already in api-client.ts)
   - Check cookies are sent (httpOnly cookies require same-site or proper CORS)

4. **Authentication loops**:
   - Clear browser cookies
   - Check tokens in Application tab (DevTools)
   - Verify middleware is properly configured
   - Check api-client.ts doesn't retry auth endpoints

5. **Migration conflicts**:
   - `python manage.py migrate --fake-initial`
   - Or manually resolve in migrations folder

6. **AI Assistant errors**:
   - Verify `GROQ_API_KEY` is set in .env
   - Check API key is valid (not placeholder value)
   - Groq errors: Verify free tier limits at https://console.groq.com
   - Embedding errors: Check if embeddings container is healthy (`docker-compose logs embeddings`)

7. **Embeddings service errors**:
   - Check container status: `docker-compose ps embeddings`
   - View logs: `docker-compose logs -f embeddings`
   - Test health endpoint: `curl http://localhost:8080/health`
   - If model download failed, rebuild: `docker-compose build --no-cache embeddings`

## Accessing the Application

- **Frontend**: http://localhost:39101
- **Backend API**: http://localhost:39100
- **Django Admin**: http://localhost:39100/admin
- **Embeddings Service**: http://localhost:8080 (API docs at /docs)
- **Database**: localhost:39102 (PostgreSQL)

## Security Notes

- Sensitive data encrypted at rest (Fernet)
- JWT in HttpOnly cookies (XSS protection)
- CORS properly configured
- Passwords hashed with Django's default (bcrypt-like)
- Never commit .env file
- Rotate ENCRYPTION_KEY requires data re-encryption
- Production: Set DEBUG=False, use HTTPS, configure ALLOWED_HOSTS
