# AI Agent Platform - Architecture & Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │          Next.js Frontend (Vercel)                            │   │
│  │  - Dashboard UI                                               │   │
│  │  - Connector Management                                       │   │
│  │  - Agent Configuration                                        │   │
│  │  - Authentication (Clerk)                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │      Express.js Orchestrator (Fly.io)                         │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │   │
│  │  │  Agents    │  │ Connectors │  │ Workflows  │             │   │
│  │  │   Routes   │  │   Routes   │  │   Routes   │             │   │
│  │  └────────────┘  └────────────┘  └────────────┘             │   │
│  │         │              │               │                      │   │
│  │         ▼              ▼               ▼                      │   │
│  │  ┌──────────────────────────────────────────┐                │   │
│  │  │     Middleware & Error Handling          │                │   │
│  │  └──────────────────────────────────────────┘                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                │                  │                  │
                │                  │                  │
    ┌───────────┘                  │                  └──────────┐
    │                              │                             │
    ▼                              ▼                             ▼
┌─────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   AI LAYER  │         │  WORKFLOW LAYER  │         │  CONNECTOR LAYER │
│             │         │                  │         │                  │
│  ┌───────┐  │         │  ┌────────────┐  │         │  ┌────────────┐  │
│  │Finance│  │         │  │    n8n     │  │         │  │   Gmail    │  │
│  │ Agent │  │         │  │  Workflow  │  │         │  │    API     │  │
│  └───────┘  │         │  │   Engine   │  │         │  └────────────┘  │
│  ┌───────┐  │         │  │            │  │         │  ┌────────────┐  │
│  │ Sales │  │         │  │ - Invoice  │  │         │  │  Calendar  │  │
│  │ Agent │  │         │  │   Remind   │  │         │  │    API     │  │
│  └───────┘  │         │  │ - Lead     │  │         │  └────────────┘  │
│  ┌───────┐  │         │  │   Intake   │  │         │  ┌────────────┐  │
│  │Report │  │         │  │ - Meeting  │  │         │  │  HubSpot   │  │
│  │ Agent │  │         │  │   Schedule │  │         │  │    CRM     │  │
│  └───────┘  │         │  │ - Payment  │  │         │  └────────────┘  │
│      │      │         │  │   Recon    │  │         │  ┌────────────┐  │
│      ▼      │         │  └────────────┘  │         │  │   Stripe   │  │
│  ┌───────┐  │         │        │         │         │  │  Payments  │  │
│  │OpenAI │  │         │        │         │         │  └────────────┘  │
│  │GPT-4  │  │         └────────┼─────────┘         │  ┌────────────┐  │
│  │Turbo  │  │                  │                   │  │  Razorpay  │  │
│  └───────┘  │                  │                   │  └────────────┘  │
└─────────────┘                  │                   │  ┌────────────┐  │
                                 │                   │  │  WhatsApp  │  │
                                 │                   │  │  (Twilio)  │  │
                                 │                   │  └────────────┘  │
                                 │                   └──────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                    │
│  ┌──────────────────────────┐    ┌──────────────────────────┐       │
│  │   PostgreSQL (Supabase)  │    │    Snowflake Warehouse   │       │
│  │                          │    │                          │       │
│  │  - Users & Teams         │    │  - Raw Data Tables       │       │
│  │  - Connectors            │    │  - Analytics Views       │       │
│  │  - Invoices              │    │  - Payment Transactions  │       │
│  │  - Leads                 │    │  - Lead Analytics        │       │
│  │  - Reports               │    │  - Financial Reports     │       │
│  │  - Agent Actions         │    │                          │       │
│  │  - Workflow Executions   │    │                          │       │
│  └──────────────────────────┘    └──────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     MONITORING & LOGGING                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Sentry  │  │ Winston  │  │  Uptime  │  │  GitHub  │            │
│  │  Errors  │  │   Logs   │  │  Robot   │  │ Actions  │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Flow Diagrams

### 1. User Authentication Flow

```
┌──────┐         ┌──────────┐         ┌──────────┐         ┌────────────┐
│User  │──Login──▶│ Next.js  │──Auth───▶│  Clerk   │──Token──▶│PostgreSQL │
└──────┘         │ Frontend │         │  Service │         │ (Supabase)│
                 └──────────┘         └──────────┘         └────────────┘
                      │
                      │ Store Token
                      ▼
                 ┌──────────┐
                 │LocalStore│
                 └──────────┘
```

### 2. Finance Agent Flow - Invoice Processing

```
┌────────┐      ┌────────────┐      ┌─────────────┐      ┌──────────┐
│ User   │      │ Frontend   │      │ Orchestrator│      │ Finance  │
│ Upload │─────▶│ API Client │─────▶│   Service   │─────▶│  Agent   │
└────────┘      └────────────┘      └─────────────┘      └──────────┘
                                                                │
                                                                ▼
                                                          ┌──────────┐
                                                          │ OpenAI   │
                                                          │ GPT-4    │
                                                          └──────────┘
                                                                │
                    ┌───────────────────────────────────────────┘
                    │ Parse Invoice
                    ▼
┌────────────┐◀────────────┐      ┌───────────┐      ┌──────────┐
│ PostgreSQL │             │      │    n8n    │      │  Gmail   │
│  Invoice   │     Save    │      │ Reminder  │─────▶│  Send    │
│   Record   │◀────────────┘      │ Workflow  │      │  Email   │
└────────────┘                    └───────────┘      └──────────┘
       │                                 ▲
       │                                 │
       │ If Overdue                      │
       └─────────────────────────────────┘
```

### 3. Sales Agent Flow - Lead Intake

```
┌────────┐      ┌────────────┐      ┌─────────────┐      ┌──────────┐
│ Lead   │      │  Frontend  │      │ Orchestrator│      │  Sales   │
│ Form   │─────▶│ Submission │─────▶│   Service   │─────▶│  Agent   │
└────────┘      └────────────┘      └─────────────┘      └──────────┘
                                                                │
                                                                ▼
                                                          ┌──────────┐
                                                          │ OpenAI   │
                                                          │ Score    │
                                                          │ Lead     │
                                                          └──────────┘
                                                                │
                    ┌───────────────────────────────────────────┘
                    │ Calculate Priority
                    ▼
                ┌─────────┐
                │Priority?│
                └────┬────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
    │  HIGH   │ │ MEDIUM │ │  LOW   │
    └────┬────┘ └───┬────┘ └───┬────┘
         │          │          │
         ▼          ▼          ▼
    ┌─────────┐ ┌────────┐ ┌─────────┐
    │n8n      │ │n8n     │ │n8n      │
    │Meeting  │ │Email   │ │Newsletter│
    │Schedule │ │Sequence│ │ Drip    │
    └────┬────┘ └───┬────┘ └────┬────┘
         │          │           │
         └──────────┼───────────┘
                    ▼
              ┌──────────┐      ┌──────────┐
              │ HubSpot  │◀────▶│PostgreSQL│
              │   CRM    │      │  Leads   │
              └──────────┘      └──────────┘
```

### 4. Workflow Execution Flow - Payment Reconciliation

```
┌──────────┐      ┌────────────┐      ┌──────────┐
│ Stripe   │      │  Webhook   │      │   n8n    │
│ Payment  │─────▶│  Trigger   │─────▶│ Payment  │
│ Event    │      │            │      │ Workflow │
└──────────┘      └────────────┘      └──────────┘
                                            │
                                            ▼
                                      ┌───────────┐
                                      │ Parse     │
                                      │ Payment   │
                                      │ Data      │
                                      └─────┬─────┘
                                            │
                                            ▼
                                      ┌───────────┐
                                      │ Search    │
                                      │ Invoice   │
                                      │ in DB     │
                                      └─────┬─────┘
                                            │
                                       ┌────┴────┐
                                       │ Match?  │
                                       └────┬────┘
                                            │
                              ┌─────────────┼─────────────┐
                              │                           │
                         ┌────▼────┐                 ┌───▼────┐
                         │  YES    │                 │   NO   │
                         └────┬────┘                 └───┬────┘
                              │                          │
                              ▼                          ▼
                      ┌──────────────┐          ┌──────────────┐
                      │ Mark Invoice │          │ Flag for     │
                      │ as Paid      │          │ Manual Review│
                      └──────┬───────┘          └──────┬───────┘
                             │                         │
                             ▼                         ▼
                      ┌──────────────┐          ┌──────────────┐
                      │ Log to       │          │ Notify       │
                      │ Snowflake    │          │ Finance Team │
                      └──────────────┘          └──────────────┘
```

