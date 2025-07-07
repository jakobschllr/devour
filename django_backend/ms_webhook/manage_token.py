import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = 'https://www.google.de/callback'
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

REFRESH_TOKEN = os.getenv('TEST_USER_R_TOKEN')

# refresh token expires after appr. 90 days
def get_new_refresh_token(authorization_code):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': authorization_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        access_token = response.json()['access_token']
        refresh_token = response.json()['refresh_token']
        return access_token, refresh_token


def get_new_access_token(refresh_token=REFRESH_TOKEN):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://graph.microsoft.com/.default"
    }

    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
            access_token = response.json()['access_token']
            return access_token
    

def get_user_info(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user info: {response.text}")
        return None