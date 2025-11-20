# Deployment Guide - AI Agent Platform

## Production Deployment Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificates obtained
- [ ] DNS records configured
- [ ] Monitoring tools set up
- [ ] Backup strategy in place

## Vercel Deployment (Frontend)

### 1. Install Vercel CLI
```powershell
npm i -g vercel
```

### 2. Login to Vercel
```powershell
vercel login
```

### 3. Deploy Frontend
```powershell
cd apps\frontend
vercel --prod
```

### 4. Environment Variables in Vercel
Add these in the Vercel dashboard under Project Settings → Environment Variables:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_APP_URL=https://your-app-domain.com
```

### 5. Custom Domain
- Go to Vercel dashboard → Domains
- Add your custom domain
- Update DNS records as instructed

## Fly.io Deployment (Backend Services)

### 1. Install Fly CLI
```powershell
irm https://fly.io/install.ps1 | iex
```

### 2. Login to Fly
```powershell
flyctl auth login
```

### 3. Deploy Orchestrator Service
```powershell
cd services\orchestrator

# Create app
flyctl apps create ai-agent-orchestrator

# Set secrets
flyctl secrets set `
  OPENAI_API_KEY=your_key `
  DATABASE_URL=your_postgres_url `
  N8N_BASE_URL=your_n8n_url `
  N8N_API_KEY=your_n8n_key

# Deploy
flyctl deploy
```

### 4. Scale Resources (if needed)
```powershell
flyctl scale vm shared-cpu-1x --memory 512
```

## n8n Deployment

### Option 1: Fly.io
```powershell
cd infra\docker\n8n

# Create app
flyctl apps create ai-agent-n8n

# Create volume for persistence
flyctl volumes create n8n_data --size 1

# Set secrets
flyctl secrets set `
  N8N_BASIC_AUTH_USER=admin `
  N8N_BASIC_AUTH_PASSWORD=secure_password `
  N8N_ENCRYPTION_KEY=your_encryption_key

# Deploy
flyctl deploy
```

### Option 2: DigitalOcean Droplet
1. Create Ubuntu 22.04 droplet
2. SSH into droplet
3. Install Docker:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```
4. Copy docker-compose.yml and deploy:
```bash
docker-compose up -d
```

## Database Setup

### PostgreSQL (Supabase)
1. Create project at https://supabase.com
2. Enable database replication
3. Run migrations:
```powershell
$env:DATABASE_URL="your_production_url"
cd packages\database
node scripts\migrate.js
```

### Snowflake
1. Log into Snowflake console
2. Create production database
3. Run schema from `packages/database/snowflake/schema.sql`
4. Set up scheduled tasks for analytics

## Monitoring Setup

### 1. Sentry
```powershell
# Install Sentry CLI
npm install -g @sentry/cli

# Create .sentryclirc
sentry-cli login

# Upload source maps (frontend)
cd apps\frontend
sentry-cli releases new production-v1.0.0
sentry-cli releases files production-v1.0.0 upload-sourcemaps .next
sentry-cli releases finalize production-v1.0.0
```

### 2. Uptime Monitoring
- Set up Uptime Robot for health checks
- Monitor endpoints:
  - Frontend: https://your-domain.com
  - API: https://api.your-domain.com/health
  - n8n: https://n8n.your-domain.com

### 3. Log Aggregation
Consider using:
- Datadog
- Logtail
- Better Stack

## Security Hardening

### 1. Environment Variables
Never commit:
- API keys
- Database credentials
- Encryption keys

### 2. SSL/TLS
- Use Cloudflare for SSL (free)
- Enable HTTPS-only redirects
- Set HSTS headers

### 3. Rate Limiting
Add rate limiting to API:
```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

app.use('/api/', limiter);
```

### 4. CORS Configuration
```typescript
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
}));
```

## Backup Strategy

### Database Backups
```sql
-- PostgreSQL (via pg_dump)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

-- Automate with cron
0 2 * * * /usr/bin/pg_dump $DATABASE_URL > /backups/db_$(date +\%Y\%m\%d).sql
```

### Snowflake Backups
- Enable Time Travel (up to 90 days for Enterprise)
- Set up scheduled COPY INTO for archival

## Post-Deployment

### 1. Smoke Tests
```powershell
# Test API health
curl https://api.your-domain.com/health

# Test agent execution
curl -X POST https://api.your-domain.com/api/agents/finance/run `
  -H "Content-Type: application/json" `
  -d '{"action":"detect_overdue","data":{"invoices":[]}}'
```

### 2. Monitor Logs
```powershell
# Fly.io logs
flyctl logs

# Vercel logs
vercel logs
```

### 3. Performance Monitoring
- Set up dashboards in Vercel Analytics
- Monitor API response times
- Track agent execution success rates

## Rollback Procedure

### Frontend (Vercel)
```powershell
# List deployments
vercel list

# Rollback to specific deployment
vercel rollback <deployment-url>
```

### Backend (Fly.io)
```powershell
# List releases
flyctl releases

# Rollback to previous version
flyctl releases rollback
```

## Cost Optimization

### Estimated Monthly Costs (Starter):
- Vercel (Hobby): $0
- Fly.io (2 apps): ~$10-20
- Supabase (Free tier): $0
- Snowflake (On-demand): ~$20-50
- OpenAI API: Variable
- **Total: ~$30-100/month**

### Scaling Up:
- Vercel Pro: $20/month
- Fly.io (scaled): $50-100/month
- Supabase Pro: $25/month
- **Total: ~$100-200/month**

## Support & Troubleshooting

### Common Issues

**Issue**: Frontend can't connect to API
- Check CORS settings
- Verify API_BASE_URL environment variable
- Ensure API is deployed and healthy

**Issue**: Agent executions failing
- Check OpenAI API key validity
- Verify n8n is accessible
- Check database connection

**Issue**: High costs
- Implement caching for API responses
- Optimize database queries
- Set rate limits on expensive operations

## Maintenance Schedule

### Daily
- Review error logs in Sentry
- Check API response times
- Monitor agent success rates

### Weekly
- Review database performance
- Check backup integrity
- Update dependencies (security patches)

### Monthly
- Review and optimize costs
- Analyze usage patterns
- Update documentation

## Emergency Contacts

- DevOps Lead: [contact]
- Database Admin: [contact]
- Security Team: [contact]

---

**Last Updated**: November 20, 2025
