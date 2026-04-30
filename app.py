import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Cloud Loan Ledger", layout="wide")
st.title("🏦 My Final Loan Tracker")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        l_df = conn.read(worksheet="loans", ttl="0s")
        p_df = conn.read(worksheet="payments", ttl="0s")
        return l_df.dropna(how='all'), p_df.dropna(how='all')
    except:
        return pd.DataFrame(columns=['name', 'principal', 'rate', 'start_date']), pd.DataFrame(columns=['loan_name', 'amount', 'date'])

loans_df, payments_df = load_data()

# --- SIDEBAR ---
st.sidebar.header("➕ Setup")
n_name = st.sidebar.text_input("Loan Source")
n_p = st.sidebar.number_input("Principal", min_value=0.0)
n_r = st.sidebar.number_input("Rate (%)", value=2.0)
n_d = st.sidebar.date_input("Start Date")

if st.sidebar.button("Save to Cloud"):
    if n_name:
        new_row = pd.DataFrame([{"name": n_name, "principal": n_p, "rate": n_r, "start_date": str(n_d)}])
        updated_loans = pd.concat([loans_df, new_row], ignore_index=True)
        conn.update(worksheet="loans", data=updated_loans)
        st.sidebar.success("Done!")
        st.rerun()

# --- TABS ---
tab1, tab2 = st.tabs(["📊 Portfolio & Payments", "🧮 Live Interest Meter"])

with tab1:
    if not loans_df.empty:
        st.subheader("Your Loans")
        st.dataframe(loans_df, use_container_width=True)
        
        st.divider()
        st.subheader("Add Payment")
        c1, c2 = st.columns(2)
        with c1:
            sel_l = st.selectbox("Select Loan", loans_df['name'].tolist())
            amt = st.number_input("Amount Paid", min_value=0.0)
        with c2:
            dt = st.date_input("Payment Date")
            if st.button("Submit Payment"):
                new_p = pd.DataFrame([{"loan_name": sel_l, "amount": amt, "date": str(dt)}])
                updated_p = pd.concat([payments_df, new_p], ignore_index=True)
                conn.update(worksheet="payments", data=updated_p)
                st.success("Payment Synced!")
                st.rerun()
    else:
        st.info("No data yet.")

with tab2:
    if not loans_df.empty:
        target = st.selectbox("Check Live Interest", loans_df['name'].tolist())
        
        # Calculation Logic
        l_info = loans_df[loans_df['name'] == target].iloc[0]
        p_info = payments_df[payments_df['loan_name'] == target]
        
        sawa = float(l_info['principal'])
        rate = float(l_info['rate'])
        start_dt = datetime.strptime(str(l_info['start_date']), '%Y-%m-%d').date()
        today = datetime.now().date()
        
        daily_rate = (rate / 100) / 30
        current_sawa = sawa
        total_int = 0
        last_date = start_dt
        
        # Calculate through payments
        for _, row in p_info.sort_values('date').iterrows():
            curr_p_date = datetime.strptime(str(row['date']), '%Y-%m-%d').date()
            days = (curr_p_date - last_date).days
            total_int += current_sawa * daily_rate * max(0, days)
            current_sawa -= float(row['amount'])
            last_date = curr_p_date
            
        # Till Today
        days_today = (today - last_date).days
        total_int += current_sawa * daily_rate * max(0, days_today)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Baki Sawa", f"Rs. {current_sawa:,.2f}")
        m2.metric("Interest Till Today", f"Rs. {total_int:,.2f}")
        m3.metric("Total Payable", f"Rs. {current_sawa + total_int:,.2f}")
