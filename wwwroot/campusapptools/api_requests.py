'''

This module contains the API_Requests class which is used to make requests to the Pythagoras API.

'''


import requests
import warnings


class API_Requests:

    def __init__(self) -> None:
        self.api_url="https://pim.pythagoras.se/imp_datamanager"
        self.headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en;q=0.9',
            'api_key': 'VAOPSF56NB15NGAOWET1059AXPEEM66NROO',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        }

    def get_component(self) -> list:
        url = f'{self.api_url}/rest/v1/component'

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data

    def get_building(self) -> list:
        '''Get all buildings.

        Returns:
            list: A list of all buildings.
        '''
        url = f'{self.api_url}/rest/v1/building'

        # Define the query string parameters
        params = {
            'orderAsc': 'true'
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_building_id(self, building_id: int) -> list:
        url = f'{self.api_url}/rest/v1/building/{building_id}'
    
        # Send a GET request to the API
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_building_id_info(self, building_id: int) -> list:
        url = f'{self.api_url}/rest/v1/building/{building_id}/info'

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data
            

    def get_building_info(self) -> list:
        url = f'{self.api_url}/rest/v1/building/info'

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_building_id_floor(self, building_id: int) -> list:
        '''Get the floors of a specific building by the building id.

        Args:
            building_id (int): The ID of the building.

        Returns:
            list: A list of all floors of the building.
        '''

        url = f'{self.api_url}/rest/v1/building/{building_id}/floor'

        # Define the query string parameters
        params = {
            'orderAsc': 'true'
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data

    
    def get_building_id_floor_info(self, building_id: int) -> list:
        '''Get the floor info of a specific building by the building id.

        Data inclues infos about walls and where they are located.

        Args:
            building_id (int): The ID of the building.

        Returns:
            list: A list of all floor info of the building.
        '''
        url = f'{self.api_url}/rest/v1/building/{building_id}/floor/info'

        # Define the query string parameters
        params = {
            'includeWallInfos': True,
            'includeWallDoorInfos': True,
            'includeWallWindowInfos': True,
            'includeColumnInfos': True,
            'includeColumnOutlines': True,
            'invertY': False,
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data

    
    def get_floor_id_workspace_info(self, floor_id: int) -> list:
        url = f'{self.api_url}/rest/v1/floor/{floor_id}/workspace/info'

        # Define the query string parameters
        params = {
            'includeAttributes': True,
            'includePolygon': True,
            'includeOutline': True,
            'includeOutlineHoles': True,
            'includeUtilityCoord': True,
            'invertY': False,
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            warnings.warn(f"Warning: Received status code {response.status_code}")
            return None

        data = response.json()

        return data


    def get_floor_id_component_all_info(self, floor_id: int) -> list:
        url = f'{self.api_url}/rest/v1/floor/{floor_id}/component/all/info'

        # Define the query string parameters
        params = {
            'includeAttributes': True,
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_floor_id_info(self, floor_id: int, includeWallInfos: bool = True, includeWallDoorInfos: bool = True,
                          includeWallWindowInfos: bool = True, includeColumnInfos: bool = True,
                          includeColumnOutlines: bool = True, includeFloorComponentInfos: bool = True, 
                          includeWorkspaceComponentInfos: bool = True) -> dict:
        url = f'{self.api_url}/rest/v1/floor/{floor_id}/info'

        # Define the query string parameters
        params = {
            'includeWallInfos': includeWallInfos,
            'includeWallDoorInfos': includeWallDoorInfos,
            'includeWallWindowInfos': includeWallWindowInfos,
            'includeColumnInfos': includeColumnInfos,
            'includeColumnOutlines': includeColumnOutlines,
            'includeFloorComponentInfos': includeFloorComponentInfos,
            'includeWorkspaceComponentInfos': includeWorkspaceComponentInfos,
            'invertY': False,
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_floor(self) -> dict:
        url = f'{self.api_url}/rest/v1/floor'

        # Define the query string parameters
        params = {
            'orderAsc': True,
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data
    

    def get_floor_info(self, ids: list) -> dict:
        url = f'{self.api_url}/rest/v1/floor/info'

        # Define the query string parameters
        params = {
            'orderAsc': True,
            'floorIds[]': ids,
            'includeWallInfos': True,
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_workspace(self) -> dict:
        url = f'{self.api_url}/rest/v1/workspace'

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_workspace_info(self) -> dict:
        url = f'{self.api_url}/rest/v1/workspace/info'

        # Define the query string parameters
        params = {
            'includeOutline': True
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data


    def get_workspace_id_info(self, room_id: int) -> list:
        url = f'{self.api_url}/rest/v1/workspace/{room_id}/info'

        # Define the query string parameters
        params = {
            'invertY': False
        }

        # Send a GET request to the API
        response = requests.get(url, headers=self.headers, params=params)
        assert response.status_code == 200, "Error: Received status code {}".format(response.status_code)
        data = response.json()

        return data