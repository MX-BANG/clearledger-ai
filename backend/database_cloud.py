"""
Cloud Database Configuration
PostgreSQL for production deployment (Supabase)
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL not set, fall back to SQLite (for local development)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./database/bookkeeping.db"
    print("⚠️ Using SQLite (local development mode)")
else:
    print("✅ Using PostgreSQL (production mode - Supabase)")
    # Supabase provides postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Add SSL requirement for Supabase
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL = f"{DATABASE_URL}?sslmode=require"

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL/Supabase settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,          # Verify connections before using
        pool_recycle=300,            # Recycle connections every 5 minutes
        pool_size=5,                 # Smaller pool for free tier
        max_overflow=10,             # Max connections beyond pool_size
        echo=False,                  # Set to True for SQL debugging
        connect_args={
            "connect_timeout": 10,   # Connection timeout
            "options": "-c timezone=utc"  # Set timezone
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    vendor = Column(String, nullable=False)
    income = Column(Float, default=0.0)
    expense = Column(Float, default=0.0)
    transaction_type = Column(String, default="expense")
    currency = Column(String, default="PKR")
    category = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    confidence_json = Column(Text, nullable=False)
    source_file = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(Integer, nullable=True)
    needs_review = Column(Boolean, default=False)
    remaining_balance = Column(Float, default=0.0)  # Your custom field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "vendor": self.vendor,
            "income": self.income,
            "expense": self.expense,
            "transaction_type": self.transaction_type,
            "currency": self.currency,
            "category": self.category,
            "notes": self.notes,
            "confidence": json.loads(self.confidence_json),
            "source_file": self.source_file,
            "raw_text": self.raw_text,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "needs_review": self.needs_review,
            "remaining_balance": self.remaining_balance,  # Your custom field
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Balance(Base):
    __tablename__ = "balance"
    
    id = Column(Integer, primary_key=True, index=True)
    opening_balance = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    total_income = Column(Float, default=0.0)
    total_expense = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "opening_balance": self.opening_balance,
            "current_balance": self.current_balance,
            "total_income": self.total_income,
            "total_expense": self.total_expense,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()