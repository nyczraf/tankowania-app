import io  # Dodaj to na samej górze pliku app.py

# ... (reszta Twojego kodu bez zmian aż do sekcji pobierania) ...

if not df.empty:
    st.dataframe(df.tail(10), use_container_width=True)
    
    # TWORZENIE PLIKU EXCEL W PAMIĘCI
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tankowania')
        # Automatyczne dopasowanie szerokości kolumn w Excelu
        worksheet = writer.sheets['Tankowania']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    
    st.download_button(
        label="📥 POBIERZ RAPORT EXCEL (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"raport_tankowania_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# KONFIGURACJA STRONY
st.set_page_config(page_title="Rejestr Tankowania", layout="centered", page_icon="⛽")

# Nazwa pliku z bazą danych na serwerze
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

# LOGIKA LINKU DLA TATY (?user=Tata_Oskara)
query_params = st.query_params
default_name = query_params.get("user", "").replace("_", " ")

st.title("⛽ Rejestr Tankowania")

# Pobieranie ostatniego przebiegu dla podpowiedzi i walidacji
last_mileage = 0
if not df.empty:
    try:
        last_mileage = int(df["Przebieg"].max())
    except:
        last_mileage = 0

# FORMULARZ WPISYWANIA DANYCH
with st.form("fuel_form", clear_on_submit=True):
    st.subheader("Dodaj nowe tankowanie")
    
    driver_name = st.text_input("Kierowca", value=default_name)
    
    col1, col2 = st.columns(2)
    with col1:
        fuel_date = st.date_input("Data", date.today())
        liters = st.number_input("Ilość litrów", min_value=0.0, step=0.01)
    with col2:
        payment_method = st.selectbox("Płatność", ["Tankpol", "DKV", "Andamur"])
        # Podpowiadamy ostatni przebieg w nawiasie
        mileage = st.number_input(f"Przebieg (Ostatnio: {last_mileage} km)", min_value=0, step=1)
    
    submit = st.form_submit_button("ZAPISZ W BAZIE")

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
        
        # Łączymy nowe dane ze starymi
        df = pd.concat([df, new_row], ignore_index=True)
        # Zapisujemy do pliku .csv na dysku serwera
        df.to_csv(DB_FILE, index=False)
        
        st.success(f"Pomyślnie zapisano tankowanie dla: {driver_name}")
        st.balloons()
        st.rerun()
    elif mileage <= last_mileage and mileage != 0:
        st.error(f"BŁĄD: Przebieg nie może być mniejszy lub równy poprzedniemu ({last_mileage} km)!")
    else:
        st.warning("Proszę poprawnie wypełnić wszystkie pola.")

# PODGLĄD I EKSPORT DANYCH
st.divider()
st.subheader("📋 Historia wpisów")

if not df.empty:
    st.dataframe(df.tail(10), use_container_width=True)
    
    # Przycisk pobierania bazy
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 POBIERZ CAŁĄ BAZĘ (PLIK EXCEL/CSV)",
        data=csv_data,
        file_name=f"raport_tankowania_{date.today()}.csv",
        mime="text/csv",
        help="Kliknij, aby zapisać kopię wszystkich wpisów na swoim urządzeniu."
    )
else:
    st.info("Baza danych jest jeszcze pusta. Dodaj pierwszy wpis!")

# OPCJA CZYSZCZENIA (UKRYTA)
with st.expander("🗑️ Zarządzanie plikiem"):
    if st.button("USUŃ OSTATNI WPIS"):
        if not df.empty:
            df = df[:-1]
            df.to_csv(DB_FILE, index=False)
            st.warning("Usunięto ostatni wiersz.")
            st.rerun()


