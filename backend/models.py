from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

# Request/Response Models

class ConfidenceScore(BaseModel):
    vendor: float = Field(..., ge=0.0, le=1.0)
    amount: float = Field(..., ge=0.0, le=1.0)
    date: float = Field(..., ge=0.0, le=1.0)
    category: float = Field(..., ge=0.0, le=1.0)

class TransactionEntry(BaseModel):
    id: Optional[int] = None
    date: str
    vendor: str
    income: float = 0.0
    expense: float = 0.0
    transaction_type: str = "expense"
    currency: str = "PKR"
    category: str
    notes: Optional[str] = None
    confidence: ConfidenceScore
    source_file: str
    raw_text: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[int] = None
    needs_review: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProcessingResult(BaseModel):
    success: bool
    entry: Optional[TransactionEntry] = None
    errors: List[str] = []
    warnings: List[str] = []

class BatchProcessingResult(BaseModel):
    total_files: int
    successful: int
    failed: int
    entries: List[TransactionEntry]
    errors: List[Dict[str, str]]

class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(csv|xlsx|json)$")
    entry_ids: Optional[List[int]] = None  # If None, export all

class DashboardStats(BaseModel):
    total_entries: int
    clean_entries: int
    flagged_entries: int
    duplicates: int
    total_amount: float
    category_breakdown: Dict[str, int]
    confidence_distribution: Dict[str, int]