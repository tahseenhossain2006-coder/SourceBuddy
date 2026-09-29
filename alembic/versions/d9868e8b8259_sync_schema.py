"""sync_schema

Revision ID: d9868e8b8259
Revises: 2f3f0fd1d3ec
Create Date: 2026-09-10 00:51:59.721346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd9868e8b8259'
down_revision: Union[str, Sequence[str], None] = '2f3f0fd1d3ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ====================================================================
    # 0. Create baseline tables that this migration modifies further down.
    #    These were previously assumed to exist (created outside Alembic).
    #    Making them part of the migration allows a clean-database bootstrap.
    # ====================================================================
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('input_type', sa.String(length=50), nullable=True),
        sa.Column('input_value', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ====================================================================
    # 1. Create new tables (dependency order: parent tables first)
    # ====================================================================
    op.create_table('suppliers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_name', sa.Text(), nullable=False),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('supplier_type', sa.String(length=100), nullable=True),
        sa.Column('product_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('moq', sa.Text(), nullable=True),
        sa.Column('price', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('lead_time', sa.Text(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('shipping_terms', sa.Text(), nullable=True),
        sa.Column('certifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_country'), 'suppliers', ['country'], unique=False)
    op.create_index(op.f('ix_suppliers_supplier_type'), 'suppliers', ['supplier_type'], unique=False)
    op.create_index(op.f('ix_suppliers_website'), 'suppliers', ['website'], unique=False)

    op.create_table('searches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('normalized_query', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('search_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_searches_created_at'), 'searches', ['created_at'], unique=False)
    op.create_index(op.f('ix_searches_status'), 'searches', ['status'], unique=False)

    op.create_table('alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_created_at'), 'alerts', ['created_at'], unique=False)
    op.create_index(op.f('ix_alerts_read'), 'alerts', ['read'], unique=False)

    op.create_table('rfqs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('suppliers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_location', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rfqs_status'), 'rfqs', ['status'], unique=False)

    op.create_table('usage_audit',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('request_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('usage_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_audit_timestamp'), 'usage_audit', ['timestamp'], unique=False)

    op.create_table('watchlists',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Text(), nullable=False),
        sa.Column('condition', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_hash', sa.Text(), nullable=True),
        sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_content_snippet', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watchlists_enabled'), 'watchlists', ['enabled'], unique=False)
    op.create_index(op.f('ix_watchlists_target_id'), 'watchlists', ['target_id'], unique=False)

    op.create_table('outreaches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('rfq_id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('provider_message_id', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rfq_id'], ['rfqs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outreaches_status'), 'outreaches', ['status'], unique=False)

    op.create_table('quotes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('rfq_id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('price', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('moq', sa.Text(), nullable=True),
        sa.Column('lead_time', sa.Text(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('shipping_terms', sa.Text(), nullable=True),
        sa.Column('incoterms', sa.String(length=20), nullable=True),
        sa.Column('validity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rfq_id'], ['rfqs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('search_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('search_id', sa.UUID(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['search_id'], ['searches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_results_url'), 'search_results', ['url'], unique=False)

    op.create_table('rankings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('search_id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('ranking_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['search_id'], ['searches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rankings_search_supplier', 'rankings', ['search_id', 'supplier_id'], unique=False)

    op.create_table('evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('search_result_id', sa.UUID(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('claim', sa.Text(), nullable=True),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('extraction_method', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['search_result_id'], ['search_results.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('contradictions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('evidence_id', sa.UUID(), nullable=True),
        sa.Column('field', sa.String(length=100), nullable=True),
        sa.Column('value_a', sa.Text(), nullable=True),
        sa.Column('value_b', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ====================================================================
    # 2. Modify existing tables
    # ====================================================================
    op.add_column('jobs', sa.Column('input_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('error', sa.Text(), nullable=True))

    op.alter_column('jobs', 'status',
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=50),
                    nullable=False)

    op.execute("UPDATE jobs SET created_at = NOW() WHERE created_at IS NULL;")
    op.execute("UPDATE jobs SET updated_at = NOW() WHERE updated_at IS NULL;")
    op.execute("UPDATE projects SET created_at = NOW() WHERE created_at IS NULL;")
    op.execute("UPDATE projects SET updated_at = NOW() WHERE updated_at IS NULL;")
    op.execute("UPDATE users SET created_at = NOW() WHERE created_at IS NULL;")
    op.execute("UPDATE users SET updated_at = NOW() WHERE updated_at IS NULL;")

    op.alter_column('jobs', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    op.alter_column('jobs', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))

    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)

    op.drop_constraint(op.f('jobs_user_id_fkey'), 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'user_id')
    op.drop_column('jobs', 'attempts')
    op.drop_column('jobs', 'progress')
    op.drop_column('jobs', 'result_data')
    op.drop_column('jobs', 'started_at')
    op.drop_column('jobs', 'completed_at')
    op.drop_column('jobs', 'error_message')
    op.drop_column('jobs', 'input_data')

    op.alter_column('projects', 'name',
                    existing_type=sa.VARCHAR(length=200),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('projects', 'description',
                    existing_type=sa.VARCHAR(length=1000),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.alter_column('projects', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    op.alter_column('projects', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'input_type')
    op.drop_column('projects', 'input_value')

    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET is_admin = false WHERE is_admin IS NULL;")
    op.alter_column('users', 'is_admin', nullable=False)

    op.alter_column('users', 'is_active',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    op.alter_column('users', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))
    op.alter_column('users', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))


def downgrade() -> None:
    """
    Downgrade schema.

    NOTE: This migration creates baseline tables (users, projects, jobs)
    that a prior migration assumed existed. Downgrade drops only the
    tables this migration adds; the baseline tables are left in place
    to preserve the invariant that they exist for future upgrades.
    """
    op.alter_column('users', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True)
    op.alter_column('users', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    op.alter_column('users', 'is_active',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.drop_column('users', 'is_admin')

    op.add_column('projects', sa.Column('input_value', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.add_column('projects', sa.Column('input_type', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('projects', sa.Column('status', sa.VARCHAR(length=50), autoincrement=False, nullable=True))

    op.alter_column('projects', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True)
    op.alter_column('projects', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    op.alter_column('projects', 'description',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(length=1000),
                    existing_nullable=True)
    op.alter_column('projects', 'name',
                    existing_type=sa.String(length=255),
                    type_=sa.VARCHAR(length=200),
                    existing_nullable=False)

    op.add_column('jobs', sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('jobs', sa.Column('error_message', sa.VARCHAR(length=1000), autoincrement=False, nullable=True))
    op.add_column('jobs', sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('jobs', sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('jobs', sa.Column('result_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('jobs', sa.Column('progress', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('jobs', sa.Column('attempts', sa.INTEGER(), autoincrement=False, nullable=True))

    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.alter_column('jobs', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True)
    op.alter_column('jobs', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))
    op.alter_column('jobs', 'status',
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=50),
                    nullable=True)
    op.drop_column('jobs', 'error')
    op.drop_column('jobs', 'result')
    op.drop_column('jobs', 'input_config')

    op.drop_table('contradictions')
    op.drop_table('evidence')
    op.drop_index(op.f('ix_search_results_url'), table_name='search_results')
    op.drop_table('search_results')
    op.drop_index('ix_rankings_search_supplier', table_name='rankings')
    op.drop_table('rankings')
    op.drop_table('quotes')
    op.drop_index(op.f('ix_outreaches_status'), table_name='outreaches')
    op.drop_table('outreaches')
    op.drop_index(op.f('ix_watchlists_target_id'), table_name='watchlists')
    op.drop_index(op.f('ix_watchlists_enabled'), table_name='watchlists')
    op.drop_table('watchlists')
    op.drop_index(op.f('ix_usage_audit_timestamp'), table_name='usage_audit')
    op.drop_table('usage_audit')
    op.drop_index(op.f('ix_rfqs_status'), table_name='rfqs')
    op.drop_table('rfqs')
    op.drop_index(op.f('ix_alerts_read'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_created_at'), table_name='alerts')
    op.drop_table('alerts')
    op.drop_index(op.f('ix_searches_status'), table_name='searches')
    op.drop_index(op.f('ix_searches_created_at'), table_name='searches')
    op.drop_table('searches')
    op.drop_index(op.f('ix_suppliers_website'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_supplier_type'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_country'), table_name='suppliers')
    op.drop_table('suppliers')
    # Note: users, projects, jobs are left in place (baseline tables).