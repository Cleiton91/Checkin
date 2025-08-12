# FRONT-END (STREAMLIT)

import streamlit as st
import requests
import pandas as pd
import base64
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

#CONEXAO COM BACK
API_URL = os.getenv("API_URL")

#IMAGEM
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

image_path = os.path.join(os.path.dirname(__file__), "image", "aeroporto.jpg")
img_base64 = get_base64_image(image_path)
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
""", unsafe_allow_html=True)

#LOGIN
USUARIO = os.getenv ("LOG_USER")
SENHA = os.getenv ("LOG_PASSWORD")

params = st.query_params
if "auth" not in params or params["auth"][0] != "1":
    st.title("Login")
    user = st.text_input("User")
    password = st.text_input("Password", type="password")
    if st.button("Enter"):
        if user == USUARIO and password == SENHA:
            st.query_params["auth"] = "1"
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.stop()

# FUNÇÃO PARA BUSCAR MÉTRICAS DE REGISTROS E CHECK-IN 
def get_passenger_metrics():
    response = requests.get(API_URL)
    if response.status_code == 200:
        passengers = response.json()
        df = pd.DataFrame(passengers)
        
        # Verificação segura da coluna CHECKIN_STATUS
        if "CHECKIN_STATUS" in df.columns:
            df["CHECKIN_STATUS"] = df["CHECKIN_STATUS"].apply(lambda x: "YES✅" if x == 1 else "NO❌")
            total = len(df)
            checkins = df["CHECKIN_STATUS"].value_counts().get("YES✅", 0)
            return total, checkins
        else:
            # Se a coluna não existir, retorna o total de passageiros e 0 check-ins
            total = len(df)
            return total, 0
    else:
        # Se a requisição falhar
        return 0, 0
    
# MÉTRICAS NO TOPO
total_passengers, checkins_done = get_passenger_metrics()
col1, col2 = st.columns(2)
col1.metric("👥 Passengers Registred ", total_passengers)
col2.metric("🛂 Check-ins Realized", checkins_done)

# TITULO
st.title("Boarding System")



# FORMULÁRIO DE REGISTRO 
with st.form(key='register_form',clear_on_submit=True):
    st.subheader("📋 Register Passenger")
    name = st.text_input("Name")
    flight = st.text_input("Flight")
    origin = st.text_input("Origin")
    destination = st.text_input("Destination")
    seat = st.text_input("Seat")
    submit = st.form_submit_button("Register")
                   

   
    if submit:
        if all([name, flight, origin, destination, seat]):
            #BUSCA PASSAGEIRO
            try:
                response_get = requests.get(API_URL)
                if response_get.status_code == 200:
                    passageiros = response_get.json()
                    nomes_existentes = [p["NAME"].lower() for p in passageiros]

                    #VERIFICA SE JA EXISTE O NOME NA LISTA (ignorando maiúsculas/minúsculas)
                    if name.lower() in nomes_existentes:
                        st.warning("Name already registred!")
                        
                    else:
                        #ENVIA NOVO REGISTRO
                        response_post = requests.post(API_URL, json={
                            "NAME": name,
                            "FLIGHT": flight,
                            "ORIGIN": origin,
                            "DESTINATION": destination,
                            "SEAT": seat
                        })
                        if response_post.status_code == 200:
                            st.success("Passenger registered successfully!")
                           
                        else:
                            st.error(response_post.json().get("detail", "Error registering passenger."))
                else:
                    st.error("Error")
            except Exception as e:
                st.error(f"API connection error: {e}")
        else:
            st.warning("Please fill in all fields.")
           
# LISTAGEM 
st.header("Registered Passengers")

def list_passengers():
    response = requests.get(API_URL)
    if response.status_code == 200:
        passengers = response.json()
        if passengers:
            df = pd.DataFrame(passengers)
            df["CHECKIN_STATUS"] = df["CHECKIN_STATUS"].apply(lambda x: "YES✅" if x == 1 else "NO❌")
            st.dataframe(df)
            return df
        else:
            st.info("No passengers registered yet.")
            return pd.DataFrame()
    else:
        st.error("Error loading passengers.")
        return pd.DataFrame()
    


# LISTA PARA FAZER O CHECK IN
df_passengers = list_passengers()


# CHECK-IN 
if not df_passengers.empty:
    passenger_id =st.selectbox("Select Passenger ID for Check-in", df_passengers["id"])
    if st.button("Do Check-in"):
        response = requests.post(f"{API_URL}/{passenger_id}/checkin")
        if response.status_code == 200:
            st.success("Check-in completed!")
            st.rerun()
        else:
            st.error(response.json().get("detail", "Check-in error."))

