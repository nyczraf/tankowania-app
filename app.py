import streamlit as st
import pandas as pd
from datetime import date
import os
import io

# KONFIGURACJA STRONY
st.set_page_config(page_title="Rejestr Tankowania", layout="centered", page_icon="⛽")

# Nazwa pliku bazy danych na serwerze
DB_FILE = "baza_tankowania.csv"

# FUNKCJA ŁADOWANIA DANYCH
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])
    else:
        return pd.DataFrame(columns=["Kierowca", "Data", "Litry", "Płatność", "Przebieg"])

# Załadowanie aktualnej bazy
df = load_data()

# LOGIKA LINKU DLA KIEROWCY (?user=Tata_Oskara)
query_params = st.query_params
default_name = query_params.get("user", "").replace("_", " ")

st.title("⛽ Rejestr Tankowania")

# Pobieranie ostatniego przebiegu (podpowiedź i walidacja)
last_mileage = 0
if not df.empty:
    try:
        last_mileage = int(df["Przebieg"].max())
    except:
        last_mileage = 0

# FORMULARZ WPISYWANIA DANYCH
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

# OBSŁUGA ZAPISU
if submit:
    if driver_name and liters > 0 and mileage > last_mileage:
        new_row = pd.DataFrame([{
            "Kierowca": driver_name,
            "Data": str(fuel_date),
            "Litry": liters,
            "Płatność": payment_method,
            "Przebieg": mileage
        }])
        
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        
        st.success(f"Dziękujemy {driver_name}! Dane zostały zapisane.")
        st.balloons()
        st.rerun()
    elif mileage <= last_mileage and mileage != 0:
        st.error(f"BŁĄD: Nowy przebieg musi być większy niż poprzedni ({last_mileage} km)!")
    else:
        st.warning("Uzupełnij poprawnie wszystkie pola formularza.")

# SEKCJA PODGLĄDU I EKSPORTU
st.divider()
st.subheader("📋 Historia ostatnich wpisów")

if not df.empty:
    # Wyświetlanie tabeli (ostatnie 10 wpisów)
    st.dataframe(df.tail(10), use_container_width=True)
    
    # GENEROWANIE PLIKU EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Arkusz1')
        # Formatowanie - automatyczna szerokość kolumn
        worksheet = writer.sheets['Arkusz1']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    
    st.download_button(
        label="📥 POBIERZ RAPORT EXCEL (.xlsx)",
        data=output.getvalue(),
        file_name=f"raport_paliwowy_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Baza danych jest pusta. Czekamy na pierwszy wpis!")

# OPCJE DODATKOWE
with st.expander("🛠️ Zarządzanie"):
    st.write("W razie pomyłki możesz usunąć ostatnio dodany wiersz:")
    if st.button("USUŃ OSTATNI WPIS"):
        if not df.empty:
            df = df[:-1]
            df.to_csv(DB_FILE, index=False)
            st.warning("Ostatni wpis został usunięty.")
            st.rerun()
