import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Safe Cloud Tracker", layout="wide")
st.title("🏦 My Auto-Save Loan Ledger")

# 1. Connect to GSheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Reading Data (TTL=0 ensures we always get the latest data)
def load_data():
    try:
        # Note: 'loans' and 'payments' must be your sheet names
        l_df = conn.read(worksheet="loans", ttl="0s")
        p_df = conn.read(worksheet="payments", ttl="0s")
        return l_df.dropna(how='all'), p_df.dropna(how='all')
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame(columns=['name', 'principal', 'rate', 'start_date']), pd.DataFrame(columns=['loan_name', 'amount', 'date'])

loans_df, payments_df = load_data()

# --- SIDEBAR: ADD LOAN ---
st.sidebar.header("➕ Naya Loan")
n_name = st.sidebar.text_input("Source Name")
n_p = st.sidebar.number_input("Principal", min_value=0.0)
n_r = st.sidebar.number_input("Rate (%)", value=1.5)
n_d = st.sidebar.date_input("Start Date")

if st.sidebar.button("Cloud ma Save Garne"):
    if n_name:
        new_row = pd.DataFrame([{"name": n_name, "principal": n_p, "rate": n_r, "start_date": str(n_d)}])
        updated_loans = pd.concat([loans_df, new_row], ignore_index=True)
        # We use clear_cache=True to fix the Error in image_c5f4a1.png
        conn.update(worksheet="loans", data=updated_loans)
        st.sidebar.success("Sheet ma save bhayo!")
        st.rerun()

# --- MAIN DASHBOARD ---
st.info("Aba yahan bata entry gareko sabai data aafai Google Sheet ma janchha.")
st.dataframe(loans_df, use_container_width=True)
