import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
from msgraph import GraphServiceClient
from datetime import *


load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = 'https://www.google.de/callback' #"http://localhost:3000/callback"
SCOPE = "OnlineMeetingTranscript.Read.All User.Read OnlineMeetings.Read offline_access" # OnlineMeetings.ReadWrite
AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"


REFRESH_TOKEN = os.getenv('MS_REFRESH_TOKEN')

# generates url where user is redirected to in order to login
def get_authorization_url():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }
    url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
    return url

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
    
def get_meeting_data(access_token, short_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings?$filter=joinMeetingIdSettings/joinMeetingId%20eq%20'{short_id}'", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching meeting data: {response.text}")
        return None

def get_transcript_url(access_token, long_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{long_id}/transcripts", headers=headers)
    
    if response.status_code == 200:
        return response.json()['value'][0]['transcriptContentUrl']
    else:
        print(f"Error fetching transcript url: {response.text}")
        return None
    
def get_transcript(access_token, url):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'text/vtt'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching meeting transcripts: {response.text}")
        return None
    
# wenn refresh_token is expired get new refresh_token
# auth_url = get_authorization_url()
# print(auth_url)
# authorization_token = input("Authorization token: ")
# access_token, refresh_token = get_new_refresh_token(authorization_token)

# # wenn refresh token noch gültig ist
# # access_token = get_new_access_token()

# # short_id = "319980869121"

# # meeting_data = get_meeting_data(access_token, short_id)
# # long_id = meeting_data['value'][0]['id']
# # transcript_url = get_transcript_url(access_token, long_id)



# transcript = get_transcript(access_token, transcript_url)
# print(transcript)