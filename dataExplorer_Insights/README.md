# DataInsights AI - Enterprise Database Analytics Platform

<div align="center">

![DataInsights AI](https://img.shields.io/badge/DataInsights-AI-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Node](https://img.shields.io/badge/node-20+-green)

**Transform natural language into powerful database insights using cutting-edge AI technology**

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Documentation](#documentation)

</div>

## 🚀 Overview

DataInsights AI is a production-ready SaaS platform that revolutionizes database analytics by combining the power of Large Language Models (LLMs) with agentic AI architecture. Ask questions in plain English and get instant insights, visualizations, and actionable recommendations from your databases.

### Key Features

✨ **Natural Language Queries** - Ask questions in plain English, no SQL knowledge required

🤖 **Agentic AI Architecture** - Multi-step reasoning using LangGraph for complex analytical workflows

📊 **Intelligent Visualizations** - Automatic chart recommendations based on your data

🗄️ **Multi-Database Support** - PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Snowflake, Redshift, BigQuery, Oracle, Cassandra, and more

⚡ **Real-time Processing** - WebSocket support for streaming results

🔒 **Enterprise Security** - JWT authentication, rate limiting, and audit logging

📈 **Deep Insights** - Statistical analysis, pattern detection, and anomaly identification

🎨 **Modern UI** - Beautiful interface built with Next.js 14 and Tailwind CSS

## 🏗️ Architecture

### High-Level System Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │              Next.js 14 Frontend (TypeScript + Tailwind)               │ │
│  │                                                                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │ │
│  │  │  Chat        │  │  Database    │  │ Visualization │  │  Query    │ │ │
│  │  │  Interface   │  │  Connection  │  │   Dashboard   │  │  History  │ │ │
│  │  │              │  │  Manager     │  │               │  │           │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │ │
│  │                                                                         │ │
│  │  State Management: Zustand | Data Fetching: React Query               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
                                     │
                          REST API (JSON) │ WebSocket
                                     ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY & MIDDLEWARE LAYER                        │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        FastAPI Application                             │ │
│  │                                                                         │ │
│  │  Authentication (JWT) │ Rate Limiting │ CORS │ Logging │ Validation   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│                          AGENTIC AI PROCESSING LAYER                          │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    LangGraph Agentic Workflow                          │ │
│  │                                                                         │ │
│  │  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐             │ │
│  │  │   Step 1    │    │    Step 2    │    │    Step 3    │             │ │
│  │  │   Intent    │───▶│   Schema     │───▶│     SQL      │             │ │
│  │  │  Analysis   │    │   Fetching   │    │  Generation  │             │ │
│  │  └─────────────┘    └──────────────┘    └──────────────┘             │ │
│  │         │                                        │                     │ │
│  │         │                                        ↓                     │ │
│  │         │                              ┌──────────────┐               │ │
│  │         │                              │    Step 4    │               │ │
│  │         │                              │    Query     │               │ │
│  │         │                              │  Execution   │               │ │
│  │         │                              └──────────────┘               │ │
│  │         │                                        │                     │ │
│  │         │                                        ↓                     │ │
│  │         │                              ┌──────────────┐               │ │
│  │         └──────────────────────────────▶│    Step 5    │               │ │
│  │                                        │  Statistical │               │ │
│  │                                        │   Analysis   │               │ │
│  │                                        └──────────────┘               │ │
│  │                                               │                        │ │
│  │                                               ↓                        │ │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │ │
│  │  │   Step 6     │    │    Step 7    │    │   Step 8     │           │ │
│  │  │   Insight    │───▶│ Visualization│───▶│   Response   │           │ │
│  │  │  Generation  │    │  Recommend.  │    │  Formation   │           │ │
│  │  └──────────────┘    └──────────────┘    └──────────────┘           │ │
│  │                                                                         │ │
│  │  LLM: OpenAI GPT-4 / Anthropic Claude                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
                                     │
                      ┌──────────────┴──────────────┐
                      │                             │
                      ↓                             ↓
┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│      SERVICE LAYER               │  │      CACHING LAYER               │
│                                  │  │                                  │
│  ┌────────────────────────────┐ │  │  ┌────────────────────────────┐ │
│  │  Database Manager          │ │  │  │  Redis Cache               │ │
│  │  • Connection Pool         │ │  │  │  • Query Results           │ │
│  │  • Query Executor          │ │  │  │  • Schema Cache            │ │
│  │  • Schema Inspector        │ │  │  │  • Session Storage         │ │
│  └────────────────────────────┘ │  │  └────────────────────────────┘ │
│                                  │  │                                  │
│  ┌────────────────────────────┐ │  │  TTL: 1 hour (configurable)    │
│  │  SQL Generator             │ │  └──────────────────────────────────┘
│  │  • Natural Language → SQL  │ │
│  │  • Query Optimization      │ │
│  │  • Validation & Safety     │ │
│  └────────────────────────────┘ │
│                                  │
│  ┌────────────────────────────┐ │
│  │  Insights Analyzer         │ │
│  │  • Statistical Analysis    │ │
│  │  • Pattern Detection       │ │
│  │  • Anomaly Detection       │ │
│  │  • Correlation Analysis    │ │
│  └────────────────────────────┘ │
└──────────────────────────────────┘
                │
                ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCE LAYER                                   │
│                                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │PostgreSQL│  │  MySQL   │  │SQL Server│  │  SQLite  │  │ MongoDB  │     │
│  │  5432    │  │  3306    │  │  1433    │  │   File   │  │  27017   │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │Snowflake │  │ Redshift │  │ BigQuery │  │  Oracle  │  │ Cassandra│     │
│  │  Cloud   │  │  Cloud   │  │  Cloud   │  │  1521    │  │  9042    │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                               │
│  ┌──────────┐  ┌──────────┐                                                 │
│  │ MariaDB  │  │  IBM DB2 │                                                 │
│  │  3306    │  │  50000   │                                                 │
│  └──────────┘  └──────────┘                                                 │
│                                                                               │
│  Supports: OLTP, OLAP, Data Warehouses, Cloud Data Platforms, NoSQL         │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Application Flow Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION FLOW                                 │
└───────────────────────────────────────────────────────────────────────────────┘

    👤 User                                                                      
     │                                                                           
     │ 1. Login/Register                                                         
     ├─────────────────────────────────────────────────────────────────────────┐      
     │                                                                   │      
     ↓                                                                   ↓      
┌─────────┐                                                      ┌──────────┐  
│  Auth   │────────────────── JWT Token ──────────────────────────▶ │  Cache   │  
│  System │                                                      │  (Redis) │  
└─────────┘                                                      └──────────┘  
     │                                                                          
     │ 2. Navigate to Dashboard                                                 
     ↓                                                                          
┌──────────────────────────────────────────────────────────────────────────────┐  
│                         DASHBOARD PAGE                                    │  
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │  
│  │  Database       │  │  Chat Interface │  │  Results Panel  │         │  
│  │  Selector       │  │                 │  │                 │         │  
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │  
└──────────────────────────────────────────────────────────────────────────────┘  
     │                                                                          
     │ 3. Select/Connect Database                                               
     ↓                                                                          
┌────────────────────────────────────────────┐                                     
│  Database Connection Modal             │                                     
│  • Choose Type (PostgreSQL/MySQL...)   │                                     
│  • Enter Credentials                   │                                     
│  • Test Connection                     │                                     
└────────────────────────────────────────────┘                                     
     │                                                                          
     │ 4. Ask Natural Language Question                                         
     ↓                                                                          
┌────────────────────────────────────────────┐                                     
│  "What are the top 10 customers       │                                     
│   by total revenue this year?"        │                                     
└────────────────────────────────────────────┘                                     
     │                                                                          
     │ 5. Send to Backend API                                                   
     ↓                                                                          
┌───────────────────────────────────────────────────────────────────────────────┐  
│                    AGENTIC AI WORKFLOW (Backend)                          │  
│                                                                           │  
│  Step 1: Intent Understanding                                            │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ LLM analyzes: "This is a metrics query requesting top customers │    │  
│  │ ranked by revenue with aggregation and filtering"               │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 2: Schema Fetching                                                 │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ • Query database for table structure                            │    │  
│  │ • Identify: customers table, orders table, revenue columns      │    │  
│  │ • Understand relationships and keys                             │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 3: SQL Generation                                                  │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ SELECT c.customer_name,                                         │    │  
│  │        SUM(o.total_amount) as revenue                           │    │  
│  │ FROM customers c                                                 │    │  
│  │ JOIN orders o ON c.id = o.customer_id                           │    │  
│  │ WHERE YEAR(o.order_date) = YEAR(CURRENT_DATE)                  │    │  
│  │ GROUP BY c.customer_name                                         │    │  
│  │ ORDER BY revenue DESC                                            │    │  
│  │ LIMIT 10                                                         │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 4: Query Execution                                                 │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ • Execute on target database                                    │    │  
│  │ • Apply timeout (5 min default)                                 │    │  
│  │ • Limit rows (10,000 default)                                   │    │  
│  │ • Return: 10 rows with customer names and revenues              │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 5: Statistical Analysis                                            │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ • Calculate: mean, median, std deviation                        │    │  
│  │ • Detect patterns and trends                                    │    │  
│  │ • Identify outliers (customers with unusually high revenue)     │    │  
│  │ • Find correlations                                             │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 6: Insight Generation                                              │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ LLM generates narrative:                                        │    │  
│  │ "The top 10 customers account for 45% of total revenue.        │    │  
│  │  Customer 'Acme Corp' leads with $2.5M, which is 3x the       │    │  
│  │  average. There's a significant drop-off after the top 3."     │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 7: Visualization Recommendations                                   │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ • Bar Chart: Customer vs Revenue (Priority 1)                  │    │  
│  │ • Pie Chart: Revenue Distribution (Priority 2)                 │    │  
│  │ • Table: Detailed breakdown (Priority 3)                        │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
│         │                                                                │  
│         ↓                                                                │  
│  Step 8: Cache & Return                                                  │  
│  ┌─────────────────────────────────────────────────────────────────────┐    │  
│  │ • Store in Redis (1 hour TTL)                                   │    │  
│  │ • Log to query history                                          │    │  
│  │ • Return JSON response                                          │    │  
│  └─────────────────────────────────────────────────────────────────────┘    │  
└───────────────────────────────────────────────────────────────────────────────┘  
     │                                                                          
     │ 6. Receive Response                                                      
     ↓                                                                          
┌───────────────────────────────────────────────────────────────────────────────┐  
│                         RESULTS DISPLAY                                   │  
│                                                                           │  
│  ┌─────────────────────────────────────────────────────────────────────┐  │  
│  │ 📊 VISUALIZATIONS                                                 │  │  
│  │  [Bar Chart showing revenue by customer]                         │  │  
│  └─────────────────────────────────────────────────────────────────────┘  │  
│                                                                           │  
│  ┌─────────────────────────────────────────────────────────────────────┐  │  
│  │ 💡 INSIGHTS                                                       │  │  
│  │  • Top 10 customers = 45% of revenue                             │  │  
│  │  • Acme Corp leads with $2.5M                                    │  │  
│  │  • Significant concentration in top 3 customers (risk factor)   │  │  
│  └─────────────────────────────────────────────────────────────────────┘  │  
│                                                                           │  
│  ┌─────────────────────────────────────────────────────────────────────┐  │  
│  │ 📋 DATA TABLE                                                     │  │  
│  │  Customer Name    │  Revenue                                     │  │  
│  │  ────────────────────────────────                                 │  │  
│  │  Acme Corp        │  $2,500,000                                  │  │  
│  │  Global Inc       │  $1,800,000                                  │  │  
│  │  TechStart LLC    │  $1,200,000                                  │  │  
│  │  ...              │  ...                                         │  │  
│  └─────────────────────────────────────────────────────────────────────┘  │  
│                                                                           │  
│  ┌─────────────────────────────────────────────────────────────────────┐  │  
│  │ 🔍 SQL QUERY (for transparency)                                   │  │  
│  │  SELECT c.customer_name, SUM(o.total_amount) as revenue...      │  │  
│  └─────────────────────────────────────────────────────────────────────┘  │  
└───────────────────────────────────────────────────────────────────────────────┘  
     │                                                                          
     │ 7. User Actions                                                          
     ↓                                                                          
┌────────────────────────────────────────┐                                     
│  • Ask follow-up questions             │                                     
│  • Export results (CSV/Excel)          │                                     
│  • Save to history                     │                                     
│  • Share insights                      │                                     
│  • Switch visualizations               │                                     
└────────────────────────────────────────┘                                     
```

### Technology Stack

**Frontend:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS + shadcn/ui for styling
- React Query for data fetching
- Zustand for state management
- Recharts & Plotly for visualizations

**Backend:**
- FastAPI for high-performance API
- LangGraph for agentic AI workflows
- LangChain for LLM orchestration
- OpenAI GPT-4 or Anthropic Claude
- SQLAlchemy for database abstraction
- Redis for caching and sessions

**Databases Supported:**

*Traditional RDBMS:*
- PostgreSQL
- MySQL / MariaDB
- Microsoft SQL Server
- SQLite
- Oracle Database
- IBM DB2

*Cloud Data Warehouses:*
- Snowflake
- Amazon Redshift
- Google BigQuery
- Azure Synapse Analytics

*NoSQL & Distributed:*
- MongoDB
- Apache Cassandra
- Amazon DynamoDB
- Redis (as data source)

## 🚦 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for containerized deployment)
- OpenAI API Key or Anthropic API Key

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/datainsights-ai.git
cd datainsights-ai
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs

### Option 2: Local Development

#### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env and configure your settings
```

5. **Start Redis** (required for caching)
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

6. **Run the backend**
```bash
python main.py
```

Backend will be available at http://localhost:8000

#### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Set up environment**
```bash
cp .env.example .env.local
# Edit .env.local if needed
```

4. **Run the development server**
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

## 📖 Usage Guide

### Connecting to a Database

1. Click the **"Select a database"** button in the dashboard
2. Choose your database type:
   - **Traditional RDBMS**: PostgreSQL, MySQL, SQL Server, Oracle, DB2
   - **Cloud Warehouses**: Snowflake, Redshift, BigQuery
   - **NoSQL**: MongoDB, Cassandra, DynamoDB
3. Enter connection details:
   - Connection Name
   - Host/Account and Port (or Cloud URL)
   - Username and Password (or API credentials)
   - Database/Schema/Keyspace Name
   - Additional parameters (region, warehouse, etc. for cloud)
4. Click **"Connect"**

**Cloud Database Examples:**
- **Snowflake**: Account URL, username, password, warehouse, database, schema
- **Redshift**: Cluster endpoint, port 5439, database, user, password
- **BigQuery**: Project ID, dataset, service account JSON key

### Asking Questions

Simply type your question in natural language:

**Examples:**
- "What are the top 10 customers by revenue?"
- "Show me sales trends for the last 6 months"
- "Which products have the highest profit margin?"
- "Find customers who haven't purchased in 90 days"
- "What is the average order value by region?"

### Understanding Results

The platform provides:

1. **Query Results** - Raw data table with your results
2. **Insights** - AI-generated analysis and key findings
3. **Visualizations** - Automatic charts based on your data
4. **SQL Query** - The generated SQL for transparency

### Real-World Use Cases & Problem Solving

#### 🛒 E-commerce Analytics

**Problem:** E-commerce manager needs to understand sales performance without SQL knowledge

**Questions DataInsights AI Solves:**
```
"Show me monthly revenue growth over the past year"
→ Returns: Trend line chart, growth %, insights on peak months

"Which products are frequently bought together?"
→ Returns: Product association analysis, cross-sell opportunities

"What's the customer lifetime value by segment?"
→ Returns: Segmented CLV analysis, retention insights

"Which products have declining sales?"
→ Returns: Products with negative trends, inventory recommendations

"What's the average cart abandonment rate by device?"
→ Returns: Device comparison, actionable UX insights
```

**Business Impact:**
- ⏱️ Reduce analysis time from hours to seconds
- 📈 Identify revenue opportunities faster
- 🎯 Make data-driven inventory decisions
- 💰 Optimize pricing strategies based on trends

#### 💼 Business Intelligence & Executive Reporting

**Problem:** Executives need quick insights without waiting for data team

**Questions DataInsights AI Solves:**
```
"Compare sales performance across all regions this quarter"
→ Returns: Regional comparison charts, growth rates, top/bottom performers

"What are the top performing sales representatives?"
→ Returns: Leaderboard, performance metrics, benchmarks

"Show me conversion rates by traffic source"
→ Returns: Funnel analysis, ROI by channel, optimization opportunities

"What's our customer acquisition cost trend?"
→ Returns: CAC over time, efficiency metrics, forecasts

"Identify our most profitable customer segments"
→ Returns: Segment profitability, characteristics, growth potential
```

**Business Impact:**
- 🚀 Enable self-service analytics for executives
- 📊 Real-time decision making
- 💡 Uncover hidden patterns and opportunities
- 🎯 Focus resources on high-value activities

#### 📊 Data Quality & Operations

**Problem:** Data team needs to monitor and maintain data quality

**Questions DataInsights AI Solves:**
```
"Find duplicate customer records"
→ Returns: Duplicate analysis, merge recommendations, data quality score

"Show me records with missing critical fields"
→ Returns: Data completeness report, field-by-field analysis

"Identify anomalies in daily transaction counts"
→ Returns: Outlier detection, potential issues flagged, alerts

"Which tables have the most NULL values?"
→ Returns: Data quality dashboard, prioritized cleanup list

"Show me data freshness by source"
→ Returns: Last update times, stale data identification
```

**Business Impact:**
- ✅ Improve data quality proactively
- 🔍 Detect issues before they impact business
- ⚡ Automate data quality monitoring
- 📋 Generate compliance reports instantly

#### 💰 Financial Analysis

**Problem:** Finance team needs to analyze financial metrics across departments

**Questions DataInsights AI Solves:**
```
"What's our burn rate for the last 6 months?"
→ Returns: Burn rate trend, runway calculation, forecast

"Compare budget vs actual spending by department"
→ Returns: Variance analysis, overspend alerts, recommendations

"Show me profit margin trends by product line"
→ Returns: Margin analysis, profitability insights, price optimization

"Which customers have outstanding invoices over 60 days?"
→ Returns: AR aging report, collection priorities, cash flow impact

"What's our customer churn rate and impact on MRR?"
→ Returns: Churn analysis, revenue impact, retention insights
```

**Business Impact:**
- 💵 Better cash flow management
- 📉 Reduce costs through insights
- 🎯 Optimize pricing and margins
- 📊 Faster month-end reporting

#### 👥 HR & People Analytics

**Problem:** HR needs workforce insights for strategic planning

**Questions DataInsights AI Solves:**
```
"What's our employee turnover rate by department?"
→ Returns: Turnover analysis, risk departments, retention insights

"Show me average time-to-hire by role"
→ Returns: Hiring efficiency metrics, bottleneck identification

"Which teams have the highest performance ratings?"
→ Returns: Performance benchmarks, best practices identification

"Compare compensation across similar roles"
→ Returns: Pay equity analysis, market competitiveness

"What's the correlation between training and performance?"
→ Returns: Training ROI, development recommendations
```

**Business Impact:**
- 👔 Improve talent retention
- 📈 Optimize hiring processes
- 💰 Ensure pay equity
- 🎓 Better training investments

#### 🏥 Healthcare & Patient Analytics

**Problem:** Healthcare providers need patient outcome insights

**Questions DataInsights AI Solves:**
```
"What's our average patient wait time by department?"
→ Returns: Wait time analysis, bottlenecks, improvement opportunities

"Show me readmission rates by diagnosis"
→ Returns: Quality metrics, risk factors, intervention opportunities

"Which treatments have the best outcomes?"
→ Returns: Treatment effectiveness, evidence-based recommendations

"Identify patients overdue for follow-up appointments"
→ Returns: Patient list, outreach priorities, compliance tracking

"What's our bed utilization rate over time?"
→ Returns: Capacity planning insights, optimization opportunities
```

**Business Impact:**
- 🏥 Improve patient outcomes
- ⏱️ Reduce wait times
- 💰 Optimize resource allocation
- 📋 Ensure compliance

#### 🏭 Manufacturing & Supply Chain

**Problem:** Operations needs real-time production and supply chain insights

**Questions DataInsights AI Solves:**
```
"What's our inventory turnover rate by product category?"
→ Returns: Turnover analysis, slow-moving inventory, optimization tips

"Show me production efficiency trends"
→ Returns: OEE metrics, bottleneck identification, improvement areas

"Which suppliers have the most quality issues?"
→ Returns: Supplier scorecard, quality metrics, recommendations

"What's our order fulfillment rate by region?"
→ Returns: Fulfillment performance, delivery insights, optimization

"Predict which items will stock out in the next 30 days"
→ Returns: Stock predictions, reorder recommendations, risk mitigation
```

**Business Impact:**
- 📦 Optimize inventory levels
- 🏭 Improve production efficiency
- 🚚 Better supply chain management
- 💰 Reduce carrying costs

#### ☁️ Cloud Data Warehouse Analytics

**Problem:** Data teams need to query massive datasets in Snowflake, Redshift, or BigQuery

**Questions DataInsights AI Solves:**
```
"Analyze 5 years of customer behavior data for trends"
→ Returns: Long-term trend analysis, seasonal patterns, predictive insights

"What's the cost breakdown of our cloud data warehouse usage?"
→ Returns: Warehouse credit consumption, cost optimization recommendations

"Show me query performance metrics across all schemas"
→ Returns: Slow queries, optimization opportunities, resource utilization

"Compare data freshness across all pipelines"
→ Returns: Pipeline health, latency metrics, stale data alerts

"Which tables have grown the most in the last quarter?"
→ Returns: Storage growth analysis, partitioning recommendations
```

**Business Impact:**
- 💰 Reduce cloud costs through optimization
- ⚡ Improve query performance
- 📊 Scale analytics seamlessly
- 🔍 Better data governance

### Key Problems DataInsights AI Solves

1. **⏱️ Time Savings**
   - Traditional: Hours to write SQL, wait for data team, create reports
   - DataInsights AI: Seconds to get answers with insights

2. **🎯 Democratize Data**
   - No SQL knowledge required
   - Self-service analytics for everyone
   - Reduces bottlenecks on data teams

3. **💡 Deeper Insights**
   - AI-powered pattern detection
   - Automatic anomaly identification
   - Proactive recommendations

4. **🔒 Governance & Security**
   - Audit trail of all queries
   - Role-based access control
   - Query validation and safety

5. **📊 Better Decisions**
   - Real-time data access
   - Visual insights
   - Contextual recommendations

6. **💰 Cost Reduction**
   - Reduce data team workload
   - Faster time to insights
   - Better resource allocation

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# LLM Configuration
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Database Connections (optional defaults)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=mydb

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

### Frontend Configuration

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Features in Detail

### Agentic AI Workflow

The platform uses LangGraph to implement a sophisticated multi-step reasoning process:

1. **Intent Understanding** - Classifies query type (metrics, insights, comparison, etc.)
2. **Schema Analysis** - Examines database structure to understand available data
3. **SQL Generation** - Creates optimized SQL queries using LLM
4. **Query Execution** - Safely executes queries with timeout and row limits
5. **Result Analysis** - Performs statistical analysis and pattern detection
6. **Insight Generation** - Creates natural language insights
7. **Visualization Recommendation** - Suggests appropriate charts

### Supported Query Types

- **Metrics** - Counts, sums, averages, and other aggregations
- **Trends** - Time-series analysis and temporal patterns
- **Comparisons** - Side-by-side analysis of different segments
- **Distribution** - Understanding how data is spread
- **Anomaly Detection** - Identifying unusual patterns
- **Correlations** - Finding relationships between variables

### Security Features

- JWT-based authentication
- Rate limiting (100 requests per minute by default)
- SQL injection prevention
- Query timeouts to prevent resource exhaustion
- Audit logging of all queries
- Dangerous operation blocking (DROP, DELETE, etc.)

## 📊 API Documentation

### Interactive API Docs

Visit http://localhost:8000/api/docs when the backend is running for interactive Swagger documentation.

### Key Endpoints

#### Authentication
```
POST /api/v1/auth/register - Register new user
POST /api/v1/auth/login - Login user
POST /api/v1/auth/refresh - Refresh access token
GET  /api/v1/auth/me - Get current user
```

#### Database Operations
```
POST /api/v1/database/test-connection - Test database connection
POST /api/v1/database/schema - Get database schema
POST /api/v1/database/sample-data - Get sample data from table
GET  /api/v1/database/supported-databases - List supported databases
```

#### Natural Language Queries
```
POST /api/v1/chat/query - Process natural language query
POST /api/v1/chat/streaming - Stream query results (SSE)
```

#### Insights
```
GET /api/v1/insights/templates - Get insight templates
GET /api/v1/insights/sample-queries - Get sample queries
```

#### Query History
```
GET    /api/v1/queries/history - Get query history
GET    /api/v1/queries/history/{id} - Get query details
DELETE /api/v1/queries/history/{id} - Delete query
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**
   - Set `DEBUG=False` in production
   - Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
   - Configure proper `ALLOWED_ORIGINS`

2. **Database Security**
   - Use read-only database users when possible
   - Enable SSL/TLS for database connections
   - Implement proper access controls

3. **Scaling**
   - Use Redis Cluster for caching at scale
   - Deploy behind a load balancer
   - Use CDN for static assets
   - Consider horizontal scaling with Kubernetes

4. **Monitoring**
   - Set up application monitoring (DataDog, New Relic, etc.)
   - Enable error tracking (Sentry)
   - Monitor API rate limits and usage
   - Track LLM API costs

### Deployment Options

#### Docker Compose
```bash
docker-compose up -d
```

#### Kubernetes
See `k8s/` directory for Kubernetes manifests (coming soon)

#### Cloud Platforms
- **AWS**: ECS, Fargate, or EKS
- **Google Cloud**: Cloud Run or GKE
- **Azure**: Container Instances or AKS
- **Vercel**: Frontend only (Next.js)
- **Railway/Render**: Full stack deployment

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

- 📧 Email: support@datainsights-ai.com
- 💬 Discord: [Join our community](https://discord.gg/datainsights)
- 📚 Documentation: [docs.datainsights-ai.com](https://docs.datainsights-ai.com)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/datainsights-ai/issues)

## 🌟 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [LangChain](https://langchain.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [OpenAI](https://openai.com/)
- [shadcn/ui](https://ui.shadcn.com/)

---

<div align="center">
Made with ❤️ by the DataInsights AI Team
</div>
