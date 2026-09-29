"""initial schema"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    op.create_table("users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table("searches",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("plan", JSONB),
        sa.Column("status", sa.String(32)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table("rfqs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("items", JSONB),
        sa.Column("suppliers", JSONB),
        sa.Column("deadline", sa.DateTime),
        sa.Column("location", sa.String(255)),
        sa.Column("currency", sa.String(8), server_default="USD"),
        sa.Column("status", sa.String(32), server_default="draft"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table("outreaches",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("rfq_id", UUID, sa.ForeignKey("rfqs.id"), nullable=False),
        sa.Column("supplier_id", sa.String(64)),
        sa.Column("subject", sa.String(255)),
        sa.Column("message", sa.Text),
        sa.Column("status", sa.String(32), server_default="draft"),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table("quotes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("rfq_id", UUID, sa.ForeignKey("rfqs.id"), nullable=False),
        sa.Column("supplier_id", sa.String(64)),
        sa.Column("price", sa.Numeric),
        sa.Column("currency", sa.String(8)),
        sa.Column("moq", sa.Integer),
        sa.Column("lead_time", sa.String(64)),
        sa.Column("payment_terms", sa.String(255)),
        sa.Column("shipping_terms", sa.String(255)),
        sa.Column("incoterms", sa.String(16)),
        sa.Column("validity", sa.DateTime),
        sa.Column("notes", sa.Text),
        sa.Column("evidence", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table("watchlists",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("condition", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table("alerts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("data", JSONB),
        sa.Column("read", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

def downgrade():
    for t in ["alerts", "watchlists", "quotes", "outreaches", "rfqs", "searches", "users"]:
        op.drop_table(t)