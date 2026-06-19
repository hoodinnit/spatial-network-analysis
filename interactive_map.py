import osmnx as ox
import networkx as nx
import folium
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 1. Fetch the local network
place_name = "Changlun, Kedah, Malaysia"
print("Fetching road network...")
G = ox.graph_from_address(place_name, dist=3000, network_type='drive')

# 2. Calculate Traffic Bottlenecks
print("Calculating bottlenecks...")
centrality = nx.betweenness_centrality(G, weight='length')
nx.set_node_attributes(G, centrality, 'centrality')

# 3. Convert Graph for Folium
print("Converting data for the web map...")
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

# 4. Initialize the Interactive Map
center_lat = gdf_nodes['y'].mean()
center_lon = gdf_nodes['x'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB dark_matter')

# 5. Plot the Nodes
print("Drawing the interactive map...")
max_cent = max(centrality.values()) 

for node_id, row in gdf_nodes.iterrows():
    cent = row['centrality']
    
    # Skip plotting dead-ends to keep the browser running smoothly
    if cent < (max_cent * 0.02):
        continue
        
    color = mcolors.to_hex(plt.cm.inferno(cent / max_cent))
    
    folium.CircleMarker(
        location=[row['y'], row['x']],
        radius= 3 + (cent / max_cent) * 8, 
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        tooltip=f"Intersection ID: {node_id}<br>Score: {cent:.4f}"
    ).add_to(m)

# 6. Save the HTML file
output_file = "changlun_interactive_map.html"
m.save(output_file)
print(f"Success! Map saved as: {output_file}")