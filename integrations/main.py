import requests
import time
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = 'https://www.google.de/callback' #"http://localhost:3000/callback"
SCOPE = "OnlineMeetingTranscript.Read.All Calendars.Read User.Read OnlineMeetings.Read OnlineMeetings.ReadWrite" # Berechtigungen die notwendig sind
AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

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

# Access Token wird generiert; mit dem Access Token kann auf die Daten des Nutzers über die MS Graph API
# zugegriffen werden
def get_access_token(authorization_code):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': authorization_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    
# get user info    
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

def subscribe(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)

def get_meeting_info(access_token, meeting_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings?$filter=joinMeetingIdSettings/joinMeetingId%20eq%20'{meeting_id}'", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching meeting transcripts: {response.text}")
        return None

def get_transcript_url(access_token, meeting_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts", headers=headers)
    
    if response.status_code == 200:
        return response.json()['value'][0]['transcriptContentUrl']
    else:
        print(f"Error fetching meeting transcripts: {response.text}")
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
    

# auth_url = get_authorization_url()
# print('Authorization URL: ', auth_url)

# authorization_token = input("Authorization token: ")
# access_token = get_access_token(authorization_token)

# meeting_id = "319980869121"

# meeting_info = get_meeting_info(access_token, meeting_id)
# long_id = meeting_info['value'][0]['id']
# transcript_url = get_transcript_url(access_token, long_id)

# transcript = get_transcript(access_token, transcript_url)
# print(transcript)