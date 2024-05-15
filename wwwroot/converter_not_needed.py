'''
This file contains the code for converting the data retrieved from the API into 3D models.

The main classes are:
    - Scene: A scene is a collection of objects. This class is used to export the scene into a glb file.
    - Object: A general object class for all objects.
    - ExtrudedPolygon: A class for all objects without holes (e.g. columns, floors, ...).
    - CuboidWithHole: A cuboid with a hole in it. Used for things such as wall elements that have windows or doors.

The main functions are:
    - create_floor: Creates outsides walls, inside walls, and floors separately for each floor/level.
    - create_building: Retrives floors of a building and calls create_floor for each floor.

    
Current Implementation:

    We create all floors separately in such a way that their respective origin is on the floor itself. If one were to simply
import every floor into a 3D modelling software, they would be stacked on top of each other at about the same position.
    As can be seen in the function create_floor, we have an offset parameter. This gives an alternatve way of positioning
the floors and buildings. Testing has shown that there is no apparent automatic way to position the floors correctly.
Either one implements the hand-tuned offsets into the 3D models (using the offset parameter) or one positions the floors
after they have been imported into unity. The latter seems preferable as it allows for more flexibility. Both methods rely on
manually fine tuning positions in some way.

The main function in this script best demonstrates how to use the classes and functions.
'''

import warnings
import time
import json

from api_requests import API_Requests

import trimesh
import shapely
import numpy as np


# Not needed in current implementation:
# ------------------------------------------------------------------------------
# RADIUS_EARTH = 6365100 # London, metres
# LONGITUDE_QT = -0.17683675319517533 # Queens Tower
# LATITUDE_QT = 51.49834757779674 # Queens Tower
# FLOOR_ORDER = ['B', 'LM', 'LG', 'G', 'GP', 'GMP', 'UG', '0', '00', '0M', '01', '01M', '02', '02M', '03', '03M', '04', '04M', '05', '05M', '06', '06M', '07', '07M', '08', '08M', '09', '09M', '10', '10M', '11', '11M', '12', '12M', '13', '13M', '14', '14M', '15', '15M', '16', '16M', 'R', 'RF', 'U']
# ------------------------------------------------------------------------------

SOUTH_KEN_LIGHT = [
    'ABDUS SALAM LIBRARY', # done
    'ACE EXTENSION', # done
    'BLACKETT', # done
    'BESSEMER', # done
    'BONE', # done
    'BUSINESS SCHOOL', # done
    'CITY AND GUILDS', # done
    'ELECTRICAL ENGINEERING', # cannot find it
    'DYSON', # done
    'FACULTY BUILDING', # done
    'FLOWERS', # looks weird (as if rotated the wrong way - another 180 around up axis) 
    'HUXLEY', # done
    'RODERIC HILL', # done
    'ROYAL SCHOOL OF MINES', # done - looks weird 
    'SHERFIELD', # done
    'SIR ALEXANDER FLEMING BUILDING', # done
    'SIR ERNST CHAIN', # done
    'SKEMPTON BUILDING', # done
    'WILLIAM PENNEY LABORATORY', # unsure where to put this
    'CHEMISTRY', # done
]


class Scene:
    def __init__(self, objects: list) -> None:
        self.objects = objects
        self.scene = trimesh.scene.scene.Scene()

        for obj in self.objects:
            self.scene.add_geometry({f'{obj.name}': obj.mesh})

    def export(self, filename: str) -> None:
        trimesh.exchange.export.export_scene(self.scene, filename, file_type="glb")


class Object:
    def __init__(self, mesh: trimesh.base.Trimesh, name: str, offset: list[float] = [0,0,0,0]) -> None:
        '''General object class for all objects.

        Args:
            mesh (trimesh.base.Trimesh): Mesh of the object.
            name (str): Name of the object.
            offset (list[float], optional): Offset to apply to the object. Format is [x,y,z,angle around z]. Used for global positioning.
        '''
        self.name = name
        self.mesh = mesh
        self.tags = {} # internal/external wall, ...

        x, y, z, angle = offset
        transformation_matrix = np.array([
            [np.cos(angle), -np.sin(angle), 0, x],
            [np.sin(angle), np.cos(angle), 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1]
        ])
        self.mesh.apply_transform(transformation_matrix)

    def export(self, filename: str) -> None:
        trimesh.exchange.export.export_mesh(self.mesh, filename, file_type="glb")


class ExtrudedPolygon(Object):
    def __init__(self, vertices_2d: list, height: float, name: str, offset: list[float] = [0,0,0,0]) -> None:
        self.vertices_2d = vertices_2d
        self.height = height

        shape = shapely.geometry.Polygon(vertices_2d)
        mesh = trimesh.creation.extrude_polygon(shape, height)

        super().__init__(mesh, name, offset)

    
class CuboidWithHole(Object):
    def __init__(self, exterior_points: list, interior_points: list, position: list[float], angle: float, thickness: float, name: str, offset: list[float] = [0,0,0,0]) -> None:
        '''
        One of two types of different objects. The cuboids with holes, for things such as windows or doors, are created
        on their side (x-z plane) and then rotated into xyz. This is so we can make use of the extrude_polygon function.

        Args:
            exterior_points (list): List of points for the exterior of the cuboid. Dimensions are (4, 2). 
            interior_points (list): List of points for the interior of the cuboid. Dimensions are (n, 4, 2) where n is the number of holes.
            position (list[float]): Position of the cuboid.
            angle (float): Angle to rotate the cuboid around.
            thickness (float): Thickness of the cuboid.
            name (str): Name of the cuboid.
            offset (list[float], optional): Offset to apply to the cuboid. Format is [x,y,z,angle around z].
        '''

        self.exterior_points = exterior_points # (4, 2)
        self.interior_points = interior_points # (n, 4, 2) where n is the number of holes

        polygon = shapely.geometry.Polygon(exterior_points, interior_points)

        # Transformation matrix to rotate the cuboid into xyz and position it. 
        # Consists of, transformation_matrix[0:2][0:2] = positioning_rotation * flip_rotation_into_xyz.
        transformation_matrix = np.array([
            [np.cos(angle), 0, -np.sin(angle), position[0]],
            [np.sin(angle), 0, np.cos(angle), position[1]],
            [0, 1, 0, position[2]],
            [0, 0, 0, 1]
        ])

        mesh = trimesh.creation.extrude_polygon(polygon, thickness)
        mesh.apply_transform(transformation_matrix)

        super().__init__(mesh, name, offset)


class Column(ExtrudedPolygon):
    def __init__(self, data: dict, name: str = 'column', offset: list[float] = [0,0,0,0]) -> None:
        vertices_2d = []

        for vertex in data['outline']['coords']:
            vertices_2d.append([vertex['x'], vertex['y']])

        height = data['height'] + 0.2 if data['height'] is not None else 3.2 # 0.2 is the height of the base/floor

        super().__init__(vertices_2d, height, name, offset)


class Floor(ExtrudedPolygon):
    def __init__(self, data: dict, name: str = 'room', offset: list[float] = [0,0,0,0]) -> None:
        vertices_2d = []

        for vertex in data['outline']['coords']:
            vertices_2d.append([vertex['x'], vertex['y']])

        height = 0.2
        name = f'room_{data["id"]}'

        super().__init__(vertices_2d, height, name, offset)


class Wall(CuboidWithHole):
    def __init__(self, data: dict, name: str = 'wall', offset: list[float] = [0,0,0,0]) -> None:
        '''Creates a wall object from the data retrieved from the API.

        Walls are created on the x-z plane, with the y-axis being the height, then they get rotated into xyz. This is so
        we can make use of the extrude_polygon function from trimesh.

        Args:
            data (dict): Data retrieved from the API.
            name (str, optional): Name of the wall. Defaults to 'wall'.
            offset (list[float], optional): Offset to apply to the wall. Format is [x,y,z,angle around z].
        '''

        x0, y0 = data['startX'], data['startY']
        x1, y1 = data['endX'], data['endY']

        height = data['height'] + 0.2 if data['height'] is not None else 3.2
        thickness = data['typeThickness']
        length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)

        angle = np.arctan2(y1 - y0, x1 - x0)
        
        # Basis Vectors of the wall
        e1 = np.array([np.cos(angle), np.sin(angle), 0])
        e2 = np.array([np.cos(angle + np.pi/2), np.sin(angle + np.pi/2), 0])
        e3 = np.array([0, 0, 1])

        postition = np.array([x0, y0, 0]) - thickness*e2/2

        exterior_points = [
            [0, 0], # bottom left
            [length, 0], # bottom right
            [length, height], # top right
            [0, height] # top left
        ]

        interior_points = [] 
        for hole in data['doorInfos'] + data['windowInfos']:
            margin = 0.05 # Fixes rendering issues (from, for example, floating point errors)

            h_x, h_y = hole['x'] - x0, hole['y'] - y0 # x, y
            h_w, h_h = hole['typeWidth'], hole['typeHeight'] # width, height
            h_t = hole['typeThreshold'] + 0.2 # threshold

            rel_pos = np.sqrt(h_x**2 + h_y**2)

            interior_points.append([
                [rel_pos - h_w/2 + margin, h_t], # bottom left
                [rel_pos + h_w/2 - margin, h_t], # bottom right
                [rel_pos + h_w/2 - margin, h_t + h_h - margin], # top right
                [rel_pos - h_w/2 + margin, h_t + h_h - margin] # top left
            ])

        super().__init__(exterior_points, interior_points, postition, angle, thickness, name, offset)
        
        if 'I' in data['typeName']:
            self.tags['isInternalWall'] = True
            self.tags['isExternalWall'] = False
        elif 'E' in data['typeName']:
            self.tags['isInternalWall'] = False
            self.tags['isExternalWall'] = True
        else:
            self.tags['isInternalWall'] = True 
            self.tags['isExternalWall'] = True


def create_floor(floor_id: int, offset: list[float] = [0,0,0,0]) -> None:
    '''Creates outsides walls, inside walls, and floors separately for each floor/level.

    The offset is for for positioning the floor/building globally. W/o offset, the floor is positioned at the origin.

    Args:
        floor_id (int): ID of the floor to create.
        offset (list[float], optional): Offset to apply to the floor. Format is [x,y,z,angle around z].
    '''
    api = API_Requests()

    data_floor = api.get_floor_id_info(floor_id)
    data_outlines = api.get_floor_id_workspace_info(floor_id)

    walls = []
    for wall in data_floor['wallInfos']:
        walls.append(Wall(wall, offset=offset))

    room_floors = []
    if data_outlines is not None:
        for outline in data_outlines:
            room_floors.append(Floor(outline, offset=offset))

    columns = []
    for column in data_floor['columnInfos']:
        columns.append(Column(column, offset=offset))

    walls_interior = []
    walls_exterior = []
    for wall in walls:
        if wall.tags['isInternalWall']:
            walls_interior.append(wall)
        if wall.tags['isExternalWall']:
            walls_exterior.append(wall)

    if len(walls_exterior) > 0 or len(columns) > 0:
        scene_outsides = Scene(walls_exterior + columns)
        scene_outsides.export(f'model_outsides/floor_{floor_id}_outsides.glb')

    if len(walls_interior) > 0: 
        scene_insides = Scene(walls_interior)
        scene_insides.export(f'model_insides/floor_{floor_id}_insides.glb')
    
    if len(room_floors) > 0:
        scene_floors = Scene(room_floors)
        scene_floors.export(f'model_floors/floor_{floor_id}_floors.glb')

    #scene_all = Scene(walls_exterior + columns + walls_interior + room_floors)
    #scene_all.export(f'floor_{floor_id}_all.glb')


def create_building(building_id: int) -> None:
    '''Creates assets of each floor for a building. Separates outside walls, inside walls, and floors of rooms.

    Best way of generating floors as it includes height offset + extra correcting offsets.

    Args:
        building_id (int): ID of the building to create.
    '''

    api = API_Requests()

    # Retrieving data from Pythagoras
    # building = api.get_building_id(building_id)
    floors = api.get_building_id_floor(building_id)

    # Looping through every possible level code and every floor
    for floor in floors:
        create_floor(floor['id'])


if __name__ == '__main__':

    start = time.time()
    # ----------------------------------------------------------------------------------------------

    api = API_Requests()
    buildings = api.get_building()

    curr_count = 0
    total_count = len(SOUTH_KEN_LIGHT)

    for building in buildings:
        if building['name'] in SOUTH_KEN_LIGHT: 
            create_building(building['id'])
            print(f"Building {building['id']} done. {curr_count}/{total_count}")

    # ----------------------------------------------------------------------------------------------
    end = time.time()

    print(f"Time taken: {end - start} seconds")
