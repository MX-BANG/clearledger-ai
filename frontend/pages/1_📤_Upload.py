"""
Upload Page - MVP 1 & 2
Upload and process receipts, invoices, and documents
"""

import streamlit as st
import requests
from pathlib import Path

st.set_page_config(page_title="Upload Files", page_icon="📤", layout="wide")

API_URL = "http://localhost:8000"

st.title("📤 Upload Documents")

st.markdown("""
Upload your receipts, invoices, screenshots, or CSV/Excel files.  
The AI will automatically extract and structure the data.
""")

# File uploader
uploaded_files = st.file_uploader(
    "Choose files to upload",
    type=["jpg", "jpeg", "png", "pdf", "csv", "xlsx"],
    accept_multiple_files=True,
    help="Supported formats: Images (JPG, PNG), PDF, CSV, Excel"
)

if uploaded_files:
    st.info(f"📁 {len(uploaded_files)} file(s) selected")
    
    # Show file details
    with st.expander("View uploaded files"):
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size / 1024:.2f} KB)")
    
    # Process button
    if st.button("🚀 Process Files", type="primary"):
        
        with st.spinner("Processing files... This may take a moment."):
            try:
                # Prepare files for upload
                files = [
                    ("files", (file.name, file, file.type))
                    for file in uploaded_files
                ]
                
                # Send to API
                response = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    timeout=300  # 5 minutes timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Success message
                    st.success(f"✅ Successfully processed {result['successful']} out of {result['total_files']} files!")
                    
                    # Show results
                    st.markdown("### 📊 Processing Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Files", result['total_files'])
                    with col2:
                        st.metric("Successful", result['successful'], delta=result['successful'])
                    with col3:
                        st.metric("Failed", result['failed'], delta=-result['failed'] if result['failed'] > 0 else 0)
                    
                    # Show extracted entries
                    if result['entries']:
                        st.markdown("### ✅ Extracted Transactions")
                        
                        for i, entry in enumerate(result['entries'], 1):
                            with st.expander(f"Entry {i}: {entry['vendor']} - {entry['amount']} {entry['currency']}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Date:**", entry['date'])
                                    st.write("**Vendor:**", entry['vendor'])
                                    st.write("**Amount:**", f"{entry['amount']} {entry['currency']}")
                                    st.write("**Category:**", entry['category'])
                                    st.write("**Notes:**", entry.get('notes', 'N/A'))
                                
                                with col2:
                                    st.write("**Confidence Scores:**")
                                    conf = entry['confidence']
                                    st.progress(conf['vendor'], text=f"Vendor: {conf['vendor']:.0%}")
                                    st.progress(conf['amount'], text=f"Amount: {conf['amount']:.0%}")
                                    st.progress(conf['date'], text=f"Date: {conf['date']:.0%}")
                                    st.progress(conf['category'], text=f"Category: {conf['category']:.0%}")
                                    
                                    if entry.get('needs_review'):
                                        st.warning("⚠️ This entry needs review")
                                    
                                    if entry.get('is_duplicate'):
                                        st.warning(f"🔄 Possible duplicate of entry #{entry.get('duplicate_of')}")
                    
                    # Show errors if any
                    if result['errors']:
                        st.markdown("### ❌ Errors")
                        for error in result['errors']:
                            st.error(f"**{error['filename']}:** {error['error']}")
                    
                    # Navigation
                    st.markdown("---")
                    st.info("👉 Go to the **Review** page to edit entries or check the **Dashboard** for statistics.")
                    
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Try uploading fewer files at once.")
            except Exception as e:
                st.error(f"❌ Error processing files: {str(e)}")

else:
    st.info("👆 Upload files above to get started")
    
    # Example section
    st.markdown("---")
    st.markdown("### 📝 Supported File Types")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Images:**
        - Receipt photos (JPG, PNG)
        - WhatsApp screenshots
        - Invoice scans
        """)
    
    with col2:
        st.markdown("""
        **Documents:**
        - PDF invoices
        - CSV transaction lists
        - Excel spreadsheets
        """)
    
    st.markdown("---")
    st.markdown("### 💡 Tips for Best Results")
    st.markdown("""
    - Take clear, well-lit photos of receipts
    - Ensure text is readable and not blurry
    - Upload files in small batches (5-10 at a time)
    - Review AI-extracted data before exporting
    """)