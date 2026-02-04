import streamlit as st
import pandas as pd
from datetime import date
import os
import io

st.set_page_config(page_title="Rejestr Tankowania", layout="centered", page_icon="⛽")

DB_FILE = "baza_tankowania.csv"

def load_data():
    columns = ["Kierowca", "Auto", "Data", "Litry", "Płatność", "Przebieg"]
    if os.path.exists(DB_FILE):
        try:
            temp_df = pd.read_csv(DB_FILE)
            # Zabezpieczenie: jeśli brakuje kolumny 'Auto' w starym pliku, dodaj ją
            for col in columns:
                if col not in temp_df.columns:
                    temp_df[col] = ""
            return temp_df[columns] # Ustawienie poprawnej kolejności
        except:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

df = load_data()

# --- LOGIKA LINKU ---
# W nowszych wersjach Streamlit używamy st.query_params bezpośrednio
q_params = st.query_params
user_param = q_params.get("user", "")
car_param = q_params.get("car", "")

default_name = user_param.replace("_", " ")
default_car = car_param.replace("_", " ").upper()

st.title("⛽ Rejestr Tankowania")

# FORMULARZ
with st.form("fuel_form", clear_on_submit=True):
    st.subheader("Nowy wpis")
    
    col_k, col_a = st.columns(2)
    with col_k:
        driver_name = st.text_input("Imię i Nazwisko", value=default_name)
    with col_a:
        vehicle = st.text_input("Numer rejestracyjny auta", value=default_car)

    # Obliczamy ostatni przebieg DLA TEGO KONKRETNEGO AUTA
    last_mileage_vehicle = 0
    if vehicle and not df.empty:
        # Upewniamy się, że szukamy w kolumnie 'Auto'
        vehicle_history = df[df["Auto"].astype(str).str.upper() == vehicle.upper()]
        if not vehicle_history.empty:
            try:
                last_mileage_vehicle = int(pd.to_numeric(vehicle_history["Przebieg"]).max())
            except:
                last_mileage_vehicle = 0

    col1, col2 = st.columns(2)
    with col1:
        fuel_date = st.date_input("Data tankowania", date.today())
        liters = st.number_input("Ilość litrów", min_value=0.0, step=0.01)
    with col2:
        payment_method = st.selectbox("Forma płatności", ["Tankpol", "DKV", "Andamur"])
        mileage = st.number_input(f"Przebieg (Ostatnio w {vehicle}: {last_mileage_vehicle} km)", min_value=0, step=1)
    
    submit = st.form_submit_button("ZAPISZ DANE")

# OBSŁUGA ZAPISU
if submit:
    if driver_name and vehicle and liters > 0 and mileage > last_mileage_vehicle:
        new_row = pd.DataFrame([{
            "Kierowca": driver_name, 
            "Auto": vehicle.upper(), 
            "Data": str(fuel_date),
            "Litry": liters, 
            "Płatność": payment_method, 
            "Przebieg": mileage
        }])
        
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        
        st.success(f"Zapisano tankowanie dla auta {vehicle.upper()}")
        st.balloons()
        st.rerun()
    elif vehicle and mileage <= last_mileage_vehicle:
        st.error(f"BŁĄD: Przebieg musi być wyższy niż {last_mileage_vehicle} km!")
    else:
        st.warning("Uzupełnij wszystkie pola.")

# --- HISTORIA OSOBISTA ---
st.divider()
if default_name:
    st.subheader(f"📋 Twoja historia ({default_name})")
    user_df = df[df["Kierowca"] == default_name]
    st.dataframe(user_df.tail(10), use_container_width=True)
else:
    st.subheader("📋 Pełna historia (Widok Administratora)")
    st.dataframe(df.tail(15), use_container_width=True)

# --- EKSPORT EXCEL ---
if not df.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tankowania')
    
    st.download_button(
        label="📥 POBIERZ RAPORT EXCEL",
        data=output.getvalue(),
        file_name=f"raport_paliwowy_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- ADMINISTRACJA ---
st.divider()
with st.expander("🔐 Administracja"):
    password = st.text_input("Podaj hasło", type="password")
    if password == "Botam":
        if st.button("USUŃ OSTATNI WPIS"):
            if not df.empty:
                df = df[:-1]
                df.to_csv(DB_FILE, index=False)
                st.rerun()
        if st.button("RESTART BAZY (KASUJE WSZYSTKO)"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.rerun()
