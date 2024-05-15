import os
import sys
sys.path.append('../')

import psycopg2
from api_requests import API_Requests
import time
import sqlite3

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data', 'spaces.db')



def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        '''
        drop table if exists buildings;
        '''
    )   
    conn.commit()     
    cursor.execute(
        '''
        create table if not exists buildings (
            building_id int primary key,
            building_uid varchar(200),
            name varchar(200),
            x float,
            y float,
            rotation float,
            timestamp bigint
        );
        '''
    )

    cursor.execute(
        '''
        drop table if exists floors;
        '''
    )      

    cursor.execute(
        '''
        create table if not exists floors (
            floor_id int primary key,
            floor_uid varchar(200),
            building_id int references buildings(building_id),
            name varchar(200),
            timestamp bigint
        );
        '''
    )

    cursor.execute(
        '''
        drop table if exists rooms;
        '''
    )    

    cursor.execute(
        '''
        create table if not exists rooms (
            room_id int primary key,
            room_uid varchar(200),
            floor_id int references floors(floor_id),
            name varchar(200),
            outline float[][],
            timestamp bigint
        );
        '''
    )

    conn.close()

api = API_Requests()

#conn.autocommit = True


create_tables()

buildings = api.get_building() 
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for building in buildings:

    print(building.keys())
    # print(building['geoLocation'].keys())
    cursor.execute(
        '''
        insert into buildings (building_id, building_uid, name, x, y, rotation, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (building_id) DO UPDATE SET
            building_uid = EXCLUDED.building_uid,
            name = EXCLUDED.name,
            x = EXCLUDED.x,
            y = EXCLUDED.y,
            rotation = EXCLUDED.rotation,
            timestamp = EXCLUDED.timestamp;
        ''',
        (building['id'], building['uid'], building['name'], building['geoLocation']['x'], building['geoLocation']['y'], building['geoLocation']['rotation'], building['updated'])
    )
conn.commit()
conn.close()


tic = time.perf_counter()

building_ids = [building['id'] for building in buildings]
for building_id in building_ids:
    floors = api.get_building_id_floor(building_id)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for i,floor in enumerate(floors):
        print(i/len(floors), '$')

        floor_info = api.get_floor_id_info(floor['id'])

        cursor.execute(
            """
            insert into floors (floor_id, floor_uid, building_id, name, timestamp)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (floor_id) DO UPDATE SET
                floor_uid = EXCLUDED.floor_uid,
                building_id = EXCLUDED.building_id,
                name = EXCLUDED.name,
                timestamp = EXCLUDED.timestamp;
            """,
            (floor['id'], floor['uid'], floor_info['buildingId'], floor_info['name'], floor['updated'])
        )

        workspace_info = api.get_floor_id_workspace_info(floor['id'])
        if workspace_info is None: continue
        for room in workspace_info:
            coords = [[elem['x'], elem['y']] for elem in room['outline']['coords']]
            print(coords)

            cursor.execute(
                '''
                insert into rooms (room_id, room_uid, floor_id, name, outline, timestamp)
                values (?, ?, ?, ?, ?, ?)
                on conflict (room_id) do update set
                    room_uid = excluded.room_uid,
                    floor_id = excluded.floor_id,
                    name = excluded.name,
                    outline = excluded.outline,
                    timestamp = excluded.timestamp;
                ''',
                (room['id'], room['uid'], floor['id'], room['name'], ''.join(str(v) for v in coords), room['updated'])
            )
    conn.commit()
    conn.close()

toc = time.perf_counter()


print('time elapsed: ', toc-tic)