### 5. Report Generation Flow

```
┌────────┐      ┌────────────┐      ┌─────────────┐      ┌──────────┐
│ User   │      │  Frontend  │      │ Orchestrator│      │ Reporting│
│Request │─────▶│   Dashboard│─────▶│   Service   │─────▶│  Agent   │
└────────┘      └────────────┘      └─────────────┘      └──────────┘
                                                                │
                                                                ▼
                                                          ┌──────────┐
                                                          │Query     │
                                                          │Snowflake │
                                                          └──────────┘
                                                                │
                                                                ▼
                                                          ┌──────────┐
                                                          │ OpenAI   │
                                                          │ Analyze  │
                                                          │ & Format │
                                                          └──────────┘
                                                                │
                                                                ▼
                                                          ┌──────────┐
                                                          │ Generate │
                                                          │ PDF/CSV  │
                                                          └──────────┘
                                                                │
                    ┌───────────────────────────────────────────┘
                    │
                    ▼
┌────────────┐◀────────────┐
│ PostgreSQL │             │
│  Reports   │     Save    │
│   Table    │◀────────────┘
└────────────┘
       │
       └─────────▶ Return Download Link
```

### 6. Data Flow - Connector Integration

```
┌──────────┐      ┌──────────────┐      ┌─────────────┐
│  User    │      │   Frontend   │      │Orchestrator │
│Configure │─────▶│   Add        │─────▶│  Connector  │
│Connector │      │   Connector  │      │   Route     │
└──────────┘      └──────────────┘      └──────┬──────┘
                                               │
                                               ▼
                                         ┌──────────┐
                                         │ OAuth    │
                                         │ Flow     │
                                         └──────────┘
                                               │
                        ┌──────────────────────┼──────────────────┐
                        │                      │                  │
                   ┌────▼────┐           ┌────▼────┐       ┌─────▼─────┐
                   │  Gmail  │           │Calendar │       │  HubSpot  │
                   │   API   │           │   API   │       │   API     │
                   └────┬────┘           └────┬────┘       └─────┬─────┘
                        │                     │                  │
                        └─────────────────────┼──────────────────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │ Encrypt &    │
                                      │ Store Tokens │
                                      └──────┬───────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │ PostgreSQL   │
                                      │ Connectors   │
                                      │ Table        │
                                      └──────────────┘
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, React, TypeScript | User interface |
| **Auth** | Clerk | Authentication & user management |
| **API** | Express.js, TypeScript | Backend orchestration |
| **AI** | OpenAI GPT-4 Turbo | Agent intelligence |
| **Workflow** | n8n | Automation workflows |
| **Database** | PostgreSQL (Supabase) | Transactional data |
| **Analytics** | Snowflake | Data warehouse |
| **Connectors** | Gmail, Calendar, HubSpot, Stripe | External integrations |
| **Monitoring** | Sentry, Winston | Error tracking & logging |
| **Deploy** | Vercel, Fly.io, Docker | Hosting & containers |
| **CI/CD** | GitHub Actions | Automated deployment |

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
│                                                             │
│  1. Frontend (Clerk Authentication)                        │
│     └─ Session tokens, JWT validation                     │
│                                                             │
│  2. API Gateway (Express Middleware)                       │
│     └─ Rate limiting, CORS, Helmet                        │
│                                                             │
│  3. Database (Row-Level Security)                          │
│     └─ Supabase RLS policies                              │
│                                                             │
│  4. Secrets (Environment Variables)                        │
│     └─ API keys encrypted at rest                         │
│                                                             │
│  5. Network (HTTPS/TLS)                                    │
│     └─ All traffic encrypted                              │
│                                                             │
│  6. Monitoring (Sentry)                                    │
│     └─ Security event tracking                            │
└─────────────────────────────────────────────────────────────┘
```

## Scalability Architecture

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │ API     │       │ API     │      │ API     │
    │Instance1│       │Instance2│      │Instance3│
    └────┬────┘       └────┬────┘      └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼───────┐
                    │   Database   │
                    │  (Replicated)│
                    └──────────────┘
```

---

**Last Updated**: November 20, 2025
