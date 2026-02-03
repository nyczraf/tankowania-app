import streamlit as st
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="Rejestr Tankowania", layout="centered")

DB_FILE = "historia_tankowan.csv"
PASSWORD_CLEAR = "Botam"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])

df = load_data()

st.title("⛽ Rejestr Tankowania")

# Zapamiętywanie kierowcy w sesji
if "driver" not in st.session_state:
    st.session_state.driver = ""

with st.form("fuel_form", clear_on_submit=False):
    driver_name = st.text_input("Imię i Nazwisko", value=st.session_state.driver)
    fuel_date = st.date_input("Data tankowania", date.today())
    liters = st.number_input("Ilość litrów", min_value=0.0, step=0.01)
    payment_method = st.selectbox("Forma płatności", ["Tankpol", "DKV", "Andamur"])
    mileage = st.number_input("Przebieg (km)", min_value=0, step=1)
    
    if st.form_submit_button("ZAPISZ DANE"):
        if driver_name and liters > 0:
            new_entry = pd.DataFrame([[driver_name, fuel_date, liters, payment_method, mileage]], 
                                    columns=df.columns)
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.session_state.driver = driver_name
            st.success("Zapisano!")
            st.rerun()

st.divider()
st.subheader("📋 Historia")
st.dataframe(df.tail(5), use_container_width=True)

if not df.empty:
    df.to_excel("raport.xlsx", index=False)
    with open("raport.xlsx", "rb") as f:
        st.download_button("📥 Pobierz Excel", f, "tankowania.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with st.expander("🗑️ Usuwanie"):
    pwd = st.text_input("Hasło", type="password")
    if st.button("KASUJ WSZYSTKO"):
        if pwd == PASSWORD_CLEAR:
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()