import sys
import os
sys.path.append('../')

import graph as graph
import api_requests as api_requests

import matplotlib.pyplot as plt


# ******************************************************************************
# Creating graph
# ******************************************************************************


graph = graph.Graph()
api = api_requests.API_Requests()

# Retrieving building ID, TODO: Add to Graph class
building_name = 'BLACKETT'
building_id = None
buildings = api.get_building()
for building in buildings:
    if building['name'] == building_name:
        building_id = building['id']
        break

assert building_id is not None, "Error: Building not found"

# Creating graph
graph.add_building(building_id)
num_floors = len(graph.nodes_floor)
num_floors = 4


# ******************************************************************************
# Plotting
# ******************************************************************************

RED = '#F73859'
YELLOW = '#FFC764'
BLUE = '#6886C5'
DARK_BLUE = '#404B69'
GREEN = '#06D6A0'

fig, ax = plt.subplots(num_floors, 1, figsize=(10, 10*num_floors))

for i in range(num_floors):

    # Plotting nodes
    for node in graph.nodes_floor[i]:
        node_info = graph.node_infos[node]

        if node_info['type'] == 'room':
            if node_info['isLift'] or node_info['isStair']:
                l1 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=BLUE, edgecolors='black', linewidths=1.5) 
            else:
                l2 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=BLUE)
        else:
            l3 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=YELLOW)

        # Plotting room outlines
        if node in graph.outline_rooms:
            outline = graph.outline_rooms[node]
            ax[i].plot(outline[:,0], outline[:,1], c='gray', alpha=0.5, zorder=-10)

        # Plotting edges
        if node not in graph.adj_list: continue
        point1 = graph.node_infos[node]['coord']

        for other_node in graph.adj_list[node]:
            point2 = graph.node_infos[other_node[0]]['coord']

            # if other_node[0] not in graph.nodes_floor[i]:
                # l4 = ax[i].scatter(point1[0], point1[1], c='black', s=15)

            ax[i].plot([point1[0], point2[0]], [point1[1], point2[1]], c='black')

    if i == 3:
        break


ax[0].legend()
plt.tight_layout()

directory = 'outputs/'
if not os.path.exists(directory):
        os.makedirs(directory)

plt.savefig('outputs/graph_building3.png', dpi=400)
#plt.show()
