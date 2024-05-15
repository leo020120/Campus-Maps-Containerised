'''

This file contains necessary classes and functions for in-building navigation (navigation between buildings has not been
implemented). 

We build up a graph network on a floor by floor basis, then connect adjacent floors. Most of it should be standard 
implementations, for example, for the A* algorithm. Non-standard things include the way we connect doors to rooms and 
some subtleties in the way floors are connected via stairs or lifts and how this impacts the weights of the edges.

Some examples of how to use the graph class can be found in the examples folder:
    - show_node_ids.py: shows the node ids on a floor
    - show_graph_building.py: shows the graph of a building
    - pathfinding_floors.py: demonstrates pathfinding inside a building

'''

from queue import PriorityQueue
import json
import copy
import numpy as np
import matplotlib.pyplot as plt

import api_requests as api_requests


class Graph:

    def __init__(self):
        '''Initialises the graph.

        The graph is mainly represented by a set of nodes and an adjacency list.

        Additionally, the graph stores information about the nodes and the outline of the rooms, as well as a list of 
        sets where sets are separated by floors.
        '''

        self.nodes = set() # {1234, 5678, ...}
        self.nodes_floor = [] # [set(), set(), ...]

        self.adj_list = {} # {1234: {(5678,1), (9012,1), ...}, ...}

        self.node_infos = {} # {1234: {'coord': [x, y], 'type': 'room'}, ...}
        self.outline_rooms = {} # {1234: [[x1, y1], [x2, y2], ...], ...}

        self.type_filter = {'Cavity', 'Cleaners Cupboard', None, 'Riser'}


    def add_building(self, building_id: int):
        api = api_requests.API_Requests()
        floors = api.get_building_id_floor(building_id)

        for floor in floors:
            self.add_floor(floor['id'])


    def add_floor(self, floor_id: int):
        '''Creates a graph for a floor and adds it to the graph of the building.

        Using the data from the Pythagoras API, the function creates room and floor nodes and adds them to the graph.
        Furthermore it connects the floor that is being added to the previous floor (This means they have to be
        initialised in order).

        Args:
            floor_id (int): The id of the floor that is being added to the graph.
        '''

        api = api_requests.API_Requests()
        data_rooms = api.get_floor_id_workspace_info(floor_id)
        data_walls = api.get_floor_id_info(floor_id)['wallInfos']

        nodes, nodes_infos, outline_rooms = self.get_nodes_floor(data_rooms, data_walls)

        self.nodes.update(nodes)
        self.nodes_floor.append(nodes)
        self.node_infos.update(nodes_infos)
        self.outline_rooms.update(outline_rooms)

        adj_list = self.get_adj_list_floor(nodes, outline_rooms)
        adj_list = self.compute_special_weights(adj_list)

        self.adj_list.update(adj_list)

        if len(self.nodes_floor) > 1:
            self.connect_floors(self.nodes_floor[-2], self.nodes_floor[-1])

    
    def get_adj_list_floor(self, nodes: list, outline_rooms: list, connect_doors: bool = False):
        '''Computing the adjacency list for a floor.

        Since we distinguish between room nodes and door nodes, we have the following rules for connecting nodes:
        - A room node can only be connected to a door node, and vice versa.
        - The distance between the door node and the wall of a particular room has to be smaller than 0.5m.
        - The door node has to be in front of the wall of the room (this is being checked by the two dot products in
        the if statement).

        Args:
            nodes (list): A list of all the nodes on the floor.
            outline_rooms (list): A list of all the outlines of the rooms on the floor.

        Returns:
            dict: The adjacency list of the floor.
        '''
        adj_list = {}

        for node in nodes:
            if self.node_infos[node]['type'] == 'door': continue

            for i, point in enumerate(outline_rooms[node]):
                next_point = outline_rooms[node][(i + 1) % len(outline_rooms[node])]
                vec_a = next_point - point

                for other_node in nodes:
                    if self.node_infos[other_node]['type'] == 'room': continue

                    vec_b = self.node_infos[other_node]['coord'] - point
                    h = np.linalg.norm(np.cross(vec_a, vec_b)) / np.linalg.norm(vec_a)

                    if h < 0.5 and np.dot(vec_a, vec_b) > 0 and np.dot(vec_b, vec_b) < np.dot(vec_a, vec_a):
                        if node not in adj_list:
                            adj_list[node] = set()
                        if other_node not in adj_list:
                            adj_list[other_node] = set()

                        distance = np.linalg.norm(self.node_infos[node]['coord'] - self.node_infos[other_node]['coord'])

                        adj_list[node].add((other_node, self.weight_func(distance)))
                        adj_list[other_node].add((node, self.weight_func(distance)))

            if connect_doors and node in adj_list: 
                for door_node in adj_list[node]:
                    for other_door_node in adj_list[node]:
                        if door_node == other_door_node: continue
                        adj_list[door_node[0]].add((other_door_node[0], 1))
                        adj_list[other_door_node[0]].add((door_node[0], 1))

        return adj_list

    
    def compute_special_weights(self, adj_list: dict):
        '''Computes weights for special edges.

        The function computes the weights for the edges between the lift and the doors on the floor. This is to emulate
        the waiting time for the lift.

        Complexity Estimate: O(n) where n is the number of lifts on the floor.

        Args:
            adj_list (dict): The adjacency list of the floor.

        Returns:
            dict: The adjacency list of the floor with the special weights.
        '''
        adj_list = copy.deepcopy(adj_list)
        lift_waiting_time = 15

        for node in adj_list:
            if not self.node_infos[node]['isLift']: continue

            for connecting_node, _ in adj_list[node]:
                if not self.node_infos[connecting_node]['type'] == 'door': continue

                adj_list[node].remove((connecting_node, _))
                adj_list[node].add((connecting_node, lift_waiting_time))

                for elem in adj_list[connecting_node]:
                    if elem[0] == node:
                        adj_list[connecting_node].remove(elem)
                        adj_list[connecting_node].add((node, lift_waiting_time))
                        break

        return adj_list


    def get_nodes_floor(self, data_rooms: list, data_walls: list):
        '''Gets set of nodes and information about the nodes on a floor.

        Using the data from Pythagoras, rooms and doors are added to the graph. Additional information about the nodes
        is stored in a dictionary.

        Args:
            data_rooms (list): A list of all the rooms on the floor.
            data_walls (list): A list of all the walls on the floor.

        Returns:
            tuple: A tuple containing the set of nodes, the dictionary of node information and the dictionary of the
            room outlines.
        '''

        nodes = set() # {1234, 5678, ...}
        nodes_infos = {} # {1234: {'coord': [x, y], 'type': 'room'}, ...}
        outline_rooms = {} # {1234: [[x1, y1], [x2, y2], ...], ...}

        for room in data_rooms:
            if room['typeName'] in self.type_filter: continue

            i = len(self.nodes) + len(nodes) + 1
            nodes.add(i)
            nodes_infos[i] = {
                'coord': np.array([room['utilityCoord']['x'], room['utilityCoord']['y']]),
                'type': 'room',
                'typeName': room['typeName'],
                'isLift': room['typeName'] == 'Lift',
                'isStair': room['typeName'] == 'Stairs'
            }

            outline_rooms[i] = self.get_outline(room)

        for wall in data_walls:
            for door in wall['doorInfos']:
                i = len(self.nodes) + len(nodes) + 1

                nodes.add(i)
                nodes_infos[i] = {
                    'coord': np.array([door['x'], door['y']]),
                    'type': 'door',
                    'typeName': room['typeName'],
                    'isLift': False,
                    'isStair': False
                }

        return nodes, nodes_infos, outline_rooms


    def get_outline(self, room: dict):
        outline = []

        for point in room['outline']['coords']:
            outline.append([
                point['x'], point['y']
            ])

        return np.array(outline)

    
    def connect_floors(self, prev_floor: set, curr_floor: set):
        '''Connects two floors together.

        This function connects the previous floor to the current floor. It does this by checking if there are any
        stairs or lifts on the previous floor and the current floor. If there are, it checks if they are close to each
        other. If they are, they are connected.

        Based on their type (stairs or lift), a different weight is assigned to the edge.

        Also, this only makes sense if the floors inputted actually connect, there is no additional check if floors are
        actually on top of each other.

        Args:
            prev_floor (set): The set of nodes on the previous floor.
            curr_floor (set): The set of nodes on the current floor.
        '''

        for node in prev_floor:
            if not self.node_infos[node]['isStair'] and not self.node_infos[node]['isLift']: continue

            coord = self.node_infos[node]['coord']

            for other_node in curr_floor:
                if not self.node_infos[other_node]['isStair'] and not self.node_infos[other_node]['isLift']: continue

                other_coord = self.node_infos[other_node]['coord']

                if np.linalg.norm(coord - other_coord) < 5:
                    if node not in self.adj_list:
                        self.adj_list[node] = set()
                    if other_node not in self.adj_list:
                        self.adj_list[other_node] = set()
                    
                    if self.node_infos[node]['isStair'] and self.node_infos[other_node]['isStair']:
                        self.adj_list[node].add((other_node, 15))
                        self.adj_list[other_node].add((node, 15))
                    elif self.node_infos[node]['isLift'] and self.node_infos[other_node]['isLift']:
                        self.adj_list[node].add((other_node, 2)) 
                        self.adj_list[other_node].add((node, 2))


    def weight_func(self, distance: float) -> float:
        return distance / 1.4 # 1.4 m/s walking speed


    def a_star_algorithm(self, start_node: int, end_node: int):
        '''A* algorithm to find the shortest path between two nodes.

        Standard implementation of the A* algorithm. It uses a priority queue to keep track of the nodes to visit. The
        priority is based on the cost of the path so far and the heuristic of the node.

        Args:
            start_node (int): The node to start from.
            end_node (int): The node to end at.

        Returns:
            tuple: A tuple containing the path and the cost of the path.
        '''

        frontier = PriorityQueue()
        frontier.put((0, start_node))

        came_from = dict()
        cost_so_far = dict()

        came_from[start_node] = None
        cost_so_far[start_node] = 0

        while not frontier.empty():
            current_node = frontier.get()[1]

            if current_node == end_node:
                print('Found end node')
                break

            for next_node, weight in self.get_neighbors(current_node):
                new_cost = cost_so_far[current_node] + weight

                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.h(next_node, end_node)
                    frontier.put((priority, next_node))
                    came_from[next_node] = current_node

        return came_from, cost_so_far

        
    def h(self, current_node: int, end_node: int) -> float:
        '''Heuristic function for the A* algorithm.

        This heuristic function is based on the euclidean distance between two nodes. It also takes into account the
        difference in floors between the two nodes. This is done by adding 5 to the distance for every floor difference.

        Args:
            current_node (int): The current node.
            end_node (int): The end node.

        Returns:
            float: The heuristic value.
        '''

        # TODO: check if this is quicker than adding an entry for floor in node_infos

        for i, floor in enumerate(self.nodes_floor):
            if current_node in floor:
                current_floor = i
            if end_node in floor:
                end_floor = i

        floor_corr = (end_floor - current_floor) * 5

        return np.linalg.norm(self.node_infos[current_node]['coord'] - self.node_infos[end_node]['coord']) + floor_corr


    def get_neighbors(self, v):
        if v in self.adj_list:
            return self.adj_list[v]
        else:
            return []

    
    def save_graph(self, output_path: str = 'outputs/graph.json'):
        with open(output_path, 'w') as f:
            json.dump(self.adj_list, f)