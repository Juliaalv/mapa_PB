import streamlit as st
import pandas as pd
import folium
from shapely.wkt import loads 
from streamlit_folium import folium_static

@st.cache_data
def load_data():
    geracao_75 = pd.read_csv("df_geracao_pb_75_ufv_eol.csv")
    geracao_5 = pd.read_csv("df_ger_pb_5_ufv_eol.csv")
    subestacoes = pd.read_csv("dados_extraidos.csv")
    return geracao_75, geracao_5, subestacoes

# Carregar dados
geracao_75, geracao_5, subestacoes = load_data()

# Lista de usinas em corte
usinas_em_corte = [
    "Chafariz 1", "Chafariz 2", "Chafariz 3", "Chafariz 4", "Chafariz 5", "Chafariz 6",
    "Serra do Seridó II", "Serra do Seridó III", "Serra do Seridó IV", "Serra do Seridó VI", 
    "Serra do Seridó VII", "Serra do Seridó X", "Serra do Seridó IX", "Serra do Seridó XI", 
    "Serra do Seridó XII", "Serra do Seridó XIV", "Serra do Seridó XVI", "Serra do Seridó XVII",
    "Luzia 2", "Luzia 3", "Santa Luzia 1", "Santa Luzia 4", "Santa Luzia V", "Santa Luzia VII", "Santa Luzia IX",
    "Coremas I", "Coremas II", "Coremas III", "Coremas IV", "Coremas V", "Coremas VI", "Coremas VII"
]

# Seleção do tipo de geração
st.sidebar.title("Opções de Visualização")
opcao_geracao = st.sidebar.radio("Selecione a faixa de geração:", ["Geração ≥ 75 kW", "Geração ≥ 5 MW"])

if opcao_geracao == "Geração ≥ 75 kW":
    dados_geracao = geracao_75.copy()
else:
    dados_geracao = geracao_5.copy()

# Tratamento de dados de geração
dados_geracao["Latitude"] = dados_geracao["Latitude"].astype(str).str.replace(",", ".").astype(float)
dados_geracao["Longitude"] = dados_geracao["Longitude"].astype(str).str.replace(",", ".").astype(float)
dados_geracao.dropna(subset=["Latitude", "Longitude"], inplace=True)

# Extrair centróides das subestações
def extract_centroid(geometry):
    shape = loads(geometry)
    centroid = shape.centroid
    return centroid.x, centroid.y

subestacoes["Longitude"], subestacoes["Latitude"] = zip(*subestacoes["geometry"].apply(extract_centroid))

# Título
st.title("Mapa de Geração e Subestações na Paraíba")

# Filtro interativo
tipos_disponiveis = ["EOL", "UFV", "Subestação"]
selecionados = st.multiselect("Selecione os tipos que deseja visualizar no mapa:", tipos_disponiveis, default=tipos_disponiveis)

# Mapa base
m = folium.Map(location=[-7.121, -36.722], zoom_start=8, tiles="cartodbpositron")

cores_geracao = {
    "EOL": "blue",
    "UFV": "orange",
}

# Pontos de geração
if any(tipo in selecionados for tipo in cores_geracao.keys()):
    for _, row in dados_geracao.iterrows():
        tipo = row["Tipo de Geração"]
        nome = row["Empreendimento"]
        if tipo in selecionados:
            if nome in usinas_em_corte:
                if tipo == "EOL":
                    cor = "green"
                elif tipo == "UFV":
                    cor = "yellow"
                else:
                    cor = "red"
                popup_text = f"<b>Usina em corte:</b> {nome}<br>Potência: {row['Potência Outorgada (kW)']} kW<br>Município: {row['DscMuninicpios']}"
            else:
                cor = cores_geracao[tipo]
                popup_text = f"{nome}<br>Potência: {row['Potência Outorgada (kW)']} kW<br>Município: {row['DscMuninicpios']}"

            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=3,
                color=cor,
                fill=True,
                fill_color=cor,
                fill_opacity=0.7,
                popup=popup_text,
            ).add_to(m)

# Subestações
if "Subestação" in selecionados:
    for _, row in subestacoes.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=3,
            color="black",
            fill=True,
            fill_color="black",
            fill_opacity=0.7,
            popup=f"Subestação: {row['NOME']}",
        ).add_to(m)

# Legenda atualizada
legend_html = """
<div style="position: fixed; 
            bottom: 30px; right: 30px; width: 300px; height: 160px; 
            background-color: white; z-index:9999; padding: 10px;
            border-radius: 10px; box-shadow: 2px 2px 3px rgba(0,0,0,0.3);
            font-size:14px;">
    <strong>Legenda:</strong><br>
    <span style="color:blue;">⬤</span> Eólica (EOL) <br>
    <span style="color:orange;">⬤</span> Solar (UFV) <br>
    <span style="color:green;">⬤</span> Eólica em corte <br>
    <span style="color:yellow;">⬤</span> Solar em corte <br>
    <span style="color:black;">⬤</span> Subestação
</div>
"""

st.markdown(legend_html, unsafe_allow_html=True)
folium_static(m, width=800, height=750)
