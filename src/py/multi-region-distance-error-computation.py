import os
import sys
import subprocess
import geopandas as gpd
import time
import yaml
import igraph as ig
import pandas as pd
from sklearn.neighbors import KDTree
from tqdm import tqdm
import numpy as np


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')

with open(ROOT_dir + '/lib/regions.yaml') as f:
    region_manager = yaml.load(f, Loader=yaml.FullLoader)

import lib.helpers as helpers


class MultiRegionNetworkDistance:
    def __init__(self, region=None, runid=None):
        if not region:
            raise Exception("A valid region must be specified!")
        if not runid:
            raise Exception("A valid runid must be specified!")
        self.region = region
        self.boundary = None
        self.osm_path = ROOT_dir + f'/dbs/{region}/osm/drive.shp'
        self.G = None
        self.nodes = None
        self.tree = None
        self.trip_path = ROOT_dir + f'/dbs/{region}/visits/visits_{runid}_trips_dom.csv'
        self.trips = None
        self.trip_path_new = ROOT_dir + f'/dbs/{region}/visits/visits_{runid}_trips_dom_network.csv'

    def boundary_loader(self):
        # The boundary to use when downloading drive networks
        metric_epsg = region_manager[self.region]['metric_epsg']
        zone_id = region_manager[self.region]['zone_id']
        zones_path = region_manager[self.region]['zones_path']
        zones = gpd.read_file(ROOT_dir + zones_path)
        zones = zones.loc[zones[zone_id].notnull()]
        zones = zones.rename(columns={zone_id: "zone"})
        zones.zone = zones.zone.astype(int)
        zones = zones.loc[zones.geometry.notnull()].to_crs(metric_epsg)
        if self.region != 'mexico':
            self.boundary = zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")
        else:
            self.boundary = zones.to_crs("EPSG:4326")
        print(self.region, 'boundary proccessed.')

    def igraph_creator(self):
        # Load downloaded network
        G = gpd.read_file(self.osm_path)

        # Get the start node and end node of each road segment
        G['u_coords_x'] = G.apply(lambda x: x['geometry'].coords[0][0], axis=1)
        G['u_coords_y'] = G.apply(lambda x: x['geometry'].coords[0][1], axis=1)

        G['v_coords_x'] = G.apply(lambda x: x['geometry'].coords[-1][0], axis=1)
        G['v_coords_y'] = G.apply(lambda x: x['geometry'].coords[-1][1], axis=1)

        # Create network
        network = []
        for x in G[['u', 'v', 'osm_id', 'length', 'oneway']].values:
            if x[4] == 'False':
                network.append(tuple([x[0], x[1], x[2], float(x[3])/1000]))
            else:
                network.append(tuple([x[0], x[1], x[2], float(x[3])/1000]))
                network.append(tuple([x[1], x[0], x[2], float(x[3])/1000]))

        G_r = ig.Graph.TupleList(network, directed=True, vertex_name_attr='node_id', edge_attrs=['edge_id', 'length'])
        self.G = G_r.components().giant()

        # Create nodes and nodes-based KD tree
        node_dict = {self.G.vs[x]['node_id']: x for x in range(0, len(self.G.vs))}

        df_nodes = pd.concat([G.loc[:, ['u', 'u_coords_x', 'u_coords_y']].rename(columns={'u': 'node',
                                                                                          'u_coords_x': 'x',
                                                                                          'u_coords_y': 'y'}),
                              G.loc[:, ['v', 'v_coords_x', 'v_coords_y']].rename(columns={'v': 'node',
                                                                                          'v_coords_x': 'x',
                                                                                          'v_coords_y': 'y'})])
        df_nodes = df_nodes.drop_duplicates(subset=['node'])
        df_nodes.loc[:, 'node_id'] = df_nodes.loc[:, 'node'].apply(lambda x: node_dict[x])
        df_nodes = df_nodes.dropna().reset_index(drop=True)
        df_nodes.loc[:, 'node_id'] = df_nodes.loc[:, 'node_id'].astype(int)
        nodes_in_graph = list(node_dict.keys())
        self.nodes = df_nodes.loc[df_nodes['node'].isin(nodes_in_graph), :]

        # Prepare KD-tree for finding the nearest node in the graph
        self.tree = KDTree(self.nodes[["y", "x"]], metric="euclidean")
        print(self.region, 'graph, nodes, and tree created.')

    def trip_loader(self):
        df_trips = pd.read_csv(self.trip_path)
        self.trips = helpers.filter_trips(df=df_trips, boundary=self.boundary)
        self.trips = self.trips.loc[self.trips['distance'] > 0.1, :]

    def routing(self):
        # Get the list of unique visits
        df_visits = pd.concat([self.trips.loc[:, ['longitude', 'latitude']],
                               self.trips.loc[:, ['longitude_d', 'latitude_d']].rename(
                                   columns={'longitude_d': 'longitude',
                                            'latitude_d': 'latitude'})])
        df_visits = df_visits.drop_duplicates(subset=['longitude', 'latitude'])
        df_visits["tree_node"] = df_visits.apply(lambda row: self.tree.query([(row['latitude'], row['longitude'])],
                                                                                      k=1, return_distance=False)[0][0],
                                                          axis=1)
        # Find the nearest network node to the unique visits
        df_visits.loc[:, 'G_node'] = df_visits["tree_node"].apply(lambda x: self.nodes.iloc[int(x)].node_id)

        # Map the G_node (node_id in network) to trips
        G_node_dict = {(row['latitude'], row['longitude']): row['G_node'] for _, row in df_visits.iterrows()}
        self.trips.loc[:, 'origin_node'] = self.trips.apply(
            lambda row: G_node_dict[(row['latitude'], row['longitude'])], axis=1)
        self.trips.loc[:, 'destination_node'] = self.trips.apply(
            lambda row: G_node_dict[(row['latitude_d'], row['longitude_d'])], axis=1)
        self.trips.loc[:, 'origin_node'] = self.trips.loc[:, 'origin_node'].astype(int)
        self.trips.loc[:, 'destination_node'] = self.trips.loc[:, 'destination_node'].astype(int)

        # Calculate network distances and travel times between places (node_ids)
        node_list_routing = list(df_visits['G_node'].unique())
        distance_network = self.G.shortest_paths_dijkstra(source=node_list_routing,
                                                          target=node_list_routing,
                                                          weights="length")
        dis_net = np.matrix(distance_network)
        idx = [node_list_routing.index(id) for id in self.trips['origin_node'].values]
        idy = [node_list_routing.index(id) for id in self.trips['destination_node'].values]
        self.trips.loc[:, 'distance_network'] = dis_net[idx, idy].tolist()[0]
        print(self.region, 'network distance added.')


def network_distance(region=None, runid=None):
    # Start timing the code
    start_time = time.time()
    dl = MultiRegionNetworkDistance(region=region, runid=runid)
    if not os.path.exists(dl.trip_path_new):
        dl.boundary_loader()
        dl.igraph_creator()
        dl.trip_loader()
        dl.routing()
        dl.trips.to_csv(dl.trip_path_new, index=False)
    else:
        print(region, "has network distances ready. Skip processing")
    print(region, "is done. Elapsed time was %g seconds" % (time.time() - start_time))


if __name__ == '__main__':
    region_list = ['surabaya', 'stpertersburg', 'barcelona', 'capetown', 'cebu', 'guadalajara',
                   'johannesburg', 'kualalumpur', 'madrid', 'nairobi']
    runid = 7

    for region in tqdm(region_list, desc='Adding network distance'):
        print(region)
        try:
            network_distance(region=region, runid=runid)
        except:
            print(region, 'failed.')
            pass

