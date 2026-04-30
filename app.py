import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="Cloud Loan Tracker", layout="wide")
st.title("🏦 My Cloud Loan Ledger")

# 1. CONNECT TO GOOGLE SHEETS
# Yo connection le Streamlit Secrets ma haleko URL aafai khojchha
conn = st.connection("gsheets", type=GSheetsConnection)

# Data tanne function (TTL=0 ko artho: naya data turuntai dekhine)
def load_data():
    try:
        l_df = conn.read(worksheet="loans", ttl="0s")
        p_df = conn.read(worksheet="payments", ttl="0s")
        return l_df.dropna(how='all'), p_df.dropna(how='all')
    except:
        return pd.DataFrame(columns=['name', 'principal', 'rate', 'start_date']), pd.DataFrame(columns=['loan_name', 'amount', 'date'])

loans_df, payments_df = load_data()

# --- SIDEBAR: ADD LOAN ---
st.sidebar.header("➕ New Loan")
n_name = st.sidebar.text_input("Source Name")
n_p = st.sidebar.number_input("Principal (Sawa)", min_value=0.0)
n_r = st.sidebar.number_input("Monthly Rate (%)", value=2.0)
n_d = st.sidebar.date_input("Start Date")

if st.sidebar.button("Save to Google Sheet"):
    if n_name:
        new_row = pd.DataFrame([{"name": n_name, "principal": n_p, "rate": n_r, "start_date": str(n_d)}])
        updated_loans = pd.concat([loans_df, new_row], ignore_index=True)
        conn.update(worksheet="loans", data=updated_loans)
        st.sidebar.success("Cloud ma save bhayo!")
        st.rerun()

# --- MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Portfolio", "🧮 Interest Calculator"])

with tab1:
    st.subheader("Your Active Loans")
    if not loans_df.empty:
        st.dataframe(loans_df, use_container_width=True)
        
        st.divider()
        st.subheader("Record a Payment")
        col1, col2 = st.columns(2)
        with col1:
            sel_l = st.selectbox("Select Loan", loans_df['name'].tolist())
            amt = st.number_input("Amount Paid", min_value=0.0)
        with col2:
            dt = st.date_input("Payment Date")
            if st.button("Save Payment"):
                new_p = pd.DataFrame([{"loan_name": sel_l, "amount": amt, "date": str(dt)}])
                updated_p = pd.concat([payments_df, new_p], ignore_index=True)
                conn.update(worksheet="payments", data=updated_p)
                st.success("Payment recorded in Cloud!")
                st.rerun()
    else:
        st.info("No loans found. Add one from sidebar!")

with tab2:
    st.info("Interest Calculation logic will fetch data from Google Sheets now.")
    # (Timiile paila chalaeko byaj hisab garne logic yahin basxa)
