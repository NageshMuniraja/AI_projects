# Development Setup Guide

## Prerequisites

- Python 3.11 or higher
- Node.js 20 or higher
- Docker and Docker Compose
- Git
- OpenAI API Key or Anthropic API Key

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd datainsights
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENAI_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local if needed
```

### 4. Start Redis (Required for backend)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Run the Applications

**Backend:**
```bash
cd backend
python main.py
```
Backend runs on: http://localhost:8000

**Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs on: http://localhost:3000

## Using Docker Compose

The easiest way to run everything:

```bash
# Create .env file in root
cp .env.example .env
# Add your OPENAI_API_KEY

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Testing Database Connections

The project includes demo databases in docker-compose:

- **PostgreSQL**: localhost:5432 (user: postgres, password: password, db: demo_db)
- **MongoDB**: localhost:27017 (user: admin, password: password)

## Project Structure

```
datainsights/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # Agentic AI agents
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic
│   ├── main.py             # Application entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   ├── lib/          # Utilities
│   │   └── store/        # State management
│   ├── package.json       # Node dependencies
│   └── next.config.js     # Next.js configuration
├── docker-compose.yml     # Docker Compose configuration
└── README.md             # Project documentation
```

## Development Workflow

1. **Make changes** to backend or frontend code
2. **Test locally** using the development servers
3. **Commit changes** with descriptive messages
4. **Test with Docker** before deploying

## Environment Variables

### Backend (.env)

```env
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
DEBUG=True
HOST=0.0.0.0
PORT=8000
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.11+)
- Ensure Redis is running: `docker ps | grep redis`
- Check logs for errors: `docker-compose logs backend`

### Frontend won't start
- Check Node version: `node --version` (should be 20+)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check logs for errors: `docker-compose logs frontend`

### Can't connect to database
- Ensure database is running
- Check connection parameters
- Test connection using database client first

### LLM not responding
- Verify API key is correct
- Check API quota/billing
- Look for errors in backend logs

## Useful Commands

```bash
# Backend
cd backend
python main.py                    # Run server
pytest                           # Run tests
black .                          # Format code
flake8 .                         # Lint code

# Frontend
cd frontend
npm run dev                      # Development server
npm run build                    # Production build
npm run lint                     # Lint code
npm run type-check               # TypeScript check

# Docker
docker-compose up -d             # Start all services
docker-compose down              # Stop all services
docker-compose logs -f backend   # View backend logs
docker-compose ps                # List running services
docker-compose restart backend   # Restart backend
```

## Next Steps

1. Connect to your database
2. Try sample queries
3. Customize the UI
4. Add more database connectors
5. Deploy to production
