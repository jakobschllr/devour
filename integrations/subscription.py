import requests
import time
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
from get_transcript import get_new_access_token
import base64

# ms teams transcript documentation: https://learn.microsoft.com/en-us/graph/api/onlinemeeting-list-transcripts?view=graph-rest-1.0&tabs=python

 
load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
ENCRYPTION_CERTIFICATE = os.getenv('ENCRYPTION_CERTIFICATE')
REDIRECT_URI = 'https://www.google.de/callback' #"http://localhost:3000/callback"
SCOPE = "OnlineMeetingTranscript.Read.All Calendars.Read User.Read" # Berechtigungen die notwendig sind
AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
REFRESH2 = os.getenv('TEST_USER_R_TOKEN')

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
    print(response)
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


# get meetings info from user
def get_meetings_info(access_token, user_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_id}/calendar/events", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching online meetings: {response.text}")
        return None

#add encrytion certificate later
def subscribe_to_tenant(access_token):
    url = "https://graph.microsoft.com/v1.0/subscriptions"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    data = {
        "changeType": "created,updated,deleted",
        "notificationUrl": "https://5066-141-41-238-69.ngrok-free.app/webhook/transcript_notification",
        "resource": f"communications/onlineMeetings/getAllTranscripts",
        "includeResourceData": True,
        # "encryptionCertificate": f"{base64encodedCertificate}",
        # "encryptionCertificateId": f"{customId}",
        "expirationDateTime": "2026-03-10T14:58:56.7951795+00:00",
        "clientState": CLIENT_SECRET
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()


#add encryption certificate later
def subscribe_to_user(access_token, user_id, base64encodedCertificate="", customId=""):
    url = "https://graph.microsoft.com/v1.0/subscriptions"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    data = {
        "changeType": "created",
        "notificationUrl": "https://7e89-141-41-238-69.ngrok-free.app/webhook/transcript_notification/",
        "resource": f"users/{user_id}/onlineMeetings/getAllTranscripts",
        "expirationDateTime": "2025-03-08T14:58:56.7951795+00:00",
        "includeResourceData": True,
        "lifecycleNotificationUrl": "https://7e89-141-41-238-69.ngrok-free.app/webhook/lifecycle_notification/",
        "encryptionCertificate": f"{base64encodedCertificate}",
        "encryptionCertificateId": f"{customId}",
        "clientState": CLIENT_SECRET
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()


def get_meeting_transcripts(access_token, meeting_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching meeting transcripts: {response.text}")
        return None


def load_cert():
    cert_path = os.getenv("ENCRYPTION_CERTIFICATE_PATH")

    if not cert_path or not os.path.exists(cert_path):
        raise ValueError("Certificate file not found")

    with open(cert_path, "r") as f:
        cert_base64 = f.read().strip().replace("\n", "").replace("\r", "")

    # Validate
    try:
        decoded_cert = base64.b64decode(cert_base64, validate=True)
        print("Certificate loaded successfully!")
        return cert_base64
    except Exception as e:
        print("Invalid Base64 certificate:", e)


# access_token = get_new_access_token(REFRESH2)

# user_info = get_user_info(access_token)
# user_id = user_info['id']

# print(user_id)

# # meeting_info = get_meetings_info(access_token, user_id)

# # meeting_transcript = get_meeting_transcripts(access_token, meeting_id)
# cert = load_cert()

# print(subscribe_to_user(access_token, user_id, cert, "My-Cert-124"))