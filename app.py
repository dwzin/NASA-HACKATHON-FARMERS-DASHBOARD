import sqlite3
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta

# Função para conectar ao banco de dados SQLite
def create_connection():
    conn = sqlite3.connect('crop_management.db')
    return conn

# Função para criar a tabela de culturas
def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            plant_date DATE NOT NULL,
            harvest_date DATE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Função para registrar uma nova cultura
def register_crop(name, plant_date, harvest_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO crops (name, plant_date, harvest_date)
        VALUES (?, ?, ?)
    ''', (name, plant_date, harvest_date))
    conn.commit()
    conn.close()

# Função para obter todas as culturas registradas
def get_crops():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM crops')
    crops = cursor.fetchall()
    conn.close()
    return crops

# Cria a tabela no banco de dados
create_table()

# Adicione o estilo CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3;
    }
    h1 {
        color: #228B22;
        font-family: 'Helvetica', sans-serif;
        text-align: center;
        font-weight: bold;
        font-size: 3em;
    }
    .css-1cpxqw2 {
        background-color: #e6ffe6;
        color: #006400;
        border: 1px solid #228B22;
        border-radius: 10px;
        font-family: 'Arial', sans-serif;
        padding: 8px;
    }
    .stButton > button {
        background-color: #228B22;
        color: white;
        border-radius: 10px;
        font-size: 1.2em;
        font-weight: bold;
        padding: 10px 20px;
    }
    h2 {
        color: #006400;
        font-family: 'Arial', sans-serif;
    }
    .alert {
        color: #FF4500; /* Red color for alerts */
        font-weight: bold;
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
        st.session_state['page'] = 'dashboard'


def make_final_decision(plant_date, harvest_date, current_date, weather_advisories):
    # Calculate the time until planting and harvesting
    days_to_plant = (plant_date - current_date).days
    days_to_harvest = (harvest_date - current_date).days

    # If there are weather advisories that suggest delaying, account for that
    if any("too low" in advisory or "too high" in advisory for advisory in weather_advisories):
        return "Current weather conditions are not optimal. Consider waiting for better conditions before planting."

    # Provide planting suggestions based on the timeline
    if days_to_plant > 0:
        return f"You should wait {days_to_plant} days to plant."
    elif days_to_plant == 0:
        return "You should plant today."
    elif days_to_harvest > 0:
        return f"You should harvest in {days_to_harvest} days."
    else:
        return "The harvest date has passed. Consider preparing for the next planting season."

def generate_advisories(combined_df, selected_crop):
    advisories = []

    # Analyze temperature
    if "T2M" in combined_df.columns:
        avg_temp = combined_df["T2M"].mean()
        if avg_temp < 10:  # Example: too cold for most crops
            advisories.append(f"The average temperature is too low for {selected_crop}. Consider using heat protection.")
        elif avg_temp > 35:  # Example: too hot for most crops
            advisories.append(f"The temperature is too high for {selected_crop}. Ensure you provide enough water and shade.")
        else:
            advisories.append(f"The temperature is within the optimal range for {selected_crop}.")

    # Analyze humidity
    if "RH2M" in combined_df.columns:
        avg_humidity = combined_df["RH2M"].mean()
        if avg_humidity < 30:  # Example: low humidity
            advisories.append(f"Humidity is too low for {selected_crop}. Increase irrigation.")
        elif avg_humidity > 80:  # Example: high humidity
            advisories.append(f"High humidity could lead to fungal growth on {selected_crop}. Increase ventilation.")
        else:
            advisories.append(f"Humidity levels are ideal for {selected_crop}.")

    # Analyze solar radiation
    if "ALLSKY_SFC_SW_DWN" in combined_df.columns:
        avg_solar = combined_df["ALLSKY_SFC_SW_DWN"].mean()
        if avg_solar < 10:  # Example: low solar radiation
            advisories.append(f"Solar radiation is low, which could reduce {selected_crop}'s growth. Consider supplemental lighting.")
        elif avg_solar > 25:  # Example: high solar radiation
            advisories.append(f"High solar radiation is supporting the growth of {selected_crop}. Ensure adequate water supply.")
    
    # Analyze wind speed
    if "WS10M" in combined_df.columns:
        avg_wind = combined_df["WS10M"].mean()
        if avg_wind > 10:  # Example: high wind speed
            advisories.append(f"High wind speeds could damage {selected_crop}. Consider using windbreaks.")
        else:
            advisories.append(f"Wind speeds are optimal for growing {selected_crop}.")

    return advisories


# Função para o dashboard
def dashboard():
    st.title("Farmer's Dashboard: Review Your Last Harvest")
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

    # Define as estações de cultivo
    growing_seasons = {
        "Beans": (3, 9),   # March to September
        "Corn": (4, 8),    # April to August
        "Wheat": (9, 6),   # September to June (overlapping year)
        "Rice": (1, 4),    # January to April
        "Soybeans": (5, 9),# May to September
        "Potatoes": (3, 6),# March to June
        "Tomatoes": (5, 10),# May to October
        "Cabbage": (2, 5), # February to May
        "Carrots": (3, 7), # March to July
        "Pumpkins": (6, 10),# June to October
        "Lettuce": (3, 7), # March to July
        "Peas": (2, 6),    # February to June
        "Radishes": (4, 6),# April to June
        "Bell Peppers": (5, 10), # May to October
        "Eggplants": (5, 10), # May to October
        "Zucchini": (5, 8), # May to August
        "Onions": (1, 4),   # January to April
        "Garlic": (10, 4),  # October to April (overlapping year)
        "Sweet Potatoes": (5, 9), # May to September
        "Strawberries": (4, 6), # April to June
        "Blueberries": (4, 7) # April to July
    }

    # Selecionar a cultura a partir do banco de dados
    st.subheader("Select a Crop")
    with st.expander("Selecter"):
        crops = get_crops()
        crop_names = [crop[1] for crop in crops]  # Get the crop names

        selected_crop = st.selectbox("Choose a crop:", crop_names)

        if selected_crop:
            # Alert the user about the selected crop
            crop_info = [crop for crop in crops if crop[1] == selected_crop][0]
            st.success(f"You selected: {crop_info[1]}. Plant Date: {crop_info[2]}, Harvest Date: {crop_info[3]}.")

            # Retrieve planting and harvest dates
            plant_date = datetime.strptime(crop_info[2], "%Y-%m-%d")  # Convert string to datetime
            harvest_date = datetime.strptime(crop_info[3], "%Y-%m-%d")

            # Check if it's a suitable time to plant the selected crop
            crop_start_season, crop_end_season = growing_seasons[selected_crop]
            current_month = datetime.now().month

            if crop_start_season <= current_month <= crop_end_season:
                st.success(f"It is a suitable time to plant {selected_crop}.")
            else:
                st.warning(f"It is NOT a suitable time to plant {selected_crop}.")

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

    # Funcionalidade de gestão de culturas
    # Funcionalidade de gestão de culturas
    st.subheader("Crop Management")
    with st.expander("Manager"):
        crops_name = []
        for x in growing_seasons:
            crops_name.append(x)
        crop_name = st.selectbox("Crop Name", crops_name ,help="Enter the name of the crop you want to register.")
        plant_date_input = st.date_input("Planting Date", help="Select the date when you plan to plant the crop.")
        expected_harvest_date = st.date_input("Expected Harvest Date", value=plant_date_input + timedelta(days=120), help="Estimated date of harvest.")

        # Check if the planting date is in the future
        if st.button("Register Crop"):
            today = datetime.today().date()  # Get today's date

            # Display error if planting date is in the future
            if expected_harvest_date > today:
                st.error("The harvest date cannot be in the future. Please select a valid date.")
            elif not crop_name:
                st.error("Please enter a valid crop name.")
            else:
                # Register the crop if all validations pass
                register_crop(crop_name, plant_date_input, expected_harvest_date)
                st.success(f"Crop '{crop_name}' registered with planting date {plant_date_input} and expected harvest date {expected_harvest_date}.")
            # Exibir todas as culturas registradas
            st.subheader("Registered Crops")
            crops = get_crops()
            if crops:
                crops_df = pd.DataFrame(crops, columns=["ID", "Name", "Plant Date", "Harvest Date"])
                st.write(crops_df)
            else:
                st.write("No crops registered yet.")

    # Pega os parâmetros da API baseados na seleção do usuário
    selected_params = [parameter_map[param] for param in parameters]

    # Botão para fazer a requisição à API
# Botão para fazer a requisição à API
    if st.button("Get Data") and selected_crop:
        # Define the start and end dates for the API request
        start_date_str = plant_date.strftime('%Y%m%d')
        end_date_str = harvest_date.strftime('%Y%m%d')

        # URL da API NASA POWER
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"

        # Parameters for the API request
        params = {
            "parameters": ",".join(selected_params),  # Combina os parâmetros selecionados
            "start": start_date_str,  # Data inicial baseada na data de plantio
            "end": end_date_str,      # Data final baseada na data de colheita
            "latitude": latitude,      # Latitude (do mapa ou entrada do usuário)
            "longitude": longitude,    # Longitude (do mapa ou entrada do usuário)
            "community": "AG",        # AG para dados de Agro-climatologia
            "format": "JSON"          # Formato JSON
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
                df_list = []
                for param in selected_params:
                    param_data = weather_data.get(param, {})
                    if param_data:
                        # Cria um DataFrame com os dados
                        df = pd.DataFrame.from_dict(param_data, orient='index', columns=[param])
                        df.index = pd.to_datetime(df.index, format='%Y%m%d')
                        # Faz uma amostragem mensal
                        monthly_df = df.resample('M').mean()
                        df_list.append(monthly_df)  # Adiciona apenas se houver dados

                # Verifica se df_list não está vazio antes de concatenar
                if df_list:
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
                    advisories = generate_advisories(combined_df, selected_crop)

                    # Display advisories
                    if advisories:
                        st.subheader("Advisories for Farmers")
                        for advisory in advisories:
                            st.write(f"- {advisory}")
                    final_decision = make_final_decision(plant_date, harvest_date, datetime.now(), advisories)


                else:
                    st.error("No weather data available for the selected parameters.")

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
