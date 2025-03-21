import pandas as pd
import folium
from folium.plugins import HeatMap
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Carregar o xls
df = pd.read_excel('dadosPorto.xlsx')
agrupados = df['ENDERECO'].value_counts()
agrupados.to_csv('Porto.csv', header=True)

geolocator = Nominatim(user_agent="geoapi")

def get_lat_lon(endereco):
    try:
        location = geolocator.geocode(endereco)
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        return None, None
    return None, None

# Criar colunas de latitude e longitude (se necessário)
if 'latitude' not in df.columns or 'longitude' not in df.columns:
    df[['latitude', 'longitude']] = df.apply(lambda row: get_lat_lon(f"{row['ENDERECO']}, {row['MUNICIPIO']}, {row['CEP']}"), axis=1, result_type="expand")

# Remover linhas sem coordenadas
df.dropna(subset=['latitude', 'longitude'], inplace=True)

# Criar o mapa
mapa = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=10)

# camada de calor
heat_data = df[['latitude', 'longitude']].values.tolist()
HeatMap(heat_data).add_to(mapa)

#  marcadores individuais
for _, row in df.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"{row['ENDERECO']}, {row['MUNICIPIO']}, {row['CEP']}",
        icon=folium.Icon(color="blue", icon="info-sign")  
    ).add_to(mapa)


# Salvar o mapa como HTML
mapa.save("mapa_Porto.html")

