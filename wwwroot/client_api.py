import os
import json
from functools import wraps

from flask import Flask, request, abort
import psycopg2
import psycopg2.extras
import logging

app = Flask(__name__)  
API_KEY = '12345'

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.args.get('api_key') and request.args.get('api_key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            abort(401)

    return decorated_function


def get_db_conn():
    return psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST'),
        port=os.environ.get('POSTGRES_PORT'),
        database="campusmap_db",
        user="postgres",
        password="postgres",
    )


@app.route('/buildings', methods=['GET'])
@require_api_key
def buildings():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from buildings")

    ans = cur.fetchall()
    buildings = []
    for row in ans:
        buildings.append(dict(row))

    cur.close()
    conn.close()

    return buildings


@app.route('/buildings/<int:id>/')
@require_api_key
def buildings_id(id):
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from buildings where building_id=%s", (id,))

    ans = cur.fetchone()
    building = dict(ans)

    cur.close()
    conn.close()

    return building



@app.route('/buildings/<int:id>/assets')
@require_api_key
def buildings_id_assets(id):
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("select floor_id from floors where building_id=%s", (id,))

    ans = cur.fetchall()
    
    cur.close()
    conn.close()

    return ans

@app.route('/floors', methods=['GET'])
@require_api_key
def floors():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from floors")

    ans = cur.fetchall()
    floors = []
    for row in ans:
        floors.append(dict(row))

    cur.close()
    conn.close()

    return floors 


@app.route('/floors/<int:id>/')
@require_api_key
def floors_id(id):
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from floors where floor_id=%s", (id,))

    ans = cur.fetchone()
    floor = dict(ans)

    cur.close()
    conn.close()

    return floor 


#   @app.route('/floors/<int:id>/model')
#   def floors_id_model(id):
    #   conn = get_db_conn()
    #   cur = conn.cursor()

    #   cur.execute('select asset from floors where floor_id=%s;', (id,))
    #   ans = cur.fetchone()[0]

    #   model = bytearray(ans)

    #   cur.close()
    #   conn.close()

    #   return list(model)


@app.route('/rooms', methods=['GET'])
def rooms():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from rooms")

    ans = cur.fetchall()
    rooms = []
    for row in ans:
        rooms.append(dict(row))

    cur.close()
    conn.close()

    return rooms 


@app.route('/rooms/<int:id>/')
def rooms_id(id):
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from rooms where room_id=%s", (id,))

    ans = cur.fetchone()
    room = dict(ans)

    cur.close()
    conn.close()

    return room 


@app.route('/request_updates')
def request_updates():
    with open('update_log.json', 'r') as f:
        update_log = json.load(f)

    client_version = request.args.get('version', default=0, type=int)
    server_version = update_log['current_version']

    if client_version == server_version:
        return {
            'current_version': server_version,
            'to_update': []
        }

    to_update = set()
    for i in range(client_version+1, server_version+1):
        for j in update_log['log'][f'{i}']:
            to_update.add(j)

    return {
        'current_version': server_version, 
        'to_update': list(to_update)
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port=8080)
