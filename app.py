import streamlit as st
import pandas as pd
from datetime import date
import os
import io

# KONFIGURACJA STRONY
st.set_page_config(page_title="Rejestr Tankowania", layout="centered", page_icon="⛽")

DB_FILE = "baza_tankowania.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])
    else:
        return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])

df = load_data()

# LOGIKA LINKU DLA KIEROWCY
query_params = st.query_params
user_param = query_params.get("user", "")
default_name = user_param.replace("_", " ")

st.title("⛽ Rejestr Tankowania")

# Pobieranie ostatniego przebiegu
last_mileage = 0
if not df.empty:
    try:
        last_mileage = int(df["Przebieg"].max())
    except:
        last_mileage = 0

# FORMULARZ
with st.form("fuel_form", clear_on_submit=True):
    st.subheader("Dodaj nowe tankowanie")
    driver_name = st.text_input("Imię i Nazwisko", value=default_name)
    
    col1, col2 = st.columns(2)
    with col1:
        fuel_date = st.date_input("Data tankowania", date.today())
        liters = st.number_input("Ilość litrów", min_value=0.0, step=0.01)
    with col2:
        payment_method = st.selectbox("Forma płatności", ["Tankpol", "DKV", "Andamur"])
        mileage = st.number_input(f"Przebieg (Ostatnio: {last_mileage} km)", min_value=0, step=1)
    
    submit = st.form_submit_button("ZAPISZ DANE")

if submit:
    if driver_name and liters > 0 and mileage > last_mileage:
        new_row = pd.DataFrame([{
            "Kierowca": driver_name, "Data": str(fuel_date),
            "Litry": liters, "Płatność": payment_method, "Przebieg": mileage
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success(f"Zapisano dane dla: {driver_name}")
        st.balloons()
        st.rerun()
    elif mileage <= last_mileage and mileage != 0:
        st.error(f"BŁĄD: Nowy przebieg musi być większy niż {last_mileage} km!")
    else:
        st.warning("Uzupełnij wszystkie pola.")

# --- SEKCJA HISTORII (PERSONALIZOWANA) ---
st.divider()
if default_name:
    st.subheader(f"📋 Twoja historia ({default_name})")
    # Filtrujemy dane tylko dla konkretnego kierowcy
    user_df = df[df["Kierowca"] == default_name]
    st.dataframe(user_df.tail(10), use_container_width=True)
else:
    st.subheader("📋 Pełna historia (Widok Administratora)")
    st.dataframe(df.tail(10), use_container_width=True)

# --- EKSPORT DO EXCELA (Zawsze cała baza dla Ciebie) ---
if not df.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tankowania')
        worksheet = writer.sheets['Tankowania']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    
    st.download_button(
        label="📥 POBIERZ PEŁNY RAPORT EXCEL",
        data=output.getvalue(),
        file_name=f"raport_paliwowy_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- ZABEZPIECZONE ZARZĄDZANIE ---
st.divider()
with st.expander("🔐 Administracja (Wymaga hasła)"):
    password = st.text_input("Podaj hasło administratora", type="password")
    if password == "Botam":
        st.warning("Uwaga: Jesteś w trybie edycji bazy danych.")
        if st.button("USUŃ OSTATNI WPIS"):
            if not df.empty:
                df = df[:-1]
                df.to_csv(DB_FILE, index=False)
                st.success("Ostatni wpis został usunięty.")
                st.rerun()
        
        if st.button("WYCZYŚĆ CAŁĄ BAZĘ"):
            if st.checkbox("Tak, chcę trwale usunąć wszystkie dane"):
                df = pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])
                df.to_csv(DB_FILE, index=False)
                st.success("Baza została wyczyszczona.")
                st.rerun()
    elif password != "":
        st.error("Błędne hasło!")
