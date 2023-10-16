import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import seaborn as sns
import plotly.express as px
import altair as alt
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import date
import json
import folium
import random
from shapely.geometry import Polygon, LinearRing, Point, mapping


# Path to GeoJSON file
file_path = 'Projet/InfoVigiCru.geojson'

st.set_page_config(layout='wide', initial_sidebar_state='expanded')
# Travail sur les coordonnées pour les extraires et pouvoir ainsi les plots dans streamlit :
# First : transform MULTILINESTINGS into POLIGON type to be able to extract coordinates more easily the coordinates:
def flatten_coordinates(coords):
    return [coord for sublist in coords for coord in sublist]

def linestring_to_polygon(gdf):
    # Convert LineString to Polygon
    gdf['geometry'] = [Polygon(LinearRing(flatten_coordinates(mapping(x)['coordinates']))) for x in gdf.geometry]
    return gdf 

# Beggining of the extraction of the coordinates :
#@st.cache_data()
def extract_coordinates(geo_data):
    # Extract coordonnates of geo_dataframe
    coords_df = geo_data.get_coordinates()
    # Create a geodf from the coords_df using the coordinates to create Point object:
    geometry = [Point(xy) for xy in zip(coords_df['x'], coords_df['y'])]
    gdf_coords = gpd.GeoDataFrame(coords_df, geometry=geometry, crs=geo_data.crs)
    # Rename column 'geometry' into 'point_geometry'
    gdf_coords = gdf_coords.rename(columns={'geometry': 'point_geometry'})
    # Concat gdf_coords with geo_data.
    result = pd.concat([geo_data, gdf_coords], axis=1)
    # Reinitialiser
    result = result.reset_index(drop=True)
    # Drop non useful columns: 
    result = result.drop(['point_geometry'], axis = 1)
    result = result.drop(['geometry'], axis = 1)
    # Rename col latitude and longitude:
    result = result.rename(columns={'x':'longitude', 'y':'latitude'})
    return result

def date_transformation(geo_data):
    geo_data['DhCEntCru'] = pd.to_datetime(geo_data['DhCEntCru'])
    geo_data['Year'] = geo_data['DhCEntCru'].dt.year
    return geo_data

def color_area(geo_data):
    # Color for the rivier :
    unique_values_riviere = geo_data['LbEntCru'].unique()
    color_mapping_riviere = {value: [round(random.uniform(0, 1), 1), round(random.uniform(0, 1), 1), round(random.uniform(0, 1), 1), round(random.uniform(0, 1), 1)] for value in unique_values_riviere}
    geo_data['Color_riviere'] = geo_data['LbEntCru'].map(color_mapping_riviere)
    # Color for the rivier basin :
    unique_values_bassin = geo_data['CdDiEnt_1'].unique()
    color_mapping_bassin = {value: [round(random.uniform(0, 1), 1), round(random.uniform(0, 1), 1), round(random.uniform(0, 1), 1), round(random.uniform(0, 1), 1)] for value in unique_values_bassin}
    geo_data['Color_bassin'] = geo_data['CdDiEnt_1'].map(color_mapping_bassin)
    return geo_data

# Function to clean the dataset (remove duplicates, apply above functions, drop non useful col, create new columns ....)
#@st.cache_data()
def clean_data():
    gdf = gpd.read_file(file_path)
    gdf = color_area(gdf)
    geo_data = linestring_to_polygon(gdf)
    geo_data = geo_data.drop(['TypEntCru'], axis=1)
    geo_data = geo_data.drop(['StEntCru'], axis=1)
    geo_data = geo_data.drop(['TypEnSup_1'], axis=1)
    geo_data = geo_data.dropna()
    geo_data['DhCEntCru'] = pd.to_datetime(geo_data['DhCEntCru'])
    geo_data['Year'] = geo_data['DhCEntCru'].dt.year.astype(int)
    geo_data['Month'] = geo_data['DhCEntCru'].dt.month.astype(int)
    geo_data_coordinates = extract_coordinates(geo_data)
    return geo_data_coordinates

# Use geopandas to read the GeoJSON file into a GeoDataFrame
geo_data = clean_data()

# Creation of the dictionaries containing the data and the corresponding value (name of the place)
dico_bassin = {
    'FRF': 'Adour-Garonne', 
    'EU35': 'Rhône-Méditerranée', 
    'FRG' : 'Loire-Bretagne',
    'EU31' : 'Seine-Normandie',
    'EU36' : 'Rhin',
    'EU3' : 'Meuse',
    'EU33' : 'Artois-Picardie',
    'FRL' : 'Réunion'
}# For the CdDiEnt_1 column

dico_territoire1 = {
    30 : 'Loire-Allier-Cher-Indre',
    32: 'Gironde-Adour-Dordogne',
    31 : 'Vienne-Charente-Atlantique',
    25 : 'Garonne-Tarn-Lot',
    18 : 'Rhône amont-Saône',
    20 : 'Grand Delta',
    29 : 'Bassins du Nord',
    4 : 'Seine aval-Côtiers Normands',
    2 : 'Meuse-Moselle',
    7 : 'Seine moyenne-Yonne-Loing',
    21 : 'Méditerranée Ouest',
    3 : 'Rhin-Sarre',
    9 : 'Maine-Loire aval',
    8 : 'Vilaine-Côtiers Bretons',
    19 : 'Alpes du Nord',
    6 : 'Seine amont-Marne amont',
    22 : 'Méditerranée Est (bassin continental)',
    26 : 'Méditerranée Est (bassin Corse)'
}# For the cdensup_1 column

st.sidebar.header("Analyse of the flood alert from 2006 to 2023 in France")
page = st.sidebar.selectbox("Select a part of the analyse :", ["General introduction", "Analyse of the alert", "General map", "Map by territory"])

with st.sidebar:
        st.write("This academical project was realized in the context of my Data Vizualization course at EFREI Paris, supervized by Mano MATHEW. The goal was to learn about data visualization. The data set use for this analyse come from the Service central d'hydrométéorologie et d'appui à la prévision des inondations.")
        st.write("Author : Camille SALAUN")
        st.write("Here is my [linkedin profile](https://www.linkedin.com/in/camille-salaun/)")
        st.write("Efrei Paris - #datavz2023efrei")


if page == "General introduction":
    st.title('Analyse of the flood alert from 2006 to 2023 in France')
    st.title('General introduction - What is the dataset composed of ?')
    st.write('First, lets load our dataset :')
    st.write(geo_data)
    st.write('After having cleaned the dataset, we can see that there are four principal columns that we will use : the LbEntCru column indicating the river name, the DhEntCru column with the dates of the alert (in general equal to the DhMentCru column), the cdensup_1 column indicating the territory, the CdDiEnt_1 indicating the basin, and the NivInfViCr with the alert level.\n',
             'We also created five columns from the data in the dataset : Color_rivier and Color_bassin columns indicating for each river or basin the color that it should have. We also extracted the year and month from the DhEntCru column to simplify our request. Finally, we extracted the latitude and longitude of each points form the geometry column of our dataset to be able to use those points in our modelisations.')
    st.write('Now that we have created all of the necessaries columns, we can finaly start to plot our datas. We will start by a general plot : a map regrouping each of the alert with the color depending on the river name :')
    st.map(geo_data, 
        latitude = 'latitude',
        longitude = 'longitude',
        size = 'NivInfViCr',
        color = 'Color_riviere'
        )
    st.write('Well, there are many color in this map and it is really ugly. Even if this map permit us to see all the river on which an alert was created since 2006, it still is a general and non usefull map. So, let us try another type of map :')
    st.map(geo_data, 
        latitude = 'latitude',
        longitude = 'longitude',
        size = 'NivInfViCr',
        color = 'Color_bassin'
    )
    st.write('This map repesent the different alert and each color correspond to a basin : we can see that there is eight principal bassin that we will be able to use to clasify and precise our data and analyse.\n',
             'Now, lets see how are the alert divide by bassin :')
    
    # Pie chart of the bassin percentages
    count_bassin = geo_data['CdDiEnt_1'].value_counts()
    bassin_percentage = (count_bassin/count_bassin.sum())*100
    labels = [dico_bassin.get(key, key) for key in bassin_percentage.index]
    fig = px.pie(values = bassin_percentage, names=labels, title='Repartition of the flood alerts by river basin')
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=0),)
    st.plotly_chart(fig, use_container_width=True)
    st.write('Ok, we can see that the basin with the most alert are Adour-Garonne, Loire-Bretagne, Seine-Normandie and Rhône-Mediterranée, but why is that ?')

    st.write('Lets see if the number of alert by basin is related to its number of river :')
    # Pie chart of the percentage of total rivier by bassin
    unique_rivers_by_basin = geo_data.groupby('CdDiEnt_1')['LbEntCru'].nunique().reset_index()
    unique_rivers_by_basin.columns = ['CdDiEnt_1', 'Unique_River_Count']
    riviere_bassin_percentage = (unique_rivers_by_basin['Unique_River_Count'] / unique_rivers_by_basin['Unique_River_Count'].sum()) * 100
    labels = [dico_bassin.get(key, key) for key in unique_rivers_by_basin['CdDiEnt_1']]
    fig = px.pie(names=labels, values=riviere_bassin_percentage, title='Repartition of Unique Rivers by River Basin')
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.write('So we can see that the number of alert by basin is related to the number of river in it, wich is pretty logical (the more river ther is in a basin, the more likely an alert will appear). But even so, the basin with the most alert, so thoose that need a particular attention are the following : Adour-Garonne, Loire-Bretagne, Seine-Normandie and Rhône-Mediterranée.')

elif page == "Analyse of the alert":
    st.title('Analyse of the flood alert from 2006 to 2023 in France')
    st.title('Analyse of the alert by year, month and type')

    st.write('Now that we know wich basin have the most alert and risk, let us analyse the type of alert that the basin can have in function of the level of alert and the year.')
    # Histplot of the repartition of the alert depending on the river name and the level of alert
    st.write('First, lets us analyse the repartition of the alert by revier and by level of alert :')
    select_values_bar = st.selectbox('Select a river basin :', list(dico_bassin.values())) 
    select_bassin_bar = {k for k,v in dico_bassin.items() if v == select_values_bar}
    filtered_bar = geo_data[geo_data['CdDiEnt_1'].isin(select_bassin_bar)]
    bar_chart = alt.Chart(filtered_bar, title ='Repartition of the alert by river name and level').mark_bar().encode(
        x = alt.X("LbEntCru:N", title="River Name"),
        y = alt.Y("count():Q", title ="Number of alerts"),
        color = alt.Color("NivInfViCr:N")
    )
    bar_chart = bar_chart.properties(
        width=600,
        title=f'Repartition of the alert by river name and level in {select_values_bar} Basin'
    )
    st.altair_chart(bar_chart, use_container_width=True)
    st.write('We can see in this graph that in general there is no many level 2 alert. Most of the river for which there is an alert regroup more than 500 alerts in general and not many river regroup more than 2000 alerts. Those huge number of alert can be explained by the fact that the rivers are monitored at multiple place during their journey. So, the longer the river, the more alert their will be for it.\n',
             'Overall, Adour-Garonne is the basin with the most alert. We can also see that the river Oise Amont in the Seine-normandie Basin is above the mean of alert in the same region with next to 4.500 alert form 2006 to 2023. Finally, the Rhône-Méditerranée basin is the one were there is the most level 2 alert (5) and the Artois-Picardie and Réunion basin are the less risky basin with no more than 1500 and 700 alert for a river.')

    # Bar chart type of alert by years:
    st.write('Now, lets us analyse the number of alert by years to see if the ones with the most alert :')
    year_range = (2006, 2023)
    selected_year_bar2 = st.slider('Select a year :', min_value=year_range[0], max_value=year_range[1], value=year_range[0], key="slider_1") 

    filtered_date_bar = geo_data[geo_data['Year'] == selected_year_bar2]

    bar_chart2 = alt.Chart(filtered_date_bar).mark_bar().encode(
        x = alt.X("NivInfViCr:N", title="Type of alert"),
        y = alt.Y("count():Q", title ="Number of occurences")
    )
    bar_chart2 = bar_chart2.properties(
        width=600,
        title=f'Occurrences of each alert level in year {selected_year_bar2}'
    )
    st.altair_chart(bar_chart2, use_container_width=True)
    st.write('With this graph, we were able to see that the years 2006, 2013, 2020 and 2021 had particularly many alert compared to the other. While the years 2007, 2009, 2010 and 2012 had less alert than the other years.')

    # Bar plot of the count of alerts by months:
    st.write('Lets now see which months regrouped the more alert:')
    bar_chart3 = alt.Chart(geo_data).mark_bar().encode(
        x=alt.X("month(DhCEntCru):T", title="Month", axis=alt.Axis(format="%B")),
        y=alt.Y("count():Q", title="Number of alerts"),
        color=alt.Color("NivInfViCr:N")
    )
    bar_chart3 = bar_chart3.properties(
        width=600,
        title=f'Repartition of the alert by month:'
    )
    st.altair_chart(bar_chart3, use_container_width=True)

    st.write('Strangely, there are most alert noted in July, August, November and March. It may be because the level of the river in this month was unusual for the season.  But which territory were the most affected ?')
    
    # Line plot number of alerts by years :
    st.write('Now, lets see the evolution of the alerts in function of the years and the territory, to be able to see the more risky rivers and territories:')
    select_territoire_line_char = st.selectbox('Select a territory :', list(dico_territoire1.values()), key="box_1") 
    select_territoire_line = {k for k,v in dico_territoire1.items() if v == select_territoire_line_char}
    # We need to transform select_territoire_line into a string without the {} and with single quote :
    select_territoire_line_str = ', '.join(f'{str(item)}' for item in select_territoire_line)

    filtered_line = geo_data.loc[geo_data['cdensup_1'] == select_territoire_line_str]
    line_chart = alt.Chart(filtered_line, title = 'Line plot of the number of alert by territory in function of the years').mark_line().encode(
        x= alt.X("year(DhCEntCru):O", title="Years"),
        y = "count():Q",
        #color = alt.Color('LbEntCru:N')
    ).properties(
        width=600,
        title=f'Line Chart for {select_territoire_line_char}'
    )
    st.altair_chart(line_chart, use_container_width=True)
    st.write('Thanks to this graph, we were able to see that : in general, many alert were count in 2006 as well as in 2013 and 2020. In 2013, many alert were noted in the Maine-Loire Aval territory while in 2020 it was in Méditerranée Ouest, Seine Moyenne and Maine-Loire aval. In 2021, the territories Rhin Sarre and Mediterranée est were the one with the most alert. Finally, in general, Vilaine-Côtière Bretons and Seine amont-Marne amont are the territory with a constant count of alert (maybe because there is no larte for the years between 2006 and 2020).')

elif page == "General map":
    st.title('Analyse of the flood alert from 2006 to 2023 in France')
    st.title('General map')
    st.write('Here is a general map of the alert in function of their level and the year :')
    # Intercative map by year and riviere :
    year_range = (2006, 2023)
    selected_year_map2 = st.slider('Select a year :', min_value=year_range[0], max_value=year_range[1], value=year_range[0], key="slider_3") 
    select_level_map2 = st.selectbox('Select a level of alert :', geo_data['NivInfViCr'].unique(), key="box_3")

    filtered_line_map2 = geo_data.loc[(geo_data['NivInfViCr'] == select_level_map2) & (geo_data['Year'] == selected_year_map2)]
    center_lat2 = filtered_line_map2['latitude'].mean()
    center_lon2 = filtered_line_map2['longitude'].mean()
    fig2 = go.Figure(go.Densitymapbox(
                        lat=filtered_line_map2['latitude'], 
                        lon=filtered_line_map2['longitude'],
                        radius=1,
                        colorscale="Viridis",
                    ))

    fig2.update_layout(
        mapbox_style="stamen-terrain", 
        mapbox_center={"lat": center_lat2, "lon": center_lon2}, 
        mapbox_zoom=5,
        )

    fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig2)
    st.write('As previously stated, the years 2006, 2013, 2020 and 2021 contains the most alert. We can see that for the year 2006, all the basin but the Ardour-Garonne had alert while it was the contrary in 2013 were alert were only noted in this basin. We notice the same phenomenom for the year 2020 and 2021 were the basin Loire Bretagne and Seine Normandie as well as the south of the Rhône Mediterranée basin had many alert in 2020 while it was only the Adour-Garonne basin the following year.\n',
             'We also notice that most of the alert of level 2 happended in 2006 and in the central-west of the Rhône-Méditerranée basin, which correspond to what we concluded earlier.')


