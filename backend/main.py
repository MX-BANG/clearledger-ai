"""
FastAPI Backend - Main Application
Provides REST API for the AI Bookkeeping Engine
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path
import json
# Use cloud database for production, fallback to local for development
import os
if os.getenv("DATABASE_URL"):
    from backend.database_cloud import init_db, get_db, Transaction, Balance
    print("✅ Using PostgreSQL (Production)")
else:
    from backend.database import init_db, get_db, Transaction, Balance
    print("⚠️ Using SQLite (Local Development)")
from backend.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from backend.models import TransactionEntry, BatchProcessingResult, ExportRequest, DashboardStats
from backend.services.ocr_service import OCRService
from backend.services.ai_structuring import AIStructuringService
from backend.services.confidence_scorer import ConfidenceScorer
from backend.services.duplicate_detector import DuplicateDetector
from backend.services.categorizer import Categorizer
from backend.services.exporter import Exporter
from backend.services.risk_detector import RiskDetector

# Initialize FastAPI app
app = FastAPI(
    title="AI Bookkeeping Cleanup Engine",
    description="Intelligent data extraction and cleanup for bookkeeping",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Initialize services
ocr_service = OCRService()
ai_service = AIStructuringService()

# Balance helper functions
def update_balance(db: Session, transaction: Transaction = None):
    """Update balance after adding/deleting transaction"""
    balance = db.query(Balance).first()
    
    if not balance:
        # Create initial balance
        balance = Balance(opening_balance=0.0, current_balance=0.0)
        db.add(balance)
    
    # Recalculate totals
    all_trans = db.query(Transaction).all()
    total_income = sum(t.income for t in all_trans)
    total_expense = sum(t.expense for t in all_trans)
    
    balance.total_income = total_income
    balance.total_expense = total_expense
    balance.current_balance = balance.opening_balance + total_income - total_expense
    
    db.commit()

def recalculate_balance(db: Session):
    """Recalculate balance from scratch"""
    balance = db.query(Balance).first()

    if not balance:
        balance = Balance(opening_balance=0.0)
        db.add(balance)

    all_trans = db.query(Transaction).all()
    total_income = sum(t.income for t in all_trans)
    total_expense = sum(t.expense for t in all_trans)

    balance.total_income = total_income
    balance.total_expense = total_expense
    balance.current_balance = balance.opening_balance + total_income - total_expense

    db.commit()
    return balance

def recalculate_remaining_balances(db: Session):
    """Recalculate remaining balance for all transactions based on starting balance"""
    balance = db.query(Balance).first()
    opening_balance = balance.opening_balance if balance else 0.0

    # Get all transactions ordered by date and id
    transactions = db.query(Transaction).order_by(Transaction.date, Transaction.id).all()

    current_balance = opening_balance

    for transaction in transactions:
        # Calculate balance after this transaction
        current_balance += transaction.income - transaction.expense
        # Set remaining balance after this transaction
        transaction.remaining_balance = current_balance

    db.commit()

    # Update the balance table's current_balance
    if balance:
        balance.current_balance = current_balance
        db.commit()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 AI Bookkeeping Engine Starting...")
    print(f"📁 Upload directory: {UPLOAD_DIR}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "AI Bookkeeping Cleanup Engine API",
        "version": "1.0.0"
    }

@app.post("/upload", response_model=BatchProcessingResult)
async def upload_files(
    files: List[UploadFile] = File(...),
    starting_balance: float = 0.0,
    db: Session = Depends(get_db)
):
    """
    Upload and process multiple files
    Returns batch processing results
    Timeout: 300 seconds per file
    """
    # Set starting balance
    balance = db.query(Balance).first()
    if not balance:
        balance = Balance()
        db.add(balance)
    balance.opening_balance = starting_balance
    db.commit()

    results = []
    errors = []

    for file in files:
        try:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                errors.append({
                    "filename": file.filename,
                    "error": f"Unsupported file type: {file_ext}"
                })
                continue

            # Save uploaded file
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process file
            entry = await process_single_file(file_path, db)
            results.append(entry)

        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    # Recalculate remaining balances after all transactions are processed
    recalculate_remaining_balances(db)

    return BatchProcessingResult(
        total_files=len(files),
        successful=len(results),
        failed=len(errors),
        entries=results,
        errors=errors
    )

async def process_single_file(file_path: Path, db: Session) -> TransactionEntry:
    """Process a single file through the entire pipeline"""
    
    # MVP 1: Extract text
    ocr_result = ocr_service.extract_text(file_path)
    if not ocr_result["success"]:
        raise Exception(ocr_result["error"])
    
    # Check if CSV/Excel with dataframe
    if "dataframe" in ocr_result:
        # For CSV/Excel, process first row only (for MVP)
        df = ocr_result["dataframe"]
        if len(df) > 0:
            # Convert first row to text
            first_row = df.iloc[0].to_dict()
            ocr_result["raw_text"] = str(first_row)
    
    # MVP 2: Structure data with AI
    structured_data = ai_service.structure_text(
        ocr_result["raw_text"],
        file_path.name
    )
    
    # MVP 3: Analyze confidence
    analysis = ConfidenceScorer.analyze_entry(structured_data)
    structured_data["needs_review"] = analysis["needs_review"]
    
    # MVP 4: Check for duplicates
    existing_entries = db.query(Transaction).all()
    existing_dicts = [e.to_dict() for e in existing_entries]
    duplicates = DuplicateDetector.find_duplicates(structured_data, existing_dicts)
    
    if duplicates:
        structured_data["is_duplicate"] = True
        structured_data["duplicate_of"] = duplicates[0]["entry_id"]
    
    # Save to database
    transaction = Transaction(
        date=structured_data["date"],
        vendor=structured_data["vendor"],
        income=structured_data.get("income", 0.0),
        expense=structured_data.get("expense", 0.0),
        transaction_type=structured_data.get("transaction_type", "expense"),
        currency=structured_data["currency"],
        category=structured_data["category"],
        notes=structured_data.get("notes", ""),
        confidence_json=json.dumps(structured_data["confidence"]),
        source_file=structured_data["source_file"],
        raw_text=structured_data["raw_text"],
        is_duplicate=structured_data.get("is_duplicate", False),
        duplicate_of=structured_data.get("duplicate_of"),
        needs_review=structured_data["needs_review"]
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Update balance
    update_balance(db, transaction)
    
    # Convert to response model
    return TransactionEntry(**transaction.to_dict())

@app.post("/transactions/manual")
async def create_manual_transaction(
    date: str,
    description: str,
    amount: float,
    transaction_type: str,  # "income" or "expense"
    category: str = "Other",
    db: Session = Depends(get_db)
):
    """Manually add a transaction"""
    
    # Determine income/expense
    income = amount if transaction_type == "income" else 0.0
    expense = amount if transaction_type == "expense" else 0.0
    
    transaction = Transaction(
        date=date,
        vendor="Manual Entry",
        income=income,
        expense=expense,
        transaction_type=transaction_type,
        currency="PKR",
        category=category,
        notes=description,
        confidence_json=json.dumps({
            "vendor": 1.0,
            "amount": 1.0,
            "date": 1.0,
            "category": 1.0,
            "transaction_type": 1.0
        }),
        source_file="Manual Entry",
        raw_text=description,
        needs_review=False
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Check for duplicates
    existing_entries = db.query(Transaction).filter(Transaction.id != transaction.id).all()
    existing_dicts = [e.to_dict() for e in existing_entries]
    duplicates = DuplicateDetector.find_duplicates(transaction.to_dict(), existing_dicts)
    
    if duplicates:
        transaction.is_duplicate = True
        transaction.duplicate_of = duplicates[0]["entry_id"]
        db.commit()
    
    # Update balance
    update_balance(db, transaction)

    # Recalculate remaining balances
    recalculate_remaining_balances(db)

    return {"message": "Transaction created", "transaction": transaction.to_dict()}

@app.get("/transactions", response_model=List[TransactionEntry])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    needs_review: bool = None,
    db: Session = Depends(get_db)
):
    """Get all transactions with optional filtering"""
    query = db.query(Transaction)
    
    if needs_review is not None:
        query = query.filter(Transaction.needs_review == needs_review)
    
    transactions = query.offset(skip).limit(limit).all()
    return [TransactionEntry(**t.to_dict()) for t in transactions]

@app.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    updated_data: dict,
    db: Session = Depends(get_db)
):
    """Update a transaction (MVP 6: Human-in-the-loop)"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update fields
    for key, value in updated_data.items():
        if hasattr(transaction, key) and key != 'id':
            setattr(transaction, key, value)
    
    # Handle income/expense split if amount or type changed
    if 'amount' in updated_data or 'transaction_type' in updated_data:
        amount = updated_data.get('amount', transaction.income + transaction.expense)
        trans_type = updated_data.get('transaction_type', transaction.transaction_type)
        
        if trans_type == 'income':
            transaction.income = amount
            transaction.expense = 0.0
        else:
            transaction.income = 0.0
            transaction.expense = amount
    
    db.commit()
    db.refresh(transaction)

    # Update balance
    update_balance(db)

    # Recalculate remaining balances
    recalculate_remaining_balances(db)

    return {"message": "Transaction updated", "transaction": transaction.to_dict()}

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction and reorder IDs"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Delete the transaction
    db.delete(transaction)
    db.flush()  # Important: flush before reordering
    
    # Reorder IDs
    remaining_transactions = db.query(Transaction).order_by(Transaction.id).all()
    
    for new_id, trans in enumerate(remaining_transactions, start=1):
        if trans.id != new_id:
            trans.id = new_id
    
    db.commit()
    
    # Reset auto-increment
    try:
        db.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
        if remaining_transactions:
            db.execute(f"INSERT INTO sqlite_sequence (name, seq) VALUES ('transactions', {len(remaining_transactions)})")
        db.commit()
    except:
        pass  # Ignore if fails
    
    # Update balance
    recalculate_balance(db)
    
    return {
        "message": "Transaction deleted and IDs reordered",
        "deleted_id": transaction_id,
        "remaining_count": len(remaining_transactions)
    }

@app.post("/bulk/mark-reviewed")
async def bulk_mark_reviewed(db: Session = Depends(get_db)):
    """Mark all transactions as reviewed (remove needs_review flag)"""
    
    transactions = db.query(Transaction).filter(Transaction.needs_review == True).all()
    count = len(transactions)
    
    for transaction in transactions:
        transaction.needs_review = False
    
    db.commit()
    
    return {
        "message": f"Marked {count} transaction(s) as reviewed",
        "count": count
    }

@app.post("/bulk/delete-duplicates")
async def bulk_delete_duplicates(db: Session = Depends(get_db)):
    """Delete all transactions marked as duplicates"""
    
    duplicates = db.query(Transaction).filter(Transaction.is_duplicate == True).all()
    count = len(duplicates)
    
    for duplicate in duplicates:
        db.delete(duplicate)
    
    db.flush()
    
    # Reorder remaining IDs
    remaining_transactions = db.query(Transaction).order_by(Transaction.id).all()
    for new_id, trans in enumerate(remaining_transactions, start=1):
        if trans.id != new_id:
            trans.id = new_id
    
    # Reset auto-increment
    try:
        db.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
        if remaining_transactions:
            db.execute(f"INSERT INTO sqlite_sequence (name, seq) VALUES ('transactions', {len(remaining_transactions)})")
    except:
        pass
    
    db.commit()
    
    # Update balance
    recalculate_balance(db)
    
    return {
        "message": f"Deleted {count} duplicate transaction(s)",
        "count": count
    }

@app.post("/bulk/delete-all")
async def bulk_delete_all(db: Session = Depends(get_db)):
    """Delete ALL transactions - DANGEROUS! Start fresh"""
    
    all_transactions = db.query(Transaction).all()
    count = len(all_transactions)
    
    # Delete all
    for transaction in all_transactions:
        db.delete(transaction)
    
    db.commit()
    
    # Reset auto-increment counter to 0
    try:
        db.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
        db.commit()
    except:
        pass
    
    # Reset balance
    recalculate_balance(db)
    
    return {
        "message": f"Deleted all {count} transaction(s). Database reset.",
        "count": count
    }

@app.get("/balance")
async def get_balance(db: Session = Depends(get_db)):
    """Get current balance"""
    balance = db.query(Balance).first()
    if not balance:
        balance = Balance(opening_balance=0.0)
        db.add(balance)
        db.commit()
        db.refresh(balance)
    return balance.to_dict()

@app.post("/balance/set-opening")
async def set_opening_balance(opening_balance: float, db: Session = Depends(get_db)):
    """Set opening balance"""
    balance = db.query(Balance).first()
    if not balance:
        balance = Balance()
        db.add(balance)

    balance.opening_balance = opening_balance
    db.commit()

    # Recalculate current balance
    recalculate_balance(db)

    # Recalculate remaining balances for all transactions
    recalculate_remaining_balances(db)

    return {"message": "Opening balance set", "balance": balance.to_dict()}

@app.post("/export")
async def export_transactions(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export transactions (MVP 7)"""

    # Get transactions (ordered by date and id to match remaining balance calculation)
    if export_request.entry_ids:
        transactions = db.query(Transaction).filter(
            Transaction.id.in_(export_request.entry_ids)
        ).order_by(Transaction.date, Transaction.id).all()
    else:
        transactions = db.query(Transaction).order_by(Transaction.date, Transaction.id).all()

    entries = [t.to_dict() for t in transactions]

    # Export
    file_path = Exporter.export(entries, export_request.format)

    return {
        "message": "Export successful",
        "file_path": file_path,
        "total_entries": len(entries)
    }

@app.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics (MVP 8)"""
    
    transactions = db.query(Transaction).all()
    entries = [t.to_dict() for t in transactions]
    
    if not entries:
        return DashboardStats(
            total_entries=0,
            clean_entries=0,
            flagged_entries=0,
            duplicates=0,
            total_amount=0.0,
            category_breakdown={},
            confidence_distribution={}
        )
    
    # Calculate stats
    clean_entries = sum(1 for e in entries if not e["needs_review"])
    flagged_entries = sum(1 for e in entries if e["needs_review"])
    duplicates = sum(1 for e in entries if e["is_duplicate"])
    
    # Calculate total as net (income - expense)
    total_income = sum(e.get("income", 0) for e in entries)
    total_expense = sum(e.get("expense", 0) for e in entries)
    total_amount = total_income - total_expense
    
    # Category breakdown
    category_breakdown = {}
    for entry in entries:
        cat = entry["category"]
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
    
    # Confidence distribution
    confidence_dist = {"High": 0, "Medium": 0, "Low": 0}
    for entry in entries:
        conf_scores = entry["confidence"]
        avg_conf = sum(conf_scores.values()) / len(conf_scores)
        
        if avg_conf >= 0.8:
            confidence_dist["High"] += 1
        elif avg_conf >= 0.6:
            confidence_dist["Medium"] += 1
        else:
            confidence_dist["Low"] += 1
    
    return DashboardStats(
        total_entries=len(entries),
        clean_entries=clean_entries,
        flagged_entries=flagged_entries,
        duplicates=duplicates,
        total_amount=total_amount,
        category_breakdown=category_breakdown,
        confidence_distribution=confidence_dist
    )

@app.get("/risk-analysis")
async def analyze_risks(db: Session = Depends(get_db)):
    """Analyze transactions for financial risks and generate alerts"""

    transactions = db.query(Transaction).all()
    entries = [TransactionEntry(**t.to_dict()) for t in transactions]

    risk_detector = RiskDetector()
    result = risk_detector.analyze_transactions(entries)

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
