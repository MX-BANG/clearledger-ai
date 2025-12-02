"""
MVP 7: Clean Data Exporter
Exports processed transactions to various formats
"""

import pandas as pd
import json
from pathlib import Path
from typing import List
from datetime import datetime
from backend.config import EXPORT_DIR

class Exporter:
    
    @staticmethod
    def export_to_csv(entries: List[dict], filename: str = None) -> str:
        """
        Export transactions to CSV
        Returns: file path
        """
        if not filename:
            filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Flatten nested confidence scores
        flat_entries = []
        for entry in entries:
            flat_entry = {
                "Date": entry.get("date"),
                "Vendor": entry.get("vendor"),
                "Category": entry.get("category"),
                "Income": entry.get("income", 0.0),
                "Expense": entry.get("expense", 0.0),
                "Remaining Balance": entry.get("remaining_balance") or 0.0,
                "Notes": entry.get("notes", "")
            }
            flat_entries.append(flat_entry)

        df = pd.DataFrame(flat_entries)

        # Add summary row
        summary = {
            "Date": "TOTAL",
            "Vendor": "",
            "Category": "",
            "Income": df["Income"].sum(),
            "Expense": df["Expense"].sum(),
            "Remaining Balance": "",
            "Notes": f"Balance: {df['Income'].sum() - df['Expense'].sum()}"
        }
        df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
        
        # Save to file
        file_path = EXPORT_DIR / filename
        df.to_csv(file_path, index=False)
        
        return str(file_path)
    
    @staticmethod
    def export_to_excel(entries: List[dict], filename: str = None) -> str:
        """
        Export transactions to Excel with formatting
        Returns: file path
        """
        if not filename:
            filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Flatten entries
        flat_entries = []
        for entry in entries:
            flat_entry = {
                "Date": entry.get("date"),
                "Vendor": entry.get("vendor"),
                "Category": entry.get("category"),
                "Income": entry.get("income", 0.0),
                "Expense": entry.get("expense", 0.0),
                "Remaining Balance": entry.get("remaining_balance", 0.0),
                "Notes": entry.get("notes", "")
            }
            flat_entries.append(flat_entry)

        df = pd.DataFrame(flat_entries)

        # Add summary
        summary = {
            "Date": "TOTAL",
            "Vendor": "",
            "Category": "",
            "Income": df["Income"].sum(),
            "Expense": df["Expense"].sum(),
            "Remaining Balance": "",
            "Notes": f"Net: {df['Income'].sum() - df['Expense'].sum()}"
        }
        summary_df = pd.DataFrame([summary])
        
        # Save to file
        file_path = EXPORT_DIR / filename
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Auto-adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns if sheet_name == 'Transactions' else summary_df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max() if sheet_name == 'Transactions' else len(str(col)),
                        len(col)
                    ) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        return str(file_path)
    
    @staticmethod
    def export_to_json(entries: List[dict], filename: str = None) -> str:
        """
        Export transactions to JSON
        Returns: file path
        """
        if not filename:
            filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        file_path = EXPORT_DIR / filename
        
        with open(file_path, 'w') as f:
            json.dump(entries, f, indent=2, default=str)
        
        return str(file_path)
    
    @staticmethod
    def export(entries: List[dict], format: str, filename: str = None) -> str:
        """
        Export to specified format
        
        Args:
            entries: List of transaction entries
            format: 'csv', 'xlsx', or 'json'
            filename: Optional custom filename
        
        Returns:
            File path of exported file
        """
        format = format.lower()
        
        if format == 'csv':
            return Exporter.export_to_csv(entries, filename)
        elif format in ['xlsx', 'excel']:
            return Exporter.export_to_excel(entries, filename)
        elif format == 'json':
            return Exporter.export_to_json(entries, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def get_summary(entries: List[dict]) -> dict:
        """
        Generate export summary statistics
        """
        if not entries:
            return {
                "total_entries": 0,
                "total_amount": 0,
                "total_income": 0,
                "total_expense": 0,
                "categories": {},
                "needs_review": 0,
                "duplicates": 0
            }
        
        df = pd.DataFrame(entries)
        
        category_counts = df.groupby('category').size().to_dict() if 'category' in df else {}
        
        total_income = df['income'].sum() if 'income' in df else 0
        total_expense = df['expense'].sum() if 'expense' in df else 0
        
        return {
            "total_entries": len(entries),
            "total_income": total_income,
            "total_expense": total_expense,
            "total_amount": total_income - total_expense,
            "categories": category_counts,
            "needs_review": df['needs_review'].sum() if 'needs_review' in df else 0,
            "duplicates": df['is_duplicate'].sum() if 'is_duplicate' in df else 0,
            "date_range": {
                "from": df['date'].min() if 'date' in df else None,
                "to": df['date'].max() if 'date' in df else None
            }
        }

