import streamlit as st
import pandas as pd
from datetime import date
import io
import requests

st.set_page_config(page_title="Rejestr Tankowania", layout="centered", page_icon="⛽")

# --- KONFIGURACJA ---
# Upewnij się, że link jest w cudzysłowie!
URL = "https://docs.google.com/spreadsheets/d/1pEuOX5WoOhv-JMwzvmHPcMbMttEaK5Vsc8-mgja569o/edit?usp=sharing"

# Funkcja do konwersji linku arkusza na link do pobierania CSV
def get_csv_url(gsheet_url):
    return gsheet_url.replace('/edit?gid=', '/export?format=csv&gid=').split('#')[0]

def load_data():
    try:
        csv_url = get_csv_url(URL)
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])

# --- LOGIKA ---
df = load_data()
query_params = st.query_params
default_name = query_params.get("user", "").replace("_", " ")

st.title("⛽ Rejestr Tankowania")

last_mileage = 0
if not df.empty and "Przebieg" in df.columns:
    try:
        last_mileage = int(df["Przebieg"].max())
    except:
        last_mileage = 0

with st.form("fuel_form", clear_on_submit=True):
    driver_name = st.text_input("Kierowca", value=default_name)
    col1, col2 = st.columns(2)
    with col1:
        fuel_date = st.date_input("Data", date.today())
        liters = st.number_input("Ilość litrów", min_value=0.0, step=0.01)
    with col2:
        payment_method = st.selectbox("Płatność", ["Tankpol", "DKV", "Andamur"])
        mileage = st.number_input(f"Przebieg (Ostatnio: {last_mileage})", min_value=0, step=1)
    
    submit = st.form_submit_button("ZAPISZ DANE")

# UWAGA: Streamlit Community Cloud ma ograniczenia w zapisywaniu do GSheets 
# przez bibliotekę st-gsheets bez pliku .streamlit/secrets.toml.
# Jeśli nadal masz błąd, najbezpieczniej jest użyć st.download_button 
# lub połączyć się przez oficjalne Google Service Account.

if submit:
    if driver_name and liters > 0 and mileage > last_mileage:
        # Tutaj następuje próba zapisu
        # Jeśli st-gsheets-connection nadal stawia opór, 
        # wyświetlimy komunikat o konfiguracji Secrets.
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            new_entry = pd.DataFrame([{
                "Kierowca": driver_name,
                "Data": str(fuel_date),
                "Litry": liters,
                "Płatność": payment_method,
                "Przebieg": mileage
            }])
            
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(spreadsheet=URL, data=updated_df)
            st.success("Zapisano w Google Sheets!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error("Błąd zapisu. Prawdopodobnie musisz dodać dane logowania do 'Secrets' w Streamlit Cloud.")
            st.info("Aby naprawić to na stałe, wejdź w 'Manage App' -> 'Settings' -> 'Secrets' i wklej tam dane dostępowe Google.")

st.divider()
st.dataframe(df.tail(10), use_container_width=True)
