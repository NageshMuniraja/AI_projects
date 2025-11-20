-- Snowflake Schema for AI Agent Platform
-- Raw Data Storage & Analytics

-- Use the database
USE DATABASE AI_AGENT_DATA;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw_data;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Raw Email Data
CREATE TABLE IF NOT EXISTS raw_data.emails (
  id STRING PRIMARY KEY,
  team_id STRING NOT NULL,
  connector_id STRING NOT NULL,
  gmail_message_id STRING,
  thread_id STRING,
  from_email STRING,
  from_name STRING,
  to_emails ARRAY,
  cc_emails ARRAY,
  subject STRING,
  body_text STRING,
  body_html STRING,
  attachments ARRAY,
  labels ARRAY,
  received_at TIMESTAMP_NTZ,
  ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  metadata VARIANT
);

-- Raw Calendar Events
CREATE TABLE IF NOT EXISTS raw_data.calendar_events (
  id STRING PRIMARY KEY,
  team_id STRING NOT NULL,
  connector_id STRING NOT NULL,
  event_id STRING,
  calendar_id STRING,
  title STRING,
  description STRING,
  location STRING,
  start_time TIMESTAMP_NTZ,
  end_time TIMESTAMP_NTZ,
  attendees ARRAY,
  organizer STRING,
  status STRING,
  event_type STRING,
  ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  metadata VARIANT
);

-- Raw CRM Data
CREATE TABLE IF NOT EXISTS raw_data.crm_records (
  id STRING PRIMARY KEY,
  team_id STRING NOT NULL,
  connector_id STRING NOT NULL,
  record_type STRING, -- contact, company, deal
  external_id STRING,
  crm_system STRING, -- hubspot, zoho
  data VARIANT,
  synced_at TIMESTAMP_NTZ,
  ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw Payment Transactions
CREATE TABLE IF NOT EXISTS raw_data.payment_transactions (
  id STRING PRIMARY KEY,
  team_id STRING NOT NULL,
  connector_id STRING NOT NULL,
  transaction_id STRING,
  payment_system STRING, -- stripe, razorpay
  amount NUMBER(12,2),
  currency STRING,
  status STRING,
  customer_id STRING,
  customer_email STRING,
  description STRING,
  invoice_id STRING,
  metadata VARIANT,
  created_at TIMESTAMP_NTZ,
  ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw WhatsApp Messages
CREATE TABLE IF NOT EXISTS raw_data.whatsapp_messages (
  id STRING PRIMARY KEY,
  team_id STRING NOT NULL,
  connector_id STRING NOT NULL,
  message_sid STRING,
  from_number STRING,
  to_number STRING,
  body STRING,
  media_url STRING,
  status STRING,
  direction STRING, -- inbound, outbound
  sent_at TIMESTAMP_NTZ,
  ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Agent Execution Analytics
CREATE TABLE IF NOT EXISTS analytics.agent_executions (
  id STRING PRIMARY KEY,
  team_id STRING NOT NULL,
  agent_type STRING,
  action_type STRING,
  success BOOLEAN,
  execution_time_ms NUMBER,
  confidence_score NUMBER(3,2),
  executed_at TIMESTAMP_NTZ,
  date DATE,
  hour NUMBER
);

-- Daily Metrics
CREATE TABLE IF NOT EXISTS analytics.daily_metrics (
  team_id STRING,
  date DATE,
  metric_type STRING,
  metric_value NUMBER,
  PRIMARY KEY (team_id, date, metric_type)
);

-- Lead Funnel Analytics
CREATE TABLE IF NOT EXISTS analytics.lead_funnel (
  team_id STRING,
  date DATE,
  stage STRING,
  count NUMBER,
  total_value NUMBER(12,2),
  PRIMARY KEY (team_id, date, stage)
);

-- Financial Analytics
CREATE TABLE IF NOT EXISTS analytics.financial_summary (
  team_id STRING,
  period_start DATE,
  period_end DATE,
  total_revenue NUMBER(12,2),
  total_expenses NUMBER(12,2),
  outstanding_invoices NUMBER(12,2),
  overdue_count NUMBER,
  PRIMARY KEY (team_id, period_start, period_end)
);

-- Create streams for real-time processing
CREATE STREAM IF NOT EXISTS raw_data.emails_stream ON TABLE raw_data.emails;
CREATE STREAM IF NOT EXISTS raw_data.payment_transactions_stream ON TABLE raw_data.payment_transactions;

-- Create tasks for periodic analytics updates
CREATE OR REPLACE TASK analytics.update_daily_metrics
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 1 * * * UTC'
AS
  INSERT INTO analytics.daily_metrics
  SELECT 
    team_id,
    CURRENT_DATE() - 1 as date,
    'emails_received' as metric_type,
    COUNT(*) as metric_value
  FROM raw_data.emails
  WHERE DATE(received_at) = CURRENT_DATE() - 1
  GROUP BY team_id;

-- Vector embeddings for semantic search (if using Snowflake Cortex)
CREATE TABLE IF NOT EXISTS raw_data.email_embeddings (
  id STRING PRIMARY KEY,
  email_id STRING,
  team_id STRING,
  embedding VECTOR(FLOAT, 1536), -- OpenAI ada-002 dimensions
  created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Views for common queries
CREATE OR REPLACE VIEW analytics.recent_activity AS
SELECT 
  'email' as activity_type,
  team_id,
  from_email as source,
  subject as description,
  received_at as timestamp
FROM raw_data.emails
WHERE received_at >= DATEADD(day, -7, CURRENT_TIMESTAMP())
UNION ALL
SELECT 
  'payment' as activity_type,
  team_id,
  customer_email as source,
  description,
  created_at as timestamp
FROM raw_data.payment_transactions
WHERE created_at >= DATEADD(day, -7, CURRENT_TIMESTAMP());

-- Grant permissions
GRANT USAGE ON SCHEMA raw_data TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA analytics TO ROLE PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA raw_data TO ROLE PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO ROLE PUBLIC;
GRANT SELECT ON ALL VIEWS IN SCHEMA analytics TO ROLE PUBLIC;
