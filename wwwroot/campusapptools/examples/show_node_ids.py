import sys
import os
sys.path.append('../')

import api_requests as api_requests
import graph as graph

import matplotlib.pyplot as plt


# ******************************************************************************
# Creating the graph
# ******************************************************************************


graph = graph.Graph() # Create graph object

# Adding floors to graph by floor ID
graph.add_floor(930)
graph.add_floor(931)
graph.add_floor(932)

num_floors = len(graph.nodes_floor)


# ******************************************************************************
# Plotting
# ******************************************************************************


RED = '#F73859'
YELLOW = '#FFC764'
BLUE = '#6886C5'
DARK_BLUE = '#404B69'
GREEN = '#06D6A0'


fig, ax = plt.subplots(num_floors, 1, figsize=(10, 8*num_floors))

for i in range(num_floors):

    for node in graph.nodes_floor[i]:
        node_info = graph.node_infos[node]

        if node_info['type'] == 'room':
            if node_info['isLift'] or node_info['isStair']: # Lifts and stairs, ie. connections to other floors
                l1 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=BLUE, edgecolors='black', linewidths=1.5)
            else: # normal room
                l2 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=BLUE)
        else: # doors
            l3 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=YELLOW)

        #ax[i].text(node_info['coord'][0], node_info['coord'][1], node_info['typeName'], fontsize=8, zorder=10) # Type of node
        ax[i].text(node_info['coord'][0], node_info['coord'][1], node, fontsize=8, zorder=10) # Node ID

        # Plotting room outlines
        if node in graph.outline_rooms:
            outline = graph.outline_rooms[node]
            ax[i].plot(outline[:,0], outline[:,1], c='gray', alpha=0.5, zorder=-10)

    
plt.tight_layout()

directory = 'outputs/'
if not os.path.exists(directory):
        os.makedirs(directory)

plt.savefig('outputs/node_ids.png', dpi=400)
#plt.show()
