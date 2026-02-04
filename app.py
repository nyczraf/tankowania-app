import streamlit as st
import pandas as pd
from datetime import date
import os
import io

st.set_page_config(page_title="Rejestr Tankowania", layout="centered", page_icon="⛽")

DB_FILE = "baza_tankowania.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame(columns=["Kierowca", "Auto", "Data", "Litry", "Płatność", "Przebieg"])
    else:
        return pd.DataFrame(columns=["Kierowca", "Auto", "Data", "Litry", "Płatność", "Przebieg"])

df = load_data()

# LOGIKA LINKU
query_params = st.query_params
user_param = query_params.get("user", "")
default_name = user_param.replace("_", " ")

st.title("⛽ Rejestr Tankowania")

# FORMULARZ
with st.form("fuel_form", clear_on_submit=True):
    st.subheader("Nowy wpis")
    
    col_k, col_a = st.columns(2)
    with col_k:
        driver_name = st.text_input("Imię i Nazwisko", value=default_name)
    with col_a:
        # Możesz tu wpisać listę aut na stałe, np. ["Auto 1", "Auto 2"] lub zostawić text_input
        vehicle = st.text_input("Numer rejestracyjny auta")

    # Obliczamy ostatni przebieg DLA TEGO AUTA (dynamicznie po wpisaniu numeru)
    last_mileage_vehicle = 0
    if vehicle and not df.empty:
        vehicle_history = df[df["Auto"].str.upper() == vehicle.upper()]
        if not vehicle_history.empty:
            last_mileage_vehicle = int(vehicle_history["Przebieg"].max())

    col1, col2 = st.columns(2)
    with col1:
        fuel_date = st.date_input("Data", date.today())
        liters = st.number_input("Litry", min_value=0.0, step=0.01)
    with col2:
        payment_method = st.selectbox("Płatność", ["Tankpol", "DKV", "Andamur"])
        mileage = st.number_input(f"Przebieg (Ostatnio w tym aucie: {last_mileage_vehicle} km)", min_value=0, step=1)
    
    submit = st.form_submit_button("ZAPISZ DANE")

if submit:
    if driver_name and vehicle and liters > 0 and mileage > last_mileage_vehicle:
        new_row = pd.DataFrame([{
            "Kierowca": driver_name, "Auto": vehicle.upper(), "Data": str(fuel_date),
            "Litry": liters, "Płatność": payment_method, "Przebieg": mileage
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success(f"Zapisano tankowanie auta {vehicle.upper()}")
        st.balloons()
        st.rerun()
    elif vehicle and mileage <= last_mileage_vehicle:
        st.error(f"BŁĄD: Przebieg dla auta {vehicle.upper()} musi być wyższy niż {last_mileage_vehicle} km!")
    else:
        st.warning("Uzupełnij wszystkie dane (Imię, Auto, Litry, Przebieg).")

# --- HISTORIA OSOBISTA ---
st.divider()
if default_name:
    st.subheader(f"📋 Twoja historia ({default_name})")
    user_df = df[df["Kierowca"] == default_name]
    st.dataframe(user_df.tail(10), use_container_width=True)
else:
    st.subheader("📋 Pełna historia (Widok Admina)")
    st.dataframe(df.tail(15), use_container_width=True)

# --- EXCEL ---
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

# --- HASŁO BOTAM ---
st.divider()
with st.expander("🔐 Administracja"):
    password = st.text_input("Hasło", type="password")
    if password == "Botam":
        if st.button("USUŃ OSTATNI WPIS"):
            if not df.empty:
                df = df[:-1]
                df.to_csv(DB_FILE, index=False)
                st.success("Usunięto.")
                st.rerun()
