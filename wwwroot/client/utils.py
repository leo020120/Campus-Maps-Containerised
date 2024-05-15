import requests
import time
import json
import ast


base_url = 'https://campusmap-dev-campusmap.to1azure.imperialapp.io'
blobstore_url = 'https://campusmaps.blob.core.windows.net/assets'

def update_assets():
    with open('assets/versions.json', 'r') as f:
        versions = json.load(f)

    version, to_update = _get_updates(versions['current_version'])
    to_update = _filter_updates(to_update, versions)

    print('Updating: ', to_update)

    _save_assets(to_update)

    with open('assets/versions.json', 'w') as f:
        versions['to_download'] = []
        versions['current_version'] = version
        json.dump(versions, f)


def get_building_assets(building_id):
    url = f"{base_url}/buildings/{building_id}/assets"

    r = requests.get(url)
    ids = ast.literal_eval(r.text)
    ids = [elem[0] for elem in ids]

    return _get_assets(ids)
print(get_building_assets)


def _get_updates(current_version):
    url = f"{base_url}/request_updates"
    #url = "http://127.0.0.1:5000/request_updates"
    params = {'version': current_version}

    r = requests.get(url, params=params)
    assert r.status_code == 200

    data = ast.literal_eval(r.text)
    to_update = data['to_update']
    version = data['current_version']

    return (version, to_update)


def _filter_updates(all_updates, versions):
    to_update = []
    for i in all_updates:
        if i in versions['assets_on_device']:
            to_update.append(i)

    for i in versions['to_download']:
        if i not in to_update:
            to_update.append(i)
        
    return to_update


def _get_assets(ids):
    assets = []
    for floor_id in ids:
        url = f"{blobstore_url}/assets/floor_{floor_id}.glb"
        r = requests.get(url) 

        assets.append((floor_id, r.content))

    with open('assets/versions.json', 'r') as f:
        versions = json.load(f)

    versions['to_download'] = ids
    versions['assets_on_device'] = versions['assets_on_device'] + ids

    with open('assets/versions.json', 'w') as f:
        json.dump(versions, f)

    return assets


def _save_assets(ids):
    assets = []
    for floor_id in ids:
        url = f"{blobstore_url}/assets/floor_{floor_id}.glb"
        r = requests.get(url) 

        with open(f'assets/floor_{floor_id}.glb', 'wb') as f:
            f.write(r.content)



if __name__ == '__main__':
    start = time.time()
    #assets = get_building_assets(202)
    update_assets()
    end = time.time()
    print(end - start)