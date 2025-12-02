"""
Balance Management Page
Set opening balance and view financial summary
"""

import streamlit as st
import requests

st.set_page_config(page_title="Balance Management", page_icon="💰", layout="wide")

API_URL = "http://localhost:8000"

st.title("💰 Balance Management")

st.markdown("""
Track your financial balance in real-time. Set your opening balance and watch it update automatically 
with every income and expense transaction.
""")

# Get current balance
try:
    response = requests.get(f"{API_URL}/balance")
    if response.status_code == 200:
        balance_data = response.json()
        
        # Display current balance - Big metrics
        st.markdown("### 📊 Current Financial Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Opening Balance", 
                f"PKR {balance_data['opening_balance']:,.2f}",
                help="Your starting balance"
            )
        
        with col2:
            st.metric(
                "Total Income", 
                f"PKR {balance_data['total_income']:,.2f}", 
                delta=f"+{balance_data['total_income']:,.2f}",
                delta_color="normal",
                help="All income transactions"
            )
        
        with col3:
            st.metric(
                "Total Expense", 
                f"PKR {balance_data['total_expense']:,.2f}",
                delta=f"-{balance_data['total_expense']:,.2f}",
                delta_color="inverse",
                help="All expense transactions"
            )
        
        with col4:
            current = balance_data['current_balance']
            opening = balance_data['opening_balance']
            diff = current - opening
            st.metric(
                "Current Balance", 
                f"PKR {current:,.2f}",
                delta=f"{diff:+,.2f}",
                delta_color="normal" if diff >= 0 else "inverse",
                help="Opening + Income - Expense"
            )
        
        # Visual progress bar
        st.markdown("---")
        st.markdown("### 📈 Balance Flow")
        
        # Calculate percentages for visual
        total_movement = balance_data['total_income'] + balance_data['total_expense']
        if total_movement > 0:
            income_pct = (balance_data['total_income'] / total_movement) * 100
            expense_pct = (balance_data['total_expense'] / total_movement) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"💰 Income: {income_pct:.1f}% of total movement")
                st.progress(income_pct / 100)
            
            with col2:
                st.error(f"💸 Expense: {expense_pct:.1f}% of total movement")
                st.progress(expense_pct / 100)
        
        # Set opening balance
        st.markdown("---")
        st.markdown("### 🎯 Set Opening Balance")
        st.info("💡 Set your starting balance here. This is the amount you had before tracking transactions.")
        
        with st.form("set_balance"):
            new_opening = st.number_input(
                "Enter Opening Balance (PKR)",
                value=float(balance_data['opening_balance']),
                step=1000.0,
                help="Your account balance before you started tracking"
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col2:
                submitted = st.form_submit_button("💾 Update Opening Balance", type="primary", use_container_width=True)
            
            if submitted:
                update_response = requests.post(
                    f"{API_URL}/balance/set-opening",
                    params={"opening_balance": new_opening}
                )
                
                if update_response.status_code == 200:
                    st.success("✅ Opening balance updated successfully!")
                    st.balloons()
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Error: {update_response.text}")
        
        # Balance calculation explanation
        st.markdown("---")
        st.markdown("### 📚 How Balance is Calculated")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Formula:**
            ```
            Current Balance = Opening Balance 
                            + Total Income 
                            - Total Expense
            ```
            """)
        
        with col2:
            st.markdown(f"""
            **Your Calculation:**
            ```
            {current:,.2f} = {opening:,.2f}
                        + {balance_data['total_income']:,.2f}
                        - {balance_data['total_expense']:,.2f}
            ```
            """)
        
        st.success("""
        ✅ **Auto-Updated:** Your balance updates automatically every time you:
        - Upload a receipt
        - Add a manual transaction
        - Delete a transaction
        """)
        
        # Quick actions
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Upload Transactions", use_container_width=True):
                st.switch_page("pages/1_📤_Upload.py")
        
        with col2:
            if st.button("📊 View Dashboard", use_container_width=True):
                st.switch_page("pages/3_📊_Dashboard.py")
        
        with col3:
            if st.button("💾 Export Data", use_container_width=True):
                st.switch_page("pages/5_💾_Export.py")
        
except Exception as e:
    st.error(f"❌ Error loading balance: {str(e)}")
    st.info("Make sure the backend API is running!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>💰 Balance updates in real-time with every transaction</p>
</div>
""", unsafe_allow_html=True)