import streamlit as st
import pandas as pd
import folium
from shapely.wkt import loads 
from streamlit_folium import folium_static

@st.cache_data
def load_data():
    geracao = pd.read_csv("geracao_sem_micro_PB.csv")  
    subestacoes = pd.read_csv("dados_extraidos.csv")  
    return geracao, subestacoes

# Carregar dados
ger_sem_micro, dados_extraidos = load_data()
ger_sem_micro["Latitude"] = ger_sem_micro["Latitude"].astype(str).str.replace(",", ".").astype(float)
ger_sem_micro["Longitude"] = ger_sem_micro["Longitude"].astype(str).str.replace(",", ".").astype(float)
ger_sem_micro.dropna(subset=["Latitude", "Longitude"], inplace=True)

# Extrair centróides
def extract_centroid(geometry):
    shape = loads(geometry)
    centroid = shape.centroid
    return centroid.x, centroid.y

dados_extraidos["Longitude"], dados_extraidos["Latitude"] = zip(*dados_extraidos["geometry"].apply(extract_centroid))

# Título
st.title("Mapa de Geração e Subestações na Paraíba")

# Filtro interativo
tipos_disponiveis = ["EOL", "UFV", "UTE", "PCH", "Subestação"]
selecionados = st.multiselect("Selecione os tipos que deseja visualizar no mapa:", tipos_disponiveis, default=tipos_disponiveis)

# Mapa base
m = folium.Map(location=[-7.121, -36.722], zoom_start=8, tiles="cartodbpositron")

cores_geracao = {
    "EOL": "blue",
    "UFV": "orange",
    "UTE": "red",
    "PCH": "green"
}

# Pontos de geração
if any(tipo in selecionados for tipo in cores_geracao.keys()):
    for _, row in ger_sem_micro.iterrows():
        tipo = row["Tipo de Geração"]
        if tipo in selecionados:
            cor = cores_geracao[tipo]
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=3,
                color=cor,
                fill=True,
                fill_color=cor,
                fill_opacity=0.7,
                popup=f"{row['Empreendimento']}<br>Potência: {row['Potência Outorgada (kW)']} kW<br>Município: {row['DscMuninicpios']}",
            ).add_to(m)

# Subestações
if "Subestação" in selecionados:
    for _, row in dados_extraidos.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=3,
            color="black",
            fill=True,
            fill_color="black",
            fill_opacity=0.7,
            popup=f"Subestação: {row['NOME']}",
        ).add_to(m)

# Legenda
legend_html = """
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 250px; height: 150px; 
            background-color: white; z-index:9999; padding: 10px;
            border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            font-size:14px;">
    <strong>Legenda:</strong><br>
    <span style="color:blue;">⬤</span> Eólica (EOL) <br>
    <span style="color:orange;">⬤</span> Solar (UFV) <br>
    <span style="color:red;">⬤</span> Termelétrica (UTE) <br>
    <span style="color:green;">⬤</span> Pequena Central Hidrelétrica (PCH) <br>
    <span style="color:black;">⬤</span> Subestação
</div>
"""

st.markdown(legend_html, unsafe_allow_html=True)
folium_static(m, width=1400, height=750)

