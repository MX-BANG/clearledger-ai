from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from backend.config import DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    vendor = Column(String, nullable=False)

    # Split amount into income and expense
    income = Column(Float, default=0.0)
    expense = Column(Float, default=0.0)

    currency = Column(String, default="PKR")
    category = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    # Transaction type
    transaction_type = Column(String, default="expense")  # "income" or "expense"

    # Confidence scores stored as JSON
    confidence_json = Column(Text, nullable=False)

    source_file = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)

    # Duplicate detection
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(Integer, nullable=True)

    # Review flag
    needs_review = Column(Boolean, default=False)

    # Remaining balance calculation
    remaining_balance = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "vendor": self.vendor,
            "amount": self.income - self.expense,
            "income": self.income,
            "expense": self.expense,
            "currency": self.currency,
            "category": self.category,
            "notes": self.notes,
            "transaction_type": self.transaction_type,
            "confidence": json.loads(self.confidence_json),
            "source_file": self.source_file,
            "raw_text": self.raw_text,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "needs_review": self.needs_review,
            "remaining_balance": self.remaining_balance,
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

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()