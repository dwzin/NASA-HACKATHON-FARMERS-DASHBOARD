import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from datetime import datetime

# Adicione o estilo CSS
st.markdown("""
    <style>
    /* Configuração geral do fundo */
    .stApp {
        background-color: #f0fff0;
    }

    /* Estilo do título */
    h1 {
        color: #228B22;
        font-family: 'Helvetica', sans-serif;
        text-align: center;
        font-weight: bold;
        font-size: 3em;
    }

    /* Estilo das caixas de texto, input e botão */
    .css-1cpxqw2 {
        background-color: #e6ffe6;
        color: #006400;
        border: 1px solid #228B22;
        border-radius: 10px;
        font-family: 'Arial', sans-serif;
        padding: 8px;
    }

    /* Estilo dos botões */
    .stButton > button {
        background-color: #228B22;
        color: white;
        border-radius: 10px;
        font-size: 1.2em;
        font-weight: bold;
        padding: 10px 20px;
    }

    /* Estilo dos advisories */
    .stMarkdown h2 {
        color: #006400;
        font-family: 'Helvetica', sans-serif;
        font-size: 1.8em;
    }

    .stMarkdown p {
        color: #006400;
        font-size: 1.1em;
    }

    /* Estilo do rodapé e subtítulos */
    h2 {
        color: #006400;
        font-family: 'Arial', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# Função para a landing page
def landing_page():
    st.title("Welcome to the Farmers' Weather Dashboard")
    st.write("""
        Optimize your farming operations with real-time weather data.
        Our tool provides key insights on temperature, humidity, solar radiation, and more,
        enabling better decision-making for your crops and land.
    """)

    if st.button("Go to Dashboard"):
        # Atualiza o estado para o dashboard
        st.session_state['page'] = 'dashboard'

# Função para o dashboard
def dashboard():
    st.title("Farmers' Weather Dashboard with Interactive Map")
    st.write("Retrieve and display multiple weather parameters from NASA POWER API to help farmers optimize their operations.")

    # Inicializa o geolocalizador
    geolocator = Nominatim(user_agent="farmers_weather_app")

    # Caixa de busca para o usuário encontrar uma localização   
    location_input = st.text_input("Search for a location (e.g., Rio de Janeiro)")

    # Coordenadas padrão (e.g., Rio de Janeiro)
    latitude = -22.9
    longitude = -43.2

    # Se o usuário procurar uma localização, faz o geocode
    if location_input:
        location = geolocator.geocode(location_input)
        if location:
            latitude = location.latitude
            longitude = location.longitude
            st.success(f"Location found: {location.address}. Latitude: {latitude}, Longitude: {longitude}")
        else:
            st.error("Location not found. Please try another search.")

    # Inputs de data para o usuário
    start_date = st.date_input("Select start date:", value=datetime(2023, 1, 1))
    end_date = st.date_input("Select end date:", value=datetime(2023, 10, 1))

    # Usuário seleciona os parâmetros meteorológicos que deseja
    parameters = st.multiselect(
        "Select the weather parameters to display:",
        options=[
            "Temperature (T2M)", 
            "Relative Humidity (RH2M)",   
            "Solar Radiation (ALLSKY_SFC_SW_DWN)", 
            "Wind Speed (WS10M)", 
        ],
        default=["Temperature (T2M)", "Wind Speed (WS10M)"]
    )

    # Mapeia os nomes exibidos para os nomes dos parâmetros da API
    parameter_map = {
        "Temperature (T2M)": "T2M",
        "Relative Humidity (RH2M)": "RH2M",
        "Solar Radiation (ALLSKY_SFC_SW_DWN)": "ALLSKY_SFC_SW_DWN",
        "Wind Speed (WS10M)": "WS10M",
    }

    # Pega os parâmetros da API baseados na seleção do usuário
    selected_params = [parameter_map[param] for param in parameters]

    # Formata as datas para a requisição da API
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    # Mensagens de advertência
    advisories = []

    # Botão para fazer a requisição à API
    if st.button("Get Data"):

        # URL da API NASA POWER
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"

        # Parâmetros para a requisição à API (parâmetros selecionados pelo usuário)
        params = {
            "parameters": ",".join(selected_params),  # Combina os parâmetros selecionados
            "start": start_date_str,  # Data inicial (entrada do usuário)
            "end": end_date_str,  # Data final (entrada do usuário)
            "latitude": latitude,  # Latitude (do mapa ou entrada do usuário)
            "longitude": longitude,  # Longitude (do mapa ou entrada do usuário)
            "community": "AG",  # AG para dados de Agro-climatologia
            "format": "JSON"  # Formato JSON
        }

        # Faz a requisição à API
        response = requests.get(url, params=params)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            data = response.json()

            # Verifica se os dados esperados estão presentes
            if 'properties' in data and 'parameter' in data['properties']:
                weather_data = data["properties"]["parameter"]

                # Verifica se há dados para trabalhar
                if weather_data:
                    df_list = []
                    # Para cada parâmetro selecionado, extrai os dados e cria um DataFrame
                    for param in selected_params:
                        param_data = weather_data.get(param, {})
                        if param_data:
                            # Cria um DataFrame com os dados
                            df = pd.DataFrame.from_dict(param_data, orient='index', columns=[param])
                            df.index = pd.to_datetime(df.index, format='%Y%m%d')
                            # Faz uma amostragem mensal
                            monthly_df = df.resample('M').mean()

                            # Adiciona avisos
                            if param == "T2M" and monthly_df["T2M"].mean() > 35:
                                advisories.append("High temperatures detected, ensure proper irrigation.")
                            if param == "ALLSKY_SFC_SW_DWN" and monthly_df["ALLSKY_SFC_SW_DWN"].mean() > 300:
                                advisories.append("High solar radiation detected, optimize water usage for crops.")

                            df_list.append(monthly_df)

                    # Combina todos os dados selecionados em um único DataFrame
                    combined_df = pd.concat(df_list, axis=1)

                    # Exibe as primeiras linhas do DataFrame no Streamlit
                    st.write("Data preview:", combined_df.head())

                    # Gera um gráfico de barras com os dados mensais
                    fig, ax = plt.subplots(figsize=(10, 6))
                    combined_df.plot(kind='bar', ax=ax, width=0.8)

                    # Define títulos e rótulos
                    ax.set_title(f"Monthly Averages for {', '.join(parameters)}", fontsize=16, pad=20)
                    ax.set_xlabel("Month", fontsize=12)
                    ax.set_ylabel("Value", fontsize=12)

                    # Rotaciona os rótulos do eixo x
                    ax.set_xticklabels(combined_df.index.strftime('%Y-%m'), rotation=45, ha='right')

                    # Torna as linhas de grade mais sutis
                    ax.grid(True, which='both', axis='y', linestyle='--', alpha=0.6)
                    ax.grid(False, which='both', axis='x')  # Remove as linhas de grade do eixo x

                    # Remove os contornos do gráfico
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)

                    # Ajusta o layout
                    plt.tight_layout()

                    # Exibe o gráfico no Streamlit
                    st.pyplot(fig)

                    # Exibe os avisos, se houver
                    if advisories:
                        st.subheader("Advisories for Farmers")
                        for advisory in advisories:
                            st.write(f"- {advisory}")

                else:
                    st.error("No weather data is available for this location or time range.")
            else:
                st.error("Error: Unexpected API response structure. 'properties' or 'parameter' key is missing.")
        else:
            # Se a requisição falhar, exibe o erro
            st.error(f"Error: {response.status_code} - {response.text}")

# Controla o estado da página
if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

# Renderiza a página baseada no estado
if st.session_state['page'] == 'landing':
    landing_page()
elif st.session_state['page'] == 'dashboard':
    dashboard()
