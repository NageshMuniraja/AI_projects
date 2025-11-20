# AI Agent Platform - Setup Guide

## Prerequisites

Before you begin, ensure you have:

- Node.js 18+ installed
- PostgreSQL 14+ installed locally or access to a hosted instance (Supabase recommended)
- Snowflake account (free trial available at https://signup.snowflake.com/)
- Docker Desktop installed
- OpenAI API key (https://platform.openai.com/api-keys)
- Clerk account for authentication (https://clerk.com/)

## Step 1: Clone and Install

```powershell
cd c:\AI_Learn\my_project
npm install
```

## Step 2: Environment Variables

1. Copy the example environment file:
```powershell
copy .env.example .env
```

2. Fill in the required variables in `.env`:

### Required for MVP:
- `OPENAI_API_KEY` - Your OpenAI API key
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` - From Clerk dashboard
- `CLERK_SECRET_KEY` - From Clerk dashboard
- `DATABASE_URL` - PostgreSQL connection string
- `N8N_API_KEY` - Generate a secure random string

### Optional (for full functionality):
- Google OAuth credentials (Gmail/Calendar)
- HubSpot credentials (CRM)
- Stripe/Razorpay keys (Payments)
- Twilio credentials (WhatsApp)

## Step 3: Database Setup

### PostgreSQL (Supabase)

1. Create a new project at https://supabase.com
2. Copy the connection string to `DATABASE_URL`
3. Run migrations:

```powershell
cd packages\database
node scripts\migrate.js
```

### Snowflake

1. Log into your Snowflake account
2. Run the SQL from `packages\database\snowflake\schema.sql` in a worksheet
3. Update `.env` with your Snowflake credentials

## Step 4: Start n8n

```powershell
cd infra\docker\n8n
copy .env.example .env
# Edit .env with secure passwords
docker-compose up -d
```

Access n8n at http://localhost:5678

## Step 5: Import n8n Workflows

1. Open n8n at http://localhost:5678
2. Go to Workflows → Import
3. Import these workflows:
   - `workers\n8n-workflows\invoice-reminder.json`
   - `workers\n8n-workflows\lead-intake.json`

## Step 6: Start Development Servers

### Terminal 1 - Frontend
```powershell
cd apps\frontend
npm run dev
```

### Terminal 2 - Orchestrator Service
```powershell
cd services\orchestrator
npm run dev
```

## Step 7: Access the Application

- Frontend: http://localhost:3000
- Orchestrator API: http://localhost:4000
- n8n: http://localhost:5678

## Next Steps

### Week 1 Tasks:
1. Configure Clerk authentication flows
2. Set up Gmail connector OAuth
3. Create first test lead in the system
4. Trigger invoice reminder workflow
5. Test agent execution endpoints

### Testing the Agents

**Finance Agent:**
```powershell
curl -X POST http://localhost:4000/api/agents/finance/run `
  -H "Content-Type: application/json" `
  -d '{\"action\":\"detect_overdue\",\"data\":{\"invoices\":[]}}'
```

**Sales Agent:**
```powershell
curl -X POST http://localhost:4000/api/agents/sales/run `
  -H "Content-Type: application/json" `
  -d '{\"action\":\"score_lead\",\"data\":{\"lead\":{}}}'
```

## Troubleshooting

### Port Already in Use
```powershell
# Find and kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL format: `postgresql://user:password@host:port/database`
- Ensure IP is whitelisted in Supabase

### n8n Not Starting
```powershell
cd infra\docker\n8n
docker-compose down
docker-compose up -d --force-recreate
docker-compose logs -f
```

## Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Test locally
4. Commit: `git commit -m "Description"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request on GitHub

## Deployment

See DEPLOYMENT.md for production deployment instructions.

## Support

- Documentation: README.md
- Issues: GitHub Issues
- Team Chat: [Your Slack/Discord]
