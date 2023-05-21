import json
import requests

class Auth():
    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_header(self) -> dict:
        return {
            'content-type': 'application/x-www-form-urlencoded',
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_key
        }

    def get_data_header(self, auth_response: dict) -> dict:
        auth_JSON = json.loads(auth_response.text)
        access_token = auth_JSON.get('access_token')

        return {
            'authorization': 'Bearer ' + access_token
        }


class DataAPI():
    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key

    def get_data(self, url: str) -> dict:
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"

        try:
            data_response = requests.get(url, headers = auth.get_data_header(auth_response))
        except:
            auth = Auth(self.app_id, self.app_key)
            auth_response = requests.post(auth_url, auth.get_auth_header())
            data_response = requests.get(url, headers = auth.get_data_header(auth_response))  
        
        data = json.loads(data_response.text)
        return data # json 格式資料

