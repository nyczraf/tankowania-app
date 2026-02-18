import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Logistyka Trasy", layout="centered", page_icon="🚚")

# --- KONFIGURACJA POŁĄCZENIA ---
# Upewnij się, że w Secrets masz zdefiniowane połączenie gsheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(ttl="0") # ttl=0 wymusza odświeżenie danych za każdym razem
    except:
        return pd.DataFrame(columns=["Kierowca", "Auto", "Data", "Litry", "Płatność", "Start Trasy", "Koniec Trasy"])

df = load_data()

# --- LOGIKA LINKÓW ---
q = st.query_params
default_name = q.get("user", "").replace("_", " ")
default_car = q.get("car", "").upper()

st.title("🚚 Rejestr Trasy i Tankowania")

with st.form("main_form", clear_on_submit=True):
    st.subheader("Wprowadź dane z trasy")
    
    c1, c2 = st.columns(2)
    with c1:
        driver = st.text_input("Kierowca", value=default_name)
        vehicle = st.text_input("Numer rejestracyjny", value=default_car)
    with c2:
        log_date = st.date_input("Data", date.today())
        payment = st.selectbox("Forma płatności", ["Tankpol", "DKV", "Andamur", "Inna"])

    st.divider()
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        start_mileage = st.number_input("Start trasy (km)", min_value=0, step=1)
    with col_b:
        end_mileage = st.number_input("Koniec trasy (km)", min_value=0, step=1)
    with col_c:
        liters = st.number_input("Zatankowano (litry)", min_value=0.0, step=0.01)

    submit = st.form_submit_button("ZAPISZ DANE W ARKUSZU")

if submit:
    if driver and vehicle and end_mileage >= start_mileage:
        try:
            new_data = pd.DataFrame([{
                "Kierowca": driver,
                "Auto": vehicle.upper(),
                "Data": str(log_date),
                "Litry": liters,
                "Płatność": payment,
                "Start Trasy": start_mileage,
                "Koniec Trasy": end_mileage
            }])
            
            # Pobieramy świeże dane, łączymy i wysyłamy
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("Dane zapisane trwale w Arkuszach Google!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Błąd połączenia z bazą: {e}")
            st.info("Upewnij się, że skonfigurowałeś 'Secrets' w panelu Streamlit.")
    else:
        st.error("Błąd: Przebieg końcowy musi być większy lub równy początkowemu!")

# --- WIDOK DLA KIEROWCY ---
st.divider()
if default_name:
    st.subheader(f"Twoje ostatnie wpisy")
    st.dataframe(df[df["Kierowca"] == default_name].tail(5), use_container_width=True)

# --- ADMINISTRACJA ---
with st.expander("🔐 Administracja (Hasło: Botam)"):
    pass_input = st.text_input("Hasło", type="password")
    if pass_input == "Botam":
        if st.button("USUŃ OSTATNI WPIS"):
            df = df[:-1]
            conn.update(data=df)
            st.rerun()
