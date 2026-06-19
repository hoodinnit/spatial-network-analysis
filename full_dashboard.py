import osmnx as ox
import networkx as nx
import folium
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 1. Fetch the local network (3km radius around Changlun)
place_name = "Changlun, Kedah, Malaysia"
print("1/5: Loading unified road network...")
G = ox.graph_from_address(place_name, dist=3000, network_type='drive')

# 2. Calculate Traffic Bottlenecks (Betweenness Centrality)
print("2/5: Calculating network traffic bottlenecks...")
centrality = nx.betweenness_centrality(G, weight='length')
nx.set_node_attributes(G, centrality, 'centrality')

# 3. Calculate Optimized Route (Dijkstra's Algorithm)
print("3/5: Calculating optimized route using Dijkstra...")
start_lat, start_lon = 6.4315, 100.4285  # Changlun center
end_lat, end_lon = 6.4450, 100.4450      # Sintok/UUM direction

start_node = ox.nearest_nodes(G, X=start_lon, Y=start_lat)
end_node = ox.nearest_nodes(G, X=end_lon, Y=end_lat)

optimized_route = nx.shortest_path(G, source=start_node, target=end_node, weight='length')
route_length = nx.shortest_path_length(G, source=start_node, target=end_node, weight='length')

# 4. Initialize the Map and Feature Groups (Layers)
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
center_lat = gdf_nodes['y'].mean()
center_lon = gdf_nodes['x'].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB dark_matter')

# Create separate layers so the user can toggle them on/off
layer_base_roads = folium.FeatureGroup(name="Base Road Network", show=True)
layer_bottlenecks = folium.FeatureGroup(name="Traffic Bottlenecks (Heatmap)", show=False)
layer_routing = folium.FeatureGroup(name="Optimized Routing Path", show=True)

# 5. Populate Layer 1: Base Roads
print("4/5: Drawing layout layers...")
for _, edge in gdf_edges.iterrows():
    coordinates = [(point[1], point[0]) for point in edge['geometry'].coords] if 'geometry' in edge else []
    if coordinates:
        folium.PolyLine(coordinates, color="#333333", weight=1.5, opacity=0.5).add_to(layer_base_roads)

# Populate Layer 2: Bottlenecks Heatmap
max_cent = max(centrality.values())
for node_id, row in gdf_nodes.iterrows():
    cent = row['centrality']
    if cent < (max_cent * 0.02):
        continue
    color = mcolors.to_hex(plt.cm.inferno(cent / max_cent))
    folium.CircleMarker(
        location=[row['y'], row['x']],
        radius=3 + (cent / max_cent) * 8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        tooltip=f"Intersection: {node_id}<br>Score: {cent:.4f}"
    ).add_to(layer_bottlenecks)

# Populate Layer 3: Optimized Dijkstra Route
route_coordinates = []
for u, v in zip(optimized_route[:-1], optimized_route[1:]):
    edge_data = G.get_edge_data(u, v)[0]
    if 'geometry' in edge_data:
        for point in edge_data['geometry'].coords:
            route_coordinates.append((point[1], point[0]))
    else:
        route_coordinates.append((G.nodes[u]['y'], G.nodes[u]['x']))
        route_coordinates.append((G.nodes[v]['y'], G.nodes[v]['x']))

folium.PolyLine(
    route_coordinates, 
    color="#00D2FF", 
    weight=5, 
    opacity=0.9,
    tooltip=f"Optimized Route ({route_length/1000:.2f} km)"
).add_to(layer_routing)

# Add route markers directly to the routing layer
folium.Marker([start_lat, start_lon], popup="Start: Changlun Center", icon=folium.Icon(color="green")).add_to(layer_routing)
folium.Marker([end_lat, end_lon], popup="End: Sintok/UUM Direction", icon=folium.Icon(color="red")).add_to(layer_routing)

# 6. Bind layers to map and add the Control Menu
layer_base_roads.add_to(m)
layer_bottlenecks.add_to(m)
layer_routing.add_to(m)

# This adds the interactive toggle box in the top-right corner
folium.LayerControl(collapsed=False).add_to(m)

# 7. Save to HTML
output_file = "final_dashboard.html"
m.save(output_file)
print(f"5/5: Success! Combined dashboard saved as '{output_file}'.")