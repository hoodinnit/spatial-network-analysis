# Spatial Network Analysis & Emergency Routing Dashboard 🗺️

## Project Overview
This project is an interactive Geographic Information System (GIS) dashboard built with Python. It analyzes the municipal road network of Changlun, Kedah, applying graph theory algorithms to identify structural traffic bottlenecks and optimize emergency response logistics. 

## Key Features
* **Network Graph Extraction:** Utilizes `OSMnx` to programmatically extract physical road infrastructure and speed limit data directly from OpenStreetMap.
* **Traffic Bottleneck Detection:** Applies Betweenness Centrality (`NetworkX`) to mathematically identify the most critical intersections vulnerable to congestion.
* **Infrastructure Scraping:** Automatically locates and maps critical Points of Interest (POIs), specifically local medical facilities and hospitals.
* **Emergency Route Optimization:** Implements Dijkstra's shortest-path algorithm, weighted by real-world travel times, to dynamically calculate the fastest response route from an incident coordinate to the nearest medical facility.
* **Interactive UI:** Deploys a multi-layered, interactive web map using `Folium`, allowing users to toggle analytical layers on and off.

## Technology Stack
* **Language:** Python 3
* **Geospatial & Data:** OSMnx, GeoPandas
* **Mathematics & Algorithms:** NetworkX (Graph Theory)
* **Visualization:** Folium, Matplotlib

## How to Run Locally
1. Clone this repository.
2. Install dependencies: `pip install osmnx networkx folium matplotlib geopandas`
3. Run the master script: `python master_gis_dashboard.py`
4. Open the generated `index.html` file in any modern web browser.
