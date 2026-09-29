# sourceai/storage/models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, JSON, Integer, Float,
    Text, Enum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Utility function for UTC timestamps
def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    searches = relationship("Search", back_populates="user")
    rfqs = relationship("RFQ", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="projects")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    input_config = Column(JSONB)
    result = Column(JSONB)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="jobs")

class Search(Base):
    __tablename__ = "searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    normalized_query = Column(Text)
    intent = Column(String(100))
    search_plan = Column(JSONB)
    status = Column(String(50), nullable=False, index=True)
    extra = Column(JSONB, name='metadata')        # renamed to avoid reserved word
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="searches")
    results = relationship("SearchResult", back_populates="search", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="search", cascade="all, delete-orphan")

class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False, index=True)
    title = Column(Text)
    snippet = Column(Text)
    content = Column(Text)
    source = Column(String(100))
    rank = Column(Integer)
    extra = Column(JSONB, name='metadata')        # renamed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    search = relationship("Search", back_populates="results")
    evidence = relationship("Evidence", back_populates="search_result", cascade="all, delete-orphan")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(Text, nullable=False)
    website = Column(Text, index=True)
    email = Column(String(255))
    phone = Column(String(50))
    country = Column(String(100), index=True)
    location = Column(Text)
    supplier_type = Column(String(100), index=True)
    product_info = Column(JSONB)
    moq = Column(Text)
    price = Column(Text)
    currency = Column(String(10))
    lead_time = Column(Text)
    payment_terms = Column(Text)
    shipping_terms = Column(Text)
    certifications = Column(JSONB)
    extra = Column(JSONB, name='metadata')        # renamed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    evidence = relationship("Evidence", back_populates="supplier", cascade="all, delete-orphan")
    contradictions = relationship("Contradiction", back_populates="supplier", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="supplier", cascade="all, delete-orphan")
    outreaches = relationship("Outreach", back_populates="supplier")
    quotes = relationship("Quote", back_populates="supplier")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    search_result_id = Column(UUID(as_uuid=True), ForeignKey("search_results.id", ondelete="SET NULL"))
    url = Column(Text, nullable=False)
    claim = Column(Text)
    evidence_text = Column(Text)
    extraction_method = Column(String(100))
    confidence = Column(Float, CheckConstraint("confidence >= 0 AND confidence <= 1"))
    extra = Column(JSONB, name='metadata')        # renamed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supplier = relationship("Supplier", back_populates="evidence")
    search_result = relationship("SearchResult", back_populates="evidence")

class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="SET NULL"))
    field = Column(String(100))
    value_a = Column(Text)
    value_b = Column(Text)
    severity = Column(String(50))
    status = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    supplier = relationship("Supplier", back_populates="contradictions")

class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float)
    rank = Column(Integer)
    ranking_factors = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    search = relationship("Search", back_populates="rankings")
    supplier = relationship("Supplier", back_populates="rankings")

    __table_args__ = (
        Index("ix_rankings_search_supplier", "search_id", "supplier_id"),
    )

class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    items = Column(JSONB)
    suppliers = Column(JSONB)  # list of supplier IDs or details
    deadline = Column(DateTime(timezone=True))
    delivery_location = Column(Text)
    currency = Column(String(10))
    status = Column(String(50), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="rfqs")
    outreaches = relationship("Outreach", back_populates="rfq", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="rfq", cascade="all, delete-orphan")

class Outreach(Base):
    __tablename__ = "outreaches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    subject = Column(Text)
    message = Column(Text)
    status = Column(String(50), nullable=False, index=True)
    provider_message_id = Column(Text)
    sent_at = Column(DateTime(timezone=True))
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    rfq = relationship("RFQ", back_populates="outreaches")
    supplier = relationship("Supplier", back_populates="outreaches")

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    price = Column(Text)
    currency = Column(String(10))
    moq = Column(Text)
    lead_time = Column(Text)
    payment_terms = Column(Text)
    shipping_terms = Column(Text)
    incoterms = Column(String(20))
    validity = Column(DateTime(timezone=True))
    notes = Column(Text)
    evidence = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    rfq = relationship("RFQ", back_populates="quotes")
    supplier = relationship("Supplier", back_populates="quotes")

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    condition = Column(JSONB)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    last_checked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="watchlists")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB)
    read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="alerts")

class UsageAudit(Base):
    __tablename__ = "usage_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    provider = Column(String(50))
    model = Column(String(50))
    request_metadata = Column(JSONB)
    usage_data = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)