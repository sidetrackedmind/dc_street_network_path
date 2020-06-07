from __future__ import division
from flask import Flask, render_template, request, jsonify
import os
import geopandas as gpd
import json
import datetime
import geojson
import json
import osmnx as ox
import networkx as nx
import pandas as pd



app = Flask(__name__)

def get_route_path_from_graph(G, lat1,lon1, lat2, lon2):
    '''
    '''
    orig = ox.get_nearest_node(G, (lat1, lon1))
    dest = ox.get_nearest_node(G, (lat2, lon2))
    route = nx.shortest_path(G, orig, dest)
    lines = []
    edge_nodes = list(zip(route[:-1], route[1:]))
    for u, v in edge_nodes:
        # if there are parallel edges, select the shortest in length
        data = min(G.get_edge_data(u, v).values(), key=lambda x: x["length"])
        if 'geometry' in data:
            line_geom = data['geometry']
            lines.append(line_geom)
    if len(lines) > 0:
        route_lines = gpd.GeoDataFrame(pd.DataFrame(range(len(lines)), columns=['idx']), crs='EPSG:4326', geometry=lines)
    else:
        route_lines = gpd.GeoDataFrame()
    return route_lines

def get_route_path_from_edges(edges, G, lat1,lon1, lat2, lon2):
    '''
    '''
    orig = ox.get_nearest_node(G, (lat1, lon1))
    dest = ox.get_nearest_node(G, (lat2, lon2))
    route = nx.shortest_path(G, orig, dest)
    route_df = pd.DataFrame(route,columns=['u'])
    route_df.loc[:,'v'] = route_df.loc[:,'u'].shift(-1)
    route_df.dropna(axis=0,subset=['v'], inplace=True)
    route_line_edges = pd.merge(edges, route_df, on=['u','v'])
    return route_line_edges

filepath = '/home/work/data/dc_boundary_network.graphml'

edge_filepath = '/home/work/data/osm_network_bus_extent_simplified4.json'

G = ox.load_graphml(filepath)

edges = gpd.read_file(edge_filepath)

#hexbins = gpd.read_file("webmap_files/hexbin_grid_level_9_w_elevation_from_dem.shp")


#hexbins_dict = json.loads(hexbins.to_json())

#hexbins_dict['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }}


@app.route('/', methods=['GET','POST'])
def index():

    return render_template('index.html'
                            )

@app.route('/route', methods=['GET','POST'])
def route_internal():
    pts_data = request.json
    print(pts_data)
    lat1 = pts_data['lat1']
    lon1 = pts_data['lon1']
    lat2 = pts_data['lat2']
    lon2 = pts_data['lon2']
    print(f"points to route lat1 {lat1} lon1 {lon1} lat2 {lat2} lon2 {lon2}")
    # route_lines = get_route_path_from_graph(G, lat1,lon1, lat2, lon2)

    route_lines = get_route_path_from_edges(edges, G, lat1,lon1, lat2, lon2)

    route_lines_dict = json.loads(route_lines.to_json())

    route_lines_dict["crs"] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }}

    #print(route_lines_dict)

    route_lines_json = json.dumps(route_lines_dict)
    #print(route_lines_json)

    return jsonify({'route_lines_dict':route_lines_json
                    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=True)