"""
Dashboard Page - MVP 8: Processing Summary Dashboard
View statistics and analytics
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

API_URL = "http://localhost:8000"

st.title("📊 Analytics Dashboard")

# Fetch dashboard stats
try:
    response = requests.get(f"{API_URL}/dashboard")
    
    if response.status_code == 200:
        stats = response.json()
        
        # Main metrics
        st.markdown("### 📈 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Entries",
                stats['total_entries'],
                help="Total number of transactions processed"
            )
        
        with col2:
            clean_percentage = (stats['clean_entries'] / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
            st.metric(
                "Clean Entries",
                stats['clean_entries'],
                delta=f"{clean_percentage:.1f}%",
                help="Entries that don't need review"
            )
        
        with col3:
            st.metric(
                "Needs Review",
                stats['flagged_entries'],
                delta=-stats['flagged_entries'] if stats['flagged_entries'] > 0 else 0,
                help="Entries flagged for manual review"
            )
        
        with col4:
            st.metric(
                "Duplicates Found",
                stats['duplicates'],
                help="Potential duplicate transactions"
            )
        
        st.markdown("---")
        
        # Financial overview
        st.markdown("### 💰 Financial Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Total Amount",
                f"PKR {stats['total_amount']:,.2f}",
                help="Sum of all transaction amounts"
            )
        
        with col2:
            avg_amount = stats['total_amount'] / stats['total_entries'] if stats['total_entries'] > 0 else 0
            st.metric(
                "Average Transaction",
                f"PKR {avg_amount:,.2f}",
                help="Average amount per transaction"
            )
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📂 Category Breakdown")
            
            if stats['category_breakdown']:
                # Prepare data
                cat_df = pd.DataFrame(
                    list(stats['category_breakdown'].items()),
                    columns=['Category', 'Count']
                )
                
                # Create pie chart
                fig = px.pie(
                    cat_df,
                    values='Count',
                    names='Category',
                    title='Transactions by Category',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Table view
                with st.expander("View details"):
                    st.dataframe(cat_df, use_container_width=True)
            else:
                st.info("No data available yet")
        
        with col2:
            st.markdown("### 💰 Income vs Expense (Monthly)")
            
            if stats['total_entries'] > 0:
                # Get all transactions
                trans_response = requests.get(f"{API_URL}/transactions?limit=1000")
                if trans_response.status_code == 200:
                    all_trans = trans_response.json()
                    
                    if all_trans:
                        # Group by month
                        df = pd.DataFrame(all_trans)
                        df['date'] = pd.to_datetime(df['date'])
                        df['month'] = df['date'].dt.strftime('%b %Y')
                        
                        monthly = df.groupby('month').agg({
                            'income': 'sum',
                            'expense': 'sum'
                        }).reset_index()
                        
                        # Create bar chart
                        fig = go.Figure(data=[
                            go.Bar(name='💰 Income', x=monthly['month'], y=monthly['income'], marker_color='#28a745'),
                            go.Bar(name='💸 Expense', x=monthly['month'], y=monthly['expense'], marker_color='#dc3545')
                        ])
                        
                        fig.update_layout(
                            barmode='group',
                            title='Monthly Income vs Expense',
                            xaxis_title='Month',
                            yaxis_title='Amount (PKR)',
                            legend=dict(x=0.01, y=0.99)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show monthly summary table
                        with st.expander("📋 View monthly breakdown"):
                            monthly['Net'] = monthly['income'] - monthly['expense']
                            st.dataframe(monthly, use_container_width=True)
                    else:
                        st.info("No transaction data yet")
                else:
                    st.error("Failed to load transactions")
            else:
                st.info("No data available yet")
        
        st.markdown("---")
        
        # Data quality insights
        st.markdown("### 🔍 Data Quality Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quality_score = (stats['clean_entries'] / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
            
            st.markdown("#### Overall Quality Score")
            
            # Custom gauge
            if quality_score >= 80:
                color = "green"
                status = "Excellent ✨"
            elif quality_score >= 60:
                color = "orange"
                status = "Good 👍"
            else:
                color = "red"
                status = "Needs Improvement ⚠️"
            
            st.markdown(f'<h2 style="color: {color};">{quality_score:.1f}%</h2>', unsafe_allow_html=True)
            st.markdown(f"**Status:** {status}")
        
        with col2:
            st.markdown("#### Processing Summary")
            st.write(f"✅ Successfully processed: **{stats['clean_entries']}**")
            st.write(f"⚠️ Flagged for review: **{stats['flagged_entries']}**")
            st.write(f"🔄 Duplicates detected: **{stats['duplicates']}**")
        
        with col3:
            st.markdown("#### Recommendations")
            
            if stats['flagged_entries'] > 0:
                st.warning(f"👉 Review {stats['flagged_entries']} flagged entries")
            
            if stats['duplicates'] > 0:
                st.info(f"👉 Check {stats['duplicates']} potential duplicates")
            
            if stats['flagged_entries'] == 0 and stats['duplicates'] == 0:
                st.success("✅ All data looks clean!")
        
        st.markdown("---")
        
        # Export section
        st.markdown("### 💾 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export All Data", type="primary"):
                st.info("👉 Go to the Export page to download your data")
        
        with col2:
            if st.button("✏️ Review Flagged Items"):
                st.info("👉 Go to the Review page to edit entries")
        
        with col3:
            if st.button("📤 Upload More Files"):
                st.info("👉 Go to the Upload page to add more data")
        
        # Fetch actual transactions for detailed analysis
        st.markdown("---")
        st.markdown("### 📋 Recent Transactions")
        
        trans_response = requests.get(f"{API_URL}/transactions?limit=10")
        
        if trans_response.status_code == 200:
            recent_trans = trans_response.json()
            
            if recent_trans:
                # Create DataFrame
                df = pd.DataFrame([
                    {
                        'ID': t['id'],
                        'Date': t['date'],
                        'Vendor': t['vendor'],
                        'Amount': t['amount'],
                        'Category': t['category'],
                        'Status': '⚠️ Review' if t.get('needs_review') else '✅ Clean'
                    }
                    for t in recent_trans
                ])
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No transactions yet")
    
    else:
        st.error(f"❌ Error fetching dashboard data: {response.status_code}")

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("Make sure the backend API is running!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Dashboard auto-refreshes when you reload the page</p>
</div>
""", unsafe_allow_html=True)