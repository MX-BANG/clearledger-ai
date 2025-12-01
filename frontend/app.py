"""
Streamlit Frontend - Main Application
AI Bookkeeping Cleanup Engine Interface
"""

import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="AI Bookkeeping Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "http://localhost:8000"

def check_api_health():
    """Check if backend API is running"""
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

# Main app
def main():
    # Header
    st.markdown('<div class="main-header">🤖 AI Bookkeeping Cleanup Engine</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running! Please start the FastAPI server first.")
        st.code("cd backend && uvicorn main:app --reload", language="bash")
        st.stop()
    
    st.success("✅ Backend API is running")
    
    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    st.sidebar.info("""
    **How to use:**
    1. 📤 Upload your receipts/invoices
    2. ✏️ Review and edit extracted data
    3. 📊 View dashboard statistics
    4. 💾 Export clean data
    """)
    
    # Main content
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entries", get_total_entries())
    
    with col2:
        st.metric("Needs Review", get_needs_review_count())
    
    with col3:
        st.metric("Duplicates", get_duplicate_count())
    
    with col4:
        st.metric("Categories", get_category_count())
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📊 Quick Overview")
    
    try:
        response = requests.get(f"{API_URL}/dashboard")
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Category Breakdown")
                if stats["category_breakdown"]:
                    df = pd.DataFrame(
                        list(stats["category_breakdown"].items()),
                        columns=["Category", "Count"]
                    )
                    st.bar_chart(df.set_index("Category"))
                else:
                    st.info("No data yet. Upload some files to get started!")
            
            with col2:
                st.markdown("### Confidence Distribution")
                if stats["confidence_distribution"]:
                    conf_df = pd.DataFrame(
                        list(stats["confidence_distribution"].items()),
                        columns=["Level", "Count"]
                    )
                    st.bar_chart(conf_df.set_index("Level"))
    except Exception as e:
        st.error(f"Error fetching dashboard: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>Made by MSF</p>
    </div>
    """, unsafe_allow_html=True)

def get_total_entries():
    """Get total number of entries"""
    try:
        response = requests.get(f"{API_URL}/transactions")
        if response.status_code == 200:
            return len(response.json())
    except:
        pass
    return 0

def get_needs_review_count():
    """Get count of entries needing review"""
    try:
        response = requests.get(f"{API_URL}/transactions?needs_review=true")
        if response.status_code == 200:
            return len(response.json())
    except:
        pass
    return 0

def get_duplicate_count():
    """Get count of duplicate entries"""
    try:
        response = requests.get(f"{API_URL}/transactions")
        if response.status_code == 200:
            entries = response.json()
            return sum(1 for e in entries if e.get("is_duplicate", False))
    except:
        pass
    return 0

def get_category_count():
    """Get number of unique categories"""
    try:
        response = requests.get(f"{API_URL}/dashboard")
        if response.status_code == 200:
            stats = response.json()
            return len(stats.get("category_breakdown", {}))
    except:
        pass
    return 0

if __name__ == "__main__":
    main()