import osmnx as ox
import networkx as nx
import folium
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 1. Fetch Network and Apply Physics
place_name = "Changlun, Kedah, Malaysia"
print("1/7: Loading road network and calculating physics constraints...")
G = ox.graph_from_address(place_name, dist=3000, network_type='drive')
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

# 2. Calculate Traffic Bottlenecks (Betweenness Centrality)
print("2/7: Analyzing network infrastructure for traffic bottlenecks...")
centrality = nx.betweenness_centrality(G, weight='length')
nx.set_node_attributes(G, centrality, 'centrality')

# 3. Scrape and Parse Medical Infrastructure (POIs)
print("3/7: Querying OpenStreetMap for local medical facilities...")
tags = {'amenity': ['hospital', 'clinic']}
try:
    pois = ox.features_from_address(place_name, tags=tags, dist=3000)
    poi_coords = []
    for idx, row in pois.iterrows():
        centroid = row.geometry.centroid
        poi_coords.append({
            'name': row.get('name', 'Unnamed Medical Facility'),
            'lat': centroid.y,
            'lon': centroid.x
        })
except Exception as e:
    print(f"Warning: Could not fetch POIs. Using fallbacks.")
    poi_coords = [{'name': 'Klinik Kesihatan Changlun', 'lat': 6.4342, 'lon': 100.4321}]

# 4. Routing Setup (Start Coordinate)
start_lat, start_lon = 6.4315, 100.4285  # Central Changlun
start_node = ox.nearest_nodes(G, X=start_lon, Y=start_lat)

# 5A. Execute Standard Commute Route (To Sintok/UUM)
print("4/7: Calculating standard commute route...")
std_end_lat, std_end_lon = 6.4450, 100.4450
std_end_node = ox.nearest_nodes(G, X=std_end_lon, Y=std_end_lat)
std_route = nx.shortest_path(G, source=start_node, target=std_end_node, weight='travel_time')
std_time_minutes = nx.shortest_path_length(G, source=start_node, target=std_end_node, weight='travel_time') / 60

# 5B. Execute Emergency Response Algorithm
print("5/7: Calculating optimal emergency route to nearest facility...")
best_emg_route = None
min_emg_time = float('inf')
best_poi = None

for poi in poi_coords:
    emg_end_node = ox.nearest_nodes(G, X=poi['lon'], Y=poi['lat'])
    try:
        time_seconds = nx.shortest_path_length(G, source=start_node, target=emg_end_node, weight='travel_time')
        if time_seconds < min_emg_time:
            min_emg_time = time_seconds
            best_emg_route = nx.shortest_path(G, source=start_node, target=emg_end_node, weight='travel_time')
            best_poi = poi
    except nx.NetworkXNoPath:
        continue

min_emg_time_minutes = min_emg_time / 60 if min_emg_time != float('inf') else 0

# 6. Map Setup and Layer Initialization
print("6/7: Compiling interactive interface layers...")
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
center_lat = gdf_nodes['y'].mean()
center_lon = gdf_nodes['x'].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB dark_matter')

# Independent layers for the control menu
layer_base_roads = folium.FeatureGroup(name="Base Road Grid", show=True)
layer_bottlenecks = folium.FeatureGroup(name="Traffic Bottlenecks Heatmap", show=False)
layer_facilities = folium.FeatureGroup(name="Medical Infrastructure Sites", show=True)
layer_std_route = folium.FeatureGroup(name="Standard Commute Route (UUM)", show=True)
layer_emergency = folium.FeatureGroup(name="Active Emergency Route", show=False)

# Populate Layer 1: Base Roads
for _, edge in gdf_edges.iterrows():
    coordinates = [(point[1], point[0]) for point in edge['geometry'].coords] if 'geometry' in edge else []
    if coordinates:
        folium.PolyLine(coordinates, color="#333333", weight=1.5, opacity=0.4).add_to(layer_base_roads)

# Populate Layer 2: Bottlenecks
max_cent = max(centrality.values()) if centrality.values() else 1
for node_id, row in gdf_nodes.iterrows():
    cent = row['centrality']
    if cent < (max_cent * 0.02):
        continue
    color = mcolors.to_hex(plt.cm.inferno(cent / max_cent))
    folium.CircleMarker(
        location=[row['y'], row['x']],
        radius=3 + (cent / max_cent) * 8,
        color=color, fill=True, fill_color=color, fill_opacity=0.8,
        tooltip=f"Intersection ID: {node_id}<br>Bottleneck Score: {cent:.4f}"
    ).add_to(layer_bottlenecks)

# Populate Layer 3: Facilities
for poi in poi_coords:
    is_closest = (poi == best_poi)
    marker_color = 'red' if is_closest else 'lightgray'
    popup_text = f"<b>{poi['name']}</b><br>Status: " + ("<b>Nearest Facility</b>" if is_closest else "Available Facility")
    folium.Marker(
        [poi['lat'], poi['lon']], popup=popup_text, tooltip=poi['name'],
        icon=folium.Icon(color=marker_color, icon='plus')
    ).add_to(layer_facilities)

# Populate Layer 4: Standard Commute Route (Neon Blue)
std_route_coords = []
for u, v in zip(std_route[:-1], std_route[1:]):
    edge_data = G.get_edge_data(u, v)[0]
    if 'geometry' in edge_data:
        for point in edge_data['geometry'].coords:
            std_route_coords.append((point[1], point[0]))
    else:
        std_route_coords.append((G.nodes[u]['y'], G.nodes[u]['x']))
        std_route_coords.append((G.nodes[v]['y'], G.nodes[v]['x']))

folium.PolyLine(
    std_route_coords, color="#00D2FF", weight=5, opacity=0.9,
    tooltip=f"Standard Commute (Sintok Direction)<br>Drive Time: {std_time_minutes:.1f} mins"
).add_to(layer_std_route)
folium.Marker([std_end_lat, std_end_lon], popup="UUM Direction", icon=folium.Icon(color="blue", icon="info-sign")).add_to(layer_std_route)

# Populate Layer 5: Active Emergency Route (Red)
if best_emg_route:
    emg_route_coords = []
    for u, v in zip(best_emg_route[:-1], best_emg_route[1:]):
        edge_data = G.get_edge_data(u, v)[0]
        if 'geometry' in edge_data:
            for point in edge_data['geometry'].coords:
                emg_route_coords.append((point[1], point[0]))
        else:
            emg_route_coords.append((G.nodes[u]['y'], G.nodes[u]['x']))
            emg_route_coords.append((G.nodes[v]['y'], G.nodes[v]['x']))

    folium.PolyLine(
        emg_route_coords, color="#FF0000", weight=6, opacity=0.9,
        tooltip=f"EMERGENCY ROUTE<br>Target: {best_poi['name']}<br>Drive Time: {min_emg_time_minutes:.1f} mins"
    ).add_to(layer_emergency)

# User pin at incident scene
folium.Marker([start_lat, start_lon], popup="Reported Incident Location", icon=folium.Icon(color="orange", icon="user")).add_to(m)

# 7. Add Layers and Layer Control to Map
layer_base_roads.add_to(m)
layer_bottlenecks.add_to(m)
layer_facilities.add_to(m)
layer_std_route.add_to(m)
layer_emergency.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

output_file = "master_dashboard.html"
m.save(output_file)
print(f"7/7: Success! Integrated system saved as '{output_file}'.")