import sys
import os
sys.path.append('../')

import graph as graph
import api_requests as api_requests

import matplotlib.pyplot as plt


# ******************************************************************************
# Creating the graph + A* algorithm
# ******************************************************************************


graph = graph.Graph()
api = api_requests.API_Requests()

graph.add_floor(930)
graph.add_floor(931)
graph.add_floor(932)

#start_node, end_node = int(sys.argv[1]), int(sys.argv[2])
start_node, end_node = 48, 280
came_from, _ = graph.a_star_algorithm(start_node, end_node)

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
            if node_info['isLift'] or node_info['isStair']:
                l1 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=BLUE, edgecolors='black', linewidths=1.5)
            else:
                l2 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=BLUE)
        else:
            l3 = ax[i].scatter(node_info['coord'][0], node_info['coord'][1], c=YELLOW)

        if node in graph.adj_list: 
            point1 = graph.node_infos[node]['coord']

            for other_node in graph.adj_list[node]:
                point2 = graph.node_infos[other_node[0]]['coord']

                #if other_node[0] not in graph.nodes_floor[i]:
                    #l4 = ax[i].scatter(point1[0], point1[1], c='black', s=15)

                ax[i].plot([point1[0], point2[0]], [point1[1], point2[1]], c='black', zorder=-5)

        if node in graph.outline_rooms:
            outline = graph.outline_rooms[node]
            ax[i].plot(outline[:,0], outline[:,1], c='gray', alpha=0.5, zorder=-10)

curr_node = end_node
while curr_node != start_node:
    next_node = came_from[curr_node]
    point1 = graph.node_infos[curr_node]['coord']
    point2 = graph.node_infos[next_node]['coord']

    for i in range(num_floors):
        if curr_node in graph.nodes_floor[i] and next_node in graph.nodes_floor[i]:
            ax[i].plot([point1[0], point2[0]], [point1[1], point2[1]], c=RED, linewidth=3)

    curr_node = next_node


l1.set_label('Lift / Stairs')
l2.set_label('Room')
l3.set_label('Door')

plt.tight_layout()

directory = 'outputs/'
if not os.path.exists(directory):
        os.makedirs(directory)

plt.savefig('outputs/pathfinding_floors.png', dpi=300)
#plt.show()