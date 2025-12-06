"""
Export Page - MVP 7: Clean Data Exporter
Export processed data in various formats
"""
import os
import streamlit as st
import requests
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Export Data", page_icon="💾", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("💾 Export Clean Data")

st.markdown("""
Export your cleaned and verified bookkeeping data in various formats.  
All exported files will be saved in the `data/exports/` directory.
""")

# Fetch transactions
try:
    response = requests.get(f"{API_URL}/transactions")
    
    if response.status_code == 200:
        transactions = response.json()
        
        if not transactions:
            st.warning("⚠️ No data to export. Upload and process some files first!")
            st.stop()
        
        st.success(f"✅ {len(transactions)} transaction(s) ready for export")
        
        # Export options
        st.markdown("### ⚙️ Export Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Select Export Format",
                ["CSV", "Excel (XLSX)", "JSON"],
                help="Choose the format for your export file"
            )
        
        with col2:
            export_filter = st.selectbox(
                "Select Data to Export",
                ["All Transactions", "Clean Only (Exclude Flagged)", "Flagged Only", "Exclude Duplicates"],
                help="Filter which transactions to include"
            )
        
        # Custom filename
        filename = st.text_input(
            "Custom Filename (optional)",
            placeholder="my_bookkeeping_data",
            help="Leave empty for auto-generated filename with timestamp"
        )
        
        # Preview section
        st.markdown("---")
        st.markdown("### 👀 Data Preview")
        
        # Filter data based on selection
        filtered_trans = transactions.copy()
        
        if export_filter == "Clean Only (Exclude Flagged)":
            filtered_trans = [t for t in filtered_trans if not t.get('needs_review', False)]
        elif export_filter == "Flagged Only":
            filtered_trans = [t for t in filtered_trans if t.get('needs_review', False)]
        elif export_filter == "Exclude Duplicates":
            filtered_trans = [t for t in filtered_trans if not t.get('is_duplicate', False)]
        
        # Show preview
        if filtered_trans:
            st.info(f"📊 {len(filtered_trans)} transaction(s) will be exported")
            
            # Create preview DataFrame
            preview_df = pd.DataFrame([
                {
                    'Date': t['date'],
                    'Vendor': t['vendor'],
                    'Income': t.get('income', 0),
                    'Expense': t.get('expense', 0),
                    'Type': t.get('transaction_type', 'expense'),
                    'Currency': t['currency'],
                    'Category': t['category'],
                    'Notes': t.get('notes', '')[:50] + '...' if len(t.get('notes', '')) > 50 else t.get('notes', ''),
                    'Status': '⚠️ Review' if t.get('needs_review') else '✅ Clean'
                }
                for t in filtered_trans[:100]  # Show first 100
            ])
            
            st.dataframe(preview_df, use_container_width=True, height=400)
            
            if len(filtered_trans) > 100:
                st.caption(f"Showing first 100 of {len(filtered_trans)} transactions")
        else:
            st.warning("No transactions match the selected filter")
            st.stop()
        
        # Export statistics
        st.markdown("---")
        st.markdown("### 📊 Export Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Entries", len(filtered_trans))
        
        with col2:
            total_amount = sum(t.get('income', 0) - t.get('expense', 0) for t in filtered_trans)
            st.metric("Total Amount", f"PKR {total_amount:,.2f}")
        
        with col3:
            categories = len(set(t['category'] for t in filtered_trans))
            st.metric("Categories", categories)
        
        with col4:
            date_range = f"{min(t['date'] for t in filtered_trans)} to {max(t['date'] for t in filtered_trans)}"
            st.metric("Date Range", date_range)
        
        # Export button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Export Data", type="primary", use_container_width=True):
                
                with st.spinner("Exporting data..."):
                    try:
                        # Determine format
                        format_map = {
                            "CSV": "csv",
                            "Excel (XLSX)": "xlsx",
                            "JSON": "json"
                        }
                        
                        export_format_code = format_map[export_format]
                        
                        # Prepare request
                        export_data = {
                            "format": export_format_code,
                            "entry_ids": [t['id'] for t in filtered_trans] if export_filter != "All Transactions" else None
                        }
                        
                        # Send export request
                        export_response = requests.post(
                            f"{API_URL}/export",
                            json=export_data
                        )
                        
                        if export_response.status_code == 200:
                            result = export_response.json()
                            
                            st.success("✅ Export successful!")
                            
                            st.markdown(f"""
                            ### 🎉 Export Complete!
                            
                            **File Location:** `{result['file_path']}`
                            
                            **Entries Exported:** {result['total_entries']}
                            
                            ---
                            
                            Your file has been saved to the exports directory.  
                            You can find it at: `{result['file_path']}`
                            """)
                            
                            # Show download button (if running locally)
                            file_path = Path(result['file_path'])
                            if file_path.exists():
                                with open(file_path, 'rb') as f:
                                    st.download_button(
                                        label=f"📥 Download {export_format}",
                                        data=f,
                                        file_name=file_path.name,
                                        mime={
                                            'csv': 'text/csv',
                                            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                            'json': 'application/json'
                                        }.get(export_format_code)
                                    )
                        else:
                            st.error(f"❌ Export failed: {export_response.text}")
                    
                    except Exception as e:
                        st.error(f"❌ Error during export: {str(e)}")
        
        # Additional info
        st.markdown("---")
        st.markdown("### 📝 Export Format Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **CSV Format**
            - Simple text format
            - Compatible with Excel, Google Sheets
            - Easy to import into accounting software
            - Smaller file size
            """)
        
        with col2:
            st.markdown("""
            **Excel (XLSX) Format**
            - Rich formatting
            - Includes confidence scores
            - Multiple sheets possible
            - Best for manual review
            """)
        
        with col3:
            st.markdown("""
            **JSON Format**
            - Complete data structure
            - Includes all metadata
            - Machine-readable
            - Best for further processing
            """)
    
    else:
        st.error(f"❌ Error fetching transactions: {response.status_code}")

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("Make sure the backend API is running!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>💡 Tip: Review your data in the <b>Review</b> page before exporting for best results</p>
</div>
""", unsafe_allow_html=True)