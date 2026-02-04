import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Logistyka Paliwowa", layout="centered", page_icon="⛽")

# --- KONFIGURACJA ---
URL = "https://docs.google.com/spreadsheets/d/1pEuOX5WoOhv-JMwzvmHPcMbMttEaK5Vsc8-mgja569o/edit?gid=845295439#gid=845295439"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(spreadsheet=URL)
    except:
        return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])

# Pobieramy dane na starcie
df = load_data()

# --- LOGIKA LINKU (?user=Imię_Nazwisko) ---
query_params = st.query_params
default_name = query_params.get("user", "").replace("_", " ")

st.title("⛽ Rejestr Tankowania")

# Wyciągamy ostatni przebieg dla podpowiedzi
last_mileage = 0
try:
    if not df.empty and "Przebieg" in df.columns:
        # Pobieramy ostatnią wartość z kolumny Przebieg
        last_val = df["Przebieg"].iloc[-1]
        # Sprawdzamy czy to na pewno liczba
        last_mileage = int(last_val) if pd.notnull(last_val) else 0
except Exception:
    last_mileage = 0

with st.form("fuel_form", clear_on_submit=True):
    st.subheader("Nowy wpis")
    
    driver_name = st.text_input("Kierowca", value=default_name)
    
    col1, col2 = st.columns(2)
    with col1:
        fuel_date = st.date_input("Data", date.today())
        liters = st.number_input("Ilość litrów", min_value=0.0, step=0.01)
    with col2:
        payment_method = st.selectbox("Forma płatności", ["Tankpol", "DKV", "Andamur"])
        # Podpowiadamy ostatni przebieg pod polem
        mileage = st.number_input(f"Przebieg (Ostatnio: {last_mileage} km)", min_value=0, step=1)
    
    submit = st.form_submit_button("ZAPISZ DANE")

if submit:
    if driver_name and liters > 0 and mileage > last_mileage:
        new_entry = pd.DataFrame([{
            "Kierowca": driver_name,
            "Data": str(fuel_date),
            "Litry": liters,
            "Płatność": payment_method,
            "Przebieg": mileage
        }])
        
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_df)
        
        st.success("Zapisano pomyślnie!")
        st.balloons()
        st.rerun()
    elif mileage <= last_mileage and mileage != 0:
        st.warning(f"Uwaga: Wpisany przebieg ({mileage}) jest mniejszy lub równy poprzedniemu ({last_mileage})!")
    else:
        st.error("Uzupełnij poprawnie wszystkie pola.")

# --- HISTORIA I ADMINISTRACJA ---
st.divider()
st.subheader("📋 Historia ostatnich tankowań")
st.dataframe(df.tail(10), use_container_width=True)

with st.expander("🔐 Administracja (Kasowanie)"):
    pwd = st.text_input("Hasło", type="password")
    if st.button("WYCZYŚĆ WSZYSTKO"):
        if pwd == "Botam":
            empty_df = pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])
            conn.update(spreadsheet=URL, data=empty_df)
            st.success("Historia została wykasowana.")
            st.rerun()
        else:
            st.error("Błędne hasło!")







