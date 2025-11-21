# AI Agent Platform - Multi-Agent Orchestration System

A comprehensive AI-powered business automation platform featuring intelligent agents for finance, sales, and reporting, with seamless integrations to Gmail, Calendar, CRM, and payment systems.

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI
- Clerk (Authentication)

**Backend:**
- Node.js/Express (Orchestrator Service)
- PostgreSQL (Supabase) - User data, teams, connector configs
- Snowflake - Raw data storage, analytics
- Vector DB (Pinecone/Weaviate) - Embeddings for semantic search

**Execution Layer:**
- n8n (Workflow automation)
- OpenAI GPT-4 (Agent reasoning)
- Custom Swarm Controller

**Integrations:**
- Gmail API
- Google Calendar API
- HubSpot/Zoho CRM
- Stripe/Razorpay Payments
- Twilio WhatsApp

**Infrastructure:**
- Vercel (Frontend hosting)
- Fly.io (n8n & services)
- GitHub Actions (CI/CD)
- Sentry (Monitoring)

## 📁 Project Structure

```
ai-agent-platform/
├── apps/
│   └── frontend/              # Next.js application
│       ├── src/
│       │   ├── app/          # App router pages
│       │   ├── components/   # React components
│       │   ├── lib/          # Utilities & configs
│       │   └── types/        # TypeScript types
│       └── package.json
│
├── services/
│   ├── orchestrator/         # Swarm controller service
│   │   ├── src/
│   │   │   ├── agents/      # Agent implementations
│   │   │   ├── controllers/ # API controllers
│   │   │   ├── services/    # Business logic
│   │   │   └── utils/       # Helpers
│   │   └── package.json
│   │
│   └── connectors/           # Connector service
│       ├── src/
│       │   ├── gmail/
│       │   ├── calendar/
│       │   ├── crm/
│       │   └── payments/
│       └── package.json
│
├── packages/
│   ├── database/             # Shared DB schemas & migrations
│   ├── shared-types/         # Shared TypeScript types
│   └── utils/                # Shared utilities
│
├── infra/
│   ├── terraform/            # IaC for cloud resources
│   ├── docker/               # Docker configs
│   │   └── n8n/             # n8n setup
│   └── github/               # GitHub Actions workflows
│
└── workers/
    └── n8n-workflows/        # n8n workflow definitions
        ├── invoice-reminder.json
        ├── lead-intake.json
        └── meeting-scheduler.json
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- PostgreSQL 14+
- Snowflake account (trial available)
- Docker (for n8n)
- OpenAI API key

### Installation

1. **Clone and install dependencies:**
```bash
git clone <your-repo-url>
cd my_project
npm install
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Set up databases:**
```bash
# PostgreSQL
npm run db:migrate

# Snowflake (run SQL in Snowflake console)
# See: packages/database/snowflake/schema.sql
```

4. **Start n8n (Docker):**
```bash
cd infra/docker/n8n
docker-compose up -d
```

5. **Run development servers:**
```bash
# Terminal 1 - Frontend
cd apps/frontend
npm run dev

# Terminal 2 - Orchestrator
cd services/orchestrator
npm run dev

# Terminal 3 - Connectors
cd services/connectors
npm run dev
```

6. **Access the application:**
- Frontend: http://localhost:3000
- Orchestrator API: http://localhost:4000
- n8n: http://localhost:5678

## 🤖 Agents

### Finance Agent
- Invoice parsing (PDF OCR)
- Overdue payment detection
- Payment reconciliation
- Anomaly detection
- Automated reminders via n8n

### Sales Agent
- Lead intake & scoring
- Follow-up sequence orchestration
- Meeting scheduling
- CRM synchronization
- Pipeline management

### Reporting Agent
- Daily/weekly summary generation
- SQL query execution on Snowflake
- PDF/HTML report generation
- Automated distribution

### Supervisor Agent
- Action approval workflows
- Conflict resolution
- Risk assessment
- Human-in-the-loop for sensitive actions

## 🔌 Connectors

### Email (Gmail)
- OAuth 2.0 authentication
- Read emails
- Send emails
- Webhook for new emails

### Calendar (Google Calendar)
- Event creation
- Availability checking
- Meeting scheduling

### CRM (HubSpot/Zoho)
- Lead creation
- Contact management
- Deal tracking

### Payments (Stripe/Razorpay)
- Payment processing
- Webhook handling
- Transaction reconciliation

### Messaging (WhatsApp via Twilio)
- Send messages
- Receive webhooks
- Template messages

## 🔐 Security

- All API credentials encrypted at rest (AES-256)
- HTTPS enforced for all endpoints
- RBAC for multi-tenant access
- Rate limiting on all public APIs
- SOC 2 compliant data handling
- Audit logs for all agent actions

## 📊 Monitoring & Observability

- Sentry for error tracking
- Custom dashboards (Prometheus/Grafana)
- Agent execution logs
- n8n workflow monitoring
- OpenAI API usage tracking

## 🧪 Testing

```bash
# Unit tests
npm run test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e
```

## 🚢 Deployment

### Staging
```bash
# Frontend to Vercel
vercel deploy --env preview

# Services to Fly.io
fly deploy --config services/orchestrator/fly.toml
```

### Production
```bash
# Frontend
vercel deploy --prod

# Services
fly deploy --config services/orchestrator/fly.toml --env production
```

## 📈 Development Roadmap

### Week 0 (Days 1-3): Setup & Architecture ✅
- [x] Monorepo setup
- [x] Auth (Clerk) integration
- [x] Database schemas
- [x] Initial CI/CD

### Week 1 (Days 4-10): UI & Connectors
- [ ] Login/signup flows
- [ ] Connector management UI
- [ ] Gmail/Calendar integration
- [ ] CRM connector
- [ ] Payment webhooks

### Week 2 (Days 11-17): n8n & Execution
- [ ] n8n provisioning
- [ ] Webhook handlers
- [ ] Core workflows (invoice, lead, meeting)
- [ ] Execution logs UI

### Week 3 (Days 18-24): Finance Agent
- [ ] Swarm controller
- [ ] PDF invoice parsing
- [ ] Overdue detection
- [ ] Payment reconciliation

### Week 4 (Days 25-31): Sales & Reporting Agents
- [ ] Sales agent implementation
- [ ] Lead scoring
- [ ] Reporting agent
- [ ] Supervisor agent skeleton

### Week 5 (Days 32-38): Polish & Deploy
- [ ] Billing integration
- [ ] RBAC & approvals
- [ ] E2E tests
- [ ] Monitoring setup
- [ ] Staging deployment
- [ ] Alpha pilot

### Week 6 (Days 39-45): Launch
- [ ] Feedback iteration
- [ ] Marketing site
- [ ] Sales playbook
- [ ] Security audit
- [ ] Public MVP launch

## 📝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For issues and questions:
- Email: naagesh2206@gmail.com
- Slack: 
- Docs: https://docs.yourdomain.com

---

**Built with ❤️ for autonomous business operations**
