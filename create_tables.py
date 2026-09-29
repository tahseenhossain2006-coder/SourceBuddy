# create_tables.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    input_config JSONB,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    normalized_query TEXT,
    intent VARCHAR(100),
    search_plan JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_id UUID NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    snippet TEXT,
    content TEXT,
    source VARCHAR(100),
    rank INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_id UUID REFERENCES searches(id) ON DELETE SET NULL,
    company_name TEXT NOT NULL,
    website TEXT,
    email VARCHAR(255),
    phone VARCHAR(50),
    country VARCHAR(100),
    location TEXT,
    supplier_type VARCHAR(100),
    product_info JSONB,
    moq TEXT,
    price TEXT,
    currency VARCHAR(10),
    lead_time TEXT,
    payment_terms TEXT,
    shipping_terms TEXT,
    certifications JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    search_result_id UUID REFERENCES search_results(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    claim TEXT,
    evidence_text TEXT,
    extraction_method VARCHAR(100),
    confidence FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    evidence_id UUID REFERENCES evidence(id) ON DELETE SET NULL,
    field VARCHAR(100),
    value_a TEXT,
    value_b TEXT,
    severity VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_id UUID NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    score FLOAT,
    rank INTEGER,
    ranking_factors JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rfqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    items JSONB,
    suppliers JSONB,
    deadline TIMESTAMP WITH TIME ZONE,
    delivery_location TEXT,
    currency VARCHAR(10),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    sent_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outreaches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rfq_id UUID NOT NULL REFERENCES rfqs(id) ON DELETE CASCADE,
    supplier_id UUID,
    subject TEXT,
    message TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    provider_message_id TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rfq_id UUID NOT NULL REFERENCES rfqs(id) ON DELETE CASCADE,
    supplier_id UUID,
    price TEXT,
    currency VARCHAR(10),
    moq TEXT,
    lead_time TEXT,
    payment_terms TEXT,
    shipping_terms TEXT,
    incoterms VARCHAR(20),
    validity TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    evidence JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    condition JSONB,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    provider VARCHAR(50),
    model VARCHAR(50),
    request_metadata JSONB,
    usage_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_suppliers_country ON suppliers(country);
CREATE INDEX IF NOT EXISTS ix_suppliers_supplier_type ON suppliers(supplier_type);
CREATE INDEX IF NOT EXISTS ix_suppliers_website ON suppliers(website);
CREATE INDEX IF NOT EXISTS ix_alerts_read ON alerts(read);
CREATE INDEX IF NOT EXISTS ix_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS ix_rfqs_status ON rfqs(status);
CREATE INDEX IF NOT EXISTS ix_searches_created_at ON searches(created_at);
CREATE INDEX IF NOT EXISTS ix_searches_status ON searches(status);
CREATE INDEX IF NOT EXISTS ix_watchlists_enabled ON watchlists(enabled);
CREATE INDEX IF NOT EXISTS ix_watchlists_target_id ON watchlists(target_id);
CREATE INDEX IF NOT EXISTS ix_outreaches_status ON outreaches(status);
CREATE INDEX IF NOT EXISTS ix_rankings_search_supplier ON rankings(search_id, supplier_id);
CREATE INDEX IF NOT EXISTS ix_search_results_url ON search_results(url);
CREATE INDEX IF NOT EXISTS ix_usage_audit_timestamp ON usage_audit(timestamp);
CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs(status);
"""


async def main():
    url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        await conn.execute(SCHEMA)
        print("✅ Tables created.")
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        print("Tables:")
        for r in rows:
            print(f"  - {r['tablename']}")
    finally:
        await conn.close()


asyncio.run(main())