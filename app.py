import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. DATABASE SETUP
conn = sqlite3.connect('loan_banking_v4.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS loans 
             (id INTEGER PRIMARY KEY, name TEXT UNIQUE, principal REAL, rate REAL, start_date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payments 
             (id INTEGER PRIMARY KEY, loan_name TEXT, amount REAL, date TEXT)''')
conn.commit()

st.set_page_config(page_title="Advanced Loan Ledger", layout="wide")
st.title("🏦 Nepali Loan Tracker (Interest First Logic)")

# --- APP TABS ---
tab1, tab2 = st.tabs(["📊 Portfolio & Payments", "🧮 Real-time Settlement Tracker"])

# --- SIDEBAR: LOAN SETUP ---
st.sidebar.header("➕ Loan Setup")
new_l_name = st.sidebar.text_input("Loan Name (e.g., Sujata)")
new_l_principal = st.sidebar.number_input("Initial Principal (Sawa)", min_value=0.0)
new_l_rate = st.sidebar.number_input("Monthly Rate (%)", min_value=0.0, value=2.0)
new_l_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1))

if st.sidebar.button("Save Loan"):
    if new_l_name:
        c.execute('INSERT OR REPLACE INTO loans (name, principal, rate, start_date) VALUES (?, ?, ?, ?)',
                  (new_l_name, new_l_principal, new_l_rate, new_l_date.strftime('%Y-%m-%d')))
        conn.commit()
        st.sidebar.success(f"{new_l_name} Saved!")
        st.rerun()

# --- TAB 1: PAYMENTS & STATUS ---
with tab1:
    loans_df = pd.read_sql_query('SELECT * FROM loans', conn)
    if not loans_df.empty:
        loan_list = loans_df['name'].tolist()
        sel_loan = st.selectbox("Select Loan to Record Payment", loan_list)
        
        col1, col2 = st.columns(2)
        with col1:
            p_amount = st.number_input("Total Amount Paid (Kista)", min_value=0.0)
        with col2:
            p_date = st.date_input("Date of Payment", datetime.now())
            
        if st.button("➕ Record Payment & Recalculate"):
            c.execute('INSERT INTO payments (loan_name, amount, date) VALUES (?, ?, ?)', 
                      (sel_loan, p_amount, p_date.strftime('%Y-%m-%d')))
            conn.commit()
            st.success("Payment Recorded!")
            st.rerun()

        st.divider()
        st.subheader("Raw Payment Records")
        raw_pays = pd.read_sql_query('SELECT date, amount FROM payments WHERE loan_name = ? ORDER BY date DESC', conn, params=(sel_loan,))
        st.dataframe(raw_pays, use_container_width=True)
    else:
        st.info("Sidebar bata Loan setup garnuhos.")

# --- TAB 2: SETTLEMENT TRACKER (BANKING LOGIC) ---
with tab2:
    if not loans_df.empty:
        target = st.selectbox("Detailed Interest Analysis:", loan_list)
        
        # Loan Info
        c.execute('SELECT principal, rate, start_date FROM loans WHERE name = ?', (target,))
        initial_sawa, rate, start_str = c.fetchone()
        start_dt = datetime.strptime(start_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # Payments
        pays = pd.read_sql_query('SELECT amount, date FROM payments WHERE loan_name = ? ORDER BY date ASC', conn, params=(target,))
        
        # --- THE CALCULATOR CORE ---
        current_sawa = initial_sawa
        last_dt = start_dt
        daily_rate = (rate / 100) / 30
        
        settlement_data = []
        
        for _, row in pays.iterrows():
            p_dt = datetime.strptime(row['date'], '%Y-%m-%d').date()
            total_paid = row['amount']
            
            # 1. Calculate Interest until THIS payment date
            days = (p_dt - last_dt).days
            interest_due = current_sawa * daily_rate * days if days > 0 else 0
            
            # 2. Split Payment (Interest first, then Principal)
            if total_paid >= interest_due:
                interest_paid = interest_due
                principal_paid = total_paid - interest_due
            else:
                interest_paid = total_paid
                principal_paid = 0
            
            # 3. Update Balance
            old_sawa = current_sawa
            current_sawa -= principal_paid
            
            settlement_data.append({
                "Date": p_dt,
                "Total Paid": total_paid,
                "Interest Cleared": round(interest_paid, 2),
                "Principal Cleared": round(principal_paid, 2),
                "Remaining Sawa": round(current_sawa, 2)
            })
            last_dt = p_dt

        # Calculate Interest from Last Payment to TODAY
        days_since = (today - last_dt).days
        current_interest_pending = current_sawa * daily_rate * days_since
        
        # Display Stats
        st.header(f"Live Status: {target}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Sawa (Baki)", f"Rs. {current_sawa:,.2f}")
        m2.metric("Interest Pending (Aja samma)", f"Rs. {current_interest_pending:,.2f}")
        m3.metric("Daily Interest Cost", f"Rs. {current_sawa * daily_rate:,.2f}")
        
        if settlement_data:
            st.subheader("Settlement History (Kati Sawa katchha, kati Byaj?)")
            st.table(pd.DataFrame(settlement_data))
        else:
            st.info("No payments yet to show settlement.")