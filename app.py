import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# --- DATABASE SETUP ---
DB_FILE = 'loan_data.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS loans 
                 (name TEXT, principal REAL, rate REAL, start_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (loan_name TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- APP CONFIG ---
st.set_page_config(page_title="Personal Loan Tracker", layout="wide")
st.title("🏦 My Private Loan Ledger")

# --- DATABASE FUNCTIONS ---
def add_loan(name, p, r, d):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO loans VALUES (?,?,?,?)", (name, p, r, str(d)))
    conn.commit()
    conn.close()

def add_payment(l_name, amt, dt):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO payments VALUES (?,?,?)", (l_name, amt, str(dt)))
    conn.commit()
    conn.close()

def get_loans():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM loans", conn)
    conn.close()
    return df

def get_payments():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM payments", conn)
    conn.close()
    return df
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM payments", conn)
    conn.close()
    return df

# --- SIDEBAR: SAFETY FIRST ---
st.sidebar.header("⚙️ Data Control")
if st.sidebar.button("📦 Prepare Backup File"):
    l_df = get_loans()
    p_df = get_payments()
    with pd.ExcelWriter("loan_backup.xlsx") as writer:
        l_df.to_excel(writer, sheet_name="loans", index=False)
        p_df.to_excel(writer, sheet_name="payments", index=False)
    
    with open("loan_backup.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Excel Now", f, file_name=f"Backup_{datetime.now().strftime('%Y-%m-%d')}.xlsx")

st.sidebar.divider()
up_file = st.sidebar.file_uploader("📂 Restore from Excel", type="xlsx")
if up_file and st.sidebar.button("✅ Restore Now"):
    l_up = pd.read_excel(up_file, sheet_name="loans")
    p_up = pd.read_excel(up_file, sheet_name="payments")
    conn = sqlite3.connect(DB_FILE)
    l_up.to_sql("loans", conn, if_exists="replace", index=False)
    p_up.to_sql("payments", conn, if_exists="replace", index=False)
    conn.close()
    st.sidebar.success("Data Restored Successfully!")
    st.rerun()

# --- MAIN UI ---
t1, t2, t3 = st.tabs(["➕ Add New", "💸 Payments", "📊 My Reports"])

with t1:
    st.subheader("Register New Loan")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Borrower Name")
        p_amt = st.number_input("Principal Amount", min_value=0.0)
    with c2:
        rate = st.number_input("Monthly Interest (%)", value=2.0)
        s_date = st.date_input("Start Date")
    
    if st.button("Save Loan Entry"):
        if name:
            add_loan(name, p_amt, rate, s_date)
            st.success(f"Record for {name} saved!")
            st.rerun()

with t2:
    st.subheader("Add Payment Received")
    loans_df = get_loans()
    if not loans_df.empty:
        l_names = loans_df['name'].tolist()
        sel_name = st.selectbox("Select Person", l_names)
        amt = st.number_input("Amount Paid", min_value=0.0)
        dt = st.date_input("Payment Date")
        if st.button("Submit Payment"):
            add_payment(sel_name, amt, dt)
            st.success("Payment Recorded!")
            st.rerun()

with t3:
    st.subheader("Live Financial Status")
    loans_df = get_loans()
    pay_df = get_payments()
    
    if not loans_df.empty:
        for _, row in loans_df.iterrows():
            sawa = row['principal']
            byaj_rate = row['rate']
            s_dt = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
            
            p_history = pay_df[pay_df['loan_name'] == row['name']]
            total_p = p_history['amount'].sum()
            
            days = (datetime.now().date() - s_dt).days
            interest_calc = (sawa * (byaj_rate/100) / 30) * days
            total_due = (sawa + interest_calc) - total_p
            
            with st.expander(f"👤 {row['name']} - Current Balance: Rs. {total_due:,.2f}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Initial Principal", f"Rs. {sawa:,.0f}")
                col2.metric("Total Interest", f"Rs. {interest_calc:,.0f}")
                col3.metric("Total Paid", f"Rs. {total_p:,.0f}")
                st.write("**Payment Log:**")
                st.table(p_history)
