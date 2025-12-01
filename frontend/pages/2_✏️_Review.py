"""
Review Page - MVP 6: Human-in-the-Loop Editor
Review and edit extracted transactions
"""

import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Review Transactions", page_icon="✏️", layout="wide")

API_URL = "http://localhost:8000"

st.title("✏️ Review & Edit Transactions")

# Filter options
st.sidebar.markdown("### 🔍 Filters")
show_all = st.sidebar.checkbox("Show all entries", value=True)
show_needs_review = st.sidebar.checkbox("Show entries needing review", value=False)
show_duplicates = st.sidebar.checkbox("Show duplicates only", value=False)

# Fetch transactions
try:
    params = {}
    if not show_all and show_needs_review:
        params['needs_review'] = 'true'
    
    response = requests.get(f"{API_URL}/transactions", params=params)
    
    if response.status_code == 200:
        transactions = response.json()
        
        # Apply filters
        if show_duplicates:
            transactions = [t for t in transactions if t.get('is_duplicate', False)]
        
        if not transactions:
            st.info("No transactions found. Upload some files first!")
            st.stop()
        
        st.success(f"Found {len(transactions)} transaction(s)")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            needs_review = sum(1 for t in transactions if t.get('needs_review', False))
            st.metric("Needs Review", needs_review)
        
        with col2:
            duplicates = sum(1 for t in transactions if t.get('is_duplicate', False))
            st.metric("Duplicates", duplicates)
        
        with col3:
            total_amount = sum(t['amount'] for t in transactions)
            st.metric("Total Amount", f"{total_amount:,.0f} PKR")
        
        with col4:
            categories = len(set(t['category'] for t in transactions))
            st.metric("Categories", categories)
        
        st.markdown("---")
        
        # Edit mode selection
        edit_mode = st.radio(
            "Select mode:",
            ["View Only", "Edit Mode"],
            horizontal=True
        )
        
        # Display transactions
        for i, transaction in enumerate(transactions):
            # Determine card color
            card_style = "background-color: #fff3cd;" if transaction.get('needs_review') else "background-color: #f8f9fa;"
            
            with st.container():
                st.markdown(f'<div style="padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; {card_style}">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### Transaction #{transaction['id']}")
                
                with col2:
                    if transaction.get('needs_review'):
                        st.warning("⚠️ Needs Review")
                    if transaction.get('is_duplicate'):
                        st.info(f"🔄 Duplicate of #{transaction.get('duplicate_of')}")
                
                if edit_mode == "Edit Mode":
                    # Editable form
                    with st.form(key=f"edit_form_{transaction['id']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            new_date = st.text_input("Date", transaction['date'])
                            new_vendor = st.text_input("Vendor", transaction['vendor'])
                        
                        with col2:
                            new_amount = st.number_input("Amount", value=float(transaction['amount']), min_value=0.0)
                            new_currency = st.text_input("Currency", transaction['currency'])
                        
                        with col3:
                            categories = ["Food", "Fuel", "Transport", "Utilities", "Rent", "Office", "Other"]
                            current_cat = transaction['category']
                            cat_index = categories.index(current_cat) if current_cat in categories else 0
                            new_category = st.selectbox("Category", categories, index=cat_index)
                            new_notes = st.text_area("Notes", transaction.get('notes', ''), height=50)
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            save_btn = st.form_submit_button("💾 Save Changes", type="primary")
                        
                        with col2:
                            if transaction.get('is_duplicate'):
                                keep_btn = st.form_submit_button("✅ Keep (Not Duplicate)")
                        
                        with col3:
                            delete_btn = st.form_submit_button("🗑️ Delete", type="secondary")
                        
                        # Handle actions
                        if save_btn:
                            updated_data = {
                                "date": new_date,
                                "vendor": new_vendor,
                                "amount": new_amount,
                                "currency": new_currency,
                                "category": new_category,
                                "notes": new_notes,
                                "needs_review": False
                            }
                            
                            update_response = requests.put(
                                f"{API_URL}/transactions/{transaction['id']}",
                                json=updated_data
                            )
                            
                            if update_response.status_code == 200:
                                st.success("✅ Transaction updated!")
                                st.rerun()
                            else:
                                st.error("❌ Update failed")
                        
                        if delete_btn:
                            delete_response = requests.delete(
                                f"{API_URL}/transactions/{transaction['id']}"
                            )
                            
                            if delete_response.status_code == 200:
                                st.success("🗑️ Transaction deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Delete failed")
                        
                        if transaction.get('is_duplicate') and keep_btn:
                            keep_response = requests.put(
                                f"{API_URL}/transactions/{transaction['id']}",
                                json={"is_duplicate": False, "duplicate_of": None}
                            )
                            
                            if keep_response.status_code == 200:
                                st.success("✅ Marked as not duplicate!")
                                st.rerun()
                
                else:
                    # View only mode
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Date:**", transaction['date'])
                        st.write("**Vendor:**", transaction['vendor'])
                    
                    with col2:
                        st.write("**Amount:**", f"{transaction['amount']} {transaction['currency']}")
                        st.write("**Category:**", transaction['category'])
                    
                    with col3:
                        st.write("**Notes:**", transaction.get('notes', 'N/A'))
                        st.write("**Source:**", transaction.get('source_file', 'N/A'))
                    
                    # Confidence scores
                    with st.expander("📊 Confidence Scores"):
                        conf = transaction['confidence']
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Vendor", f"{conf['vendor']:.0%}")
                        with col2:
                            st.metric("Amount", f"{conf['amount']:.0%}")
                        with col3:
                            st.metric("Date", f"{conf['date']:.0%}")
                        with col4:
                            st.metric("Category", f"{conf['category']:.0%}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Bulk actions
        st.markdown("---")
        st.markdown("### 🔧 Bulk Actions")
        
        # Count duplicates
        duplicates_count = sum(1 for t in transactions if t.get('is_duplicate', False))
        needs_review_count = sum(1 for t in transactions if t.get('needs_review', False))
        total_count = len(transactions)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"**{needs_review_count}** items need review")
            if st.button("✅ Mark All as Reviewed", use_container_width=True, disabled=(needs_review_count == 0)):
                with st.spinner("Marking all as reviewed..."):
                    try:
                        response = requests.post(f"{API_URL}/bulk/mark-reviewed")
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            st.markdown(f"**{duplicates_count}** duplicate(s) found")
            if duplicates_count > 0:
                if st.button("🗑️ Delete All Duplicates", use_container_width=True, type="secondary"):
                    st.session_state['confirm_delete_duplicates'] = True
                
                # Show confirmation if button clicked
                if st.session_state.get('confirm_delete_duplicates', False):
                    st.warning(f"⚠️ About to delete {duplicates_count} duplicate transaction(s). IDs will be reordered!")
                    
                    col_cancel, col_confirm = st.columns(2)
                    
                    with col_cancel:
                        if st.button("❌ Cancel", key="cancel_dup", use_container_width=True):
                            st.session_state['confirm_delete_duplicates'] = False
                            st.rerun()
                    
                    with col_confirm:
                        if st.button("🔴 Confirm Delete", key="confirm_dup", use_container_width=True, type="primary"):
                            with st.spinner("Deleting duplicates..."):
                                try:
                                    response = requests.post(f"{API_URL}/bulk/delete-duplicates")
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success(f"✅ {result['message']}")
                                        st.session_state['confirm_delete_duplicates'] = False
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {response.text}")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
            else:
                st.button("🗑️ Delete All Duplicates", use_container_width=True, disabled=True)
                st.caption("No duplicates found")
        
        with col3:
            st.markdown("**Export your data**")
            if st.button("📥 Go to Export Page", use_container_width=True):
                st.switch_page("pages/4_💾_Export.py")
        
        with col4:
            st.markdown(f"**{total_count}** total transactions")
            if st.button("🔴 Delete ALL Data", use_container_width=True, type="secondary"):
                st.session_state['confirm_delete_all'] = True
            
            # Show confirmation for delete all
            if st.session_state.get('confirm_delete_all', False):
                st.error(f"⚠️ DANGER: About to delete ALL {total_count} transactions! This cannot be undone!")
                
                col_cancel, col_confirm = st.columns(2)
                
                with col_cancel:
                    if st.button("❌ Cancel", key="cancel_all", use_container_width=True):
                        st.session_state['confirm_delete_all'] = False
                        st.rerun()
                
                with col_confirm:
                    if st.button("💀 YES, DELETE EVERYTHING", key="confirm_all", use_container_width=True, type="primary"):
                        with st.spinner("Deleting all transactions..."):
                            try:
                                response = requests.post(f"{API_URL}/bulk/delete-all")
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success(f"✅ {result['message']}")
                                    st.info("🎯 Database reset. You can start fresh!")
                                    st.session_state['confirm_delete_all'] = False
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error: {response.text}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
    
    else:
        st.error(f"❌ Error fetching transactions: {response.status_code}")

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("Make sure the backend API is running!")