-- Initialize PostgreSQL with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security (RLS) on key tables
-- This will be enforced after tables are created by SQLAlchemy

-- Create indexes for vector similarity search
-- These will be created after the application creates the tables
