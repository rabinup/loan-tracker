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
st.title("🏦 Personal Loan Ledger (Offline + Backup)")

# --- FUNCTIONS ---
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

# --- SIDEBAR: BACKUP & RESTORE ---
st.sidebar.header("⚙️ Backup & Recovery")
# Download Button
if st.sidebar.button("Prepare Backup File"):
    loans = get_loans()
    payments = get_payments()
    with pd.ExcelWriter("loan_backup.xlsx") as writer:
        loans.to_excel(writer, sheet_name="loans", index=False)
        payments.to_excel(writer, sheet_name="payments", index=False)
    
    with open("loan_backup.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Excel Backup", f, file_name="loan_backup.xlsx")

# Restore (Upload) Button
uploaded_file = st.sidebar.file_uploader("📂 Restore from Backup", type="xlsx")
if uploaded_file and st.sidebar.button("Restore Now"):
    l_up = pd.read_excel(uploaded_file, sheet_name="loans")
    p_up = pd.read_excel(uploaded_file, sheet_name="payments")
    conn = sqlite3.connect(DB_FILE)
    l_up.to_sql("loans", conn, if_exists="replace", index=False)
    p_up.to_sql("payments", conn, if_exists="replace", index=False)
    conn.close()
    st.sidebar.success("Data Restored!")
    st.rerun()

# --- MAIN UI ---
tab1, tab2, tab3 = st.tabs(["➕ Add New", "💸 Payments", "📊 Reports"])

with tab1:
    st.subheader("Add New Loan")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name (e.g. Sujata)")
        principal = st.number_input("Principal Amount", min_value=0.0)
    with col2:
        rate = st.number_input("Monthly Interest (%)", value=2.0)
        date = st.date_input("Start Date", value=datetime.now())
    
    if st.button("Save Loan"):
        if name:
            add_loan(name, principal, rate, date)
            st.success(f"Loan for {name} saved!")
            st.rerun()

with tab2:
    st.subheader("Record Payment")
    loans_df = get_loans()
    if not loans_df.empty:
        l_list = loans_df['name'].tolist()
        sel_loan = st.selectbox("Select Person", l_list)
        p_amt = st.number_input("Payment Amount", min_value=0.0)
        p_date = st.date_input("Payment Date")
        if st.button("Save Payment"):
            add_payment(sel_loan, p_amt, p_date)
            st.success("Payment recorded!")
            st.rerun()
    else:
        st.info("Paila Loan thapnu hola.")

with tab3:
    st.subheader("Live Balance Status")
    loans_df = get_loans()
    pay_df = get_payments()
    
    if not loans_df.empty:
        for index, row in loans_df.iterrows():
            # Interest Calculation Logic
            sawa = row['principal']
            r = row['rate']
            start_dt = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
            
            # Filter payments for this person
            person_pays = pay_df[pay_df['loan_name'] == row['name']]
            
            # Simple Interest Calculation till today
            days = (datetime.now().date() - start_dt).days
            total_interest = (sawa * (r/100) / 30) * days
            total_paid = person_pays['amount'].sum()
            total_due = (sawa + total_interest) - total_paid
            
            with st.expander(f"👤 {row['name']} Details"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Principal", f"Rs. {sawa:,.0f}")
                c2.metric("Total Interest", f"Rs. {total_interest:,.0f}")
                c3.metric("Baki Amount", f"Rs. {total_due:,.0f}")
                st.write("**Payment History:**")
                st.dataframe(person_pays, use_container_width=True)