elif page == "Map by territory":
    st.title('Analyse of the flood alert from 2006 to 2023 in France')
    st.title('Map by territory and by year')
    st.write('This map will permit to visualize what we saw earlier in the analyse of the alerts part:')
    # Interactive map of flood by year and territories
    year_range = (2006, 2023)
    selected_year_map1 = st.slider('Select a year :', min_value=year_range[0], max_value=year_range[1], value=year_range[0], key="slider_2") 
    select_territoire_char_map1 = st.selectbox('Select a territory :', list(dico_territoire1.values()), key="box_2") 
    select_territoire_line_map1 = {k for k,v in dico_territoire1.items() if v == select_territoire_char_map1 }
    select_territoire_line_str_map1 = ', '.join(f'{str(item)}' for item in select_territoire_line_map1)

    filtered_line_map = geo_data.loc[(geo_data['cdensup_1'] == select_territoire_line_str_map1) & (geo_data['Year'] == selected_year_map1)]
    center_lat = filtered_line_map['latitude'].mean()
    center_lon = filtered_line_map['longitude'].mean()
    fig1 = go.Figure(go.Densitymapbox(
                        lat=filtered_line_map['latitude'], 
                        lon=filtered_line_map['longitude'],
                        radius=1,
                        colorscale="Viridis",
                    ))

    fig1.update_layout(
        mapbox_style="stamen-terrain", 
        mapbox_center={"lat": center_lat, "lon": center_lon}, 
        mapbox_zoom=7,
        )
    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig1)
    st.write('Thanks to this graph, we were able to confirm what we saw earlier, which is that in 2013, many alert were noted in the Maine-Loire Aval territory while in 2020 it was in Méditerranée Ouest, Seine Moyenne and Maine-Loire aval. In 2021, the territories Rhin Sarre and Mediterranée est were the one with the most alert.')
    st.write('So, to conclude our analysis, we can say that :')
    st.markdown('- The basin with the most alert are Adour-Garonne, Loire-Bretagne, Seine-Normandie and Rhône-Mediterranée,\n- The number of alert by basin is related to the number of river in it,\n- The river Oise Amont in the Seine-normandie Basin is above the mean of alert in the same region,\n- The Rhône-Méditerranée basin is the one were there is the most level 2 alert,\n-The Artois-Picardie and Réunion basin are the less risky basin with no more than 1500 and 700 alert for a river,\n- The years 2006, 2013, 2020 and 2021 had particularly many alert compared to the other,\n- The years 2007, 2009, 2010 and 2012 had less alert than the other years,\n- There are most alert noted in July, August, November and March,\n- In 2013, many alert were noted in the Maine-Loire Aval territory while in 2020 it was in Méditerranée Ouest, Seine Moyenne and Maine-Loire aval. In 2021, the territories Rhin Sarre and Mediterranée est were the one with the most alert,\n- For the year 2006, all the basin but the Ardour-Garonne had alert while it was the contrary in 2013 were alert were only noted in this basin. We notice the same phenomenom for the year 2020 and 2021 were the basin Loire Bretagne and Seine Normandie as well as the south of the Rhône Mediterranée basin had many alert in 2020 while it was only the Adour-Garonne basin the following year.')
