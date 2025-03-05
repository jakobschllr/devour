import json
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from webhook.get_access_token import get_new_access_token
from django.utils.dateparse import parse_datetime


# Store the latest event for debugging purposes
LATEST_EVENTS = []
ACCESS_TOKEN = get_new_access_token()

load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = 'https://www.google.de/callback' #"http://localhost:3000/callback"
SCOPE = "OnlineMeetingTranscript.Read.All Calendars.Read User.Read OnlineMeetings.Read OnlineMeetings.ReadWrite" # Berechtigungen die notwendig sind
AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"



@csrf_exempt
def transcript_notification(request):
    """Handle Microsoft Graph API subscription notifications"""
    
    # Microsoft Graph validates webhook by sending a validationToken
    if(request.GET.get("validationToken", "")):
        validation_token = request.GET.get("validationToken", "")
        print(validation_token)
        if validation_token:
            return HttpResponse(validation_token, content_type="text/plain", status=200)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received notification:", json.dumps(data, indent=2))

            # Store the event for debugging (in-memory, replace with DB if needed)
            LATEST_EVENTS.append({"timestamp": now(), "data": data})

            # Process the notification data
            for event in data.get("value", []):
                process_meeting_event(event)

            return JsonResponse({"message": "Notification received"}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    return JsonResponse({"error": "Invalid request"}, status=400)


def process_meeting_event(event):
    """Extract meeting details and fetch transcript if available"""
    
    resource_data = event.get("resourceData", {})
    event_id = resource_data.get("id")
    organizer_id = resource_data.get("organizer", {}).get("id")

    if event_id and organizer_id:
        print(f"Processing event {event_id} from organizer {organizer_id}")
        
        # Fetch transcript if meeting has ended
        transcript = fetch_transcript(organizer_id, event_id)
        print("Transcript Data:", transcript)


def fetch_transcript(user_id, event_id):
    """Fetch the transcript for the meeting"""
    
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/onlineMeetings/{event_id}/transcripts"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching transcript:", response.json())
        return None


@csrf_exempt
def lifecycle_notification(request):
    if request.method == "POST":
        try:
            if(request.GET.get("validationToken", "")):
                validation_token = request.GET.get("validationToken", "")
                print(validation_token)
                if validation_token:
                    return HttpResponse(validation_token, content_type="text/plain", status=200)

            # Parse the incoming JSON request body
            data = json.loads(request.body)

            # Extract the necessary fields from the request data
            subscription_id = data.get('subscriptionId')
            notification_type = data.get('notificationType')
            expiration_date_time = data.get('expirationDateTime')
            client_state = data.get('clientState')

            # Parse the expiration date time to a Python datetime object
            expiration_date_time = parse_datetime(expiration_date_time)



            # You can add any custom logic here, like checking if the subscription is expiring soon
            if(expiration_date_time - now() <= 5):
                print("Subscription lauft bald ab") # mmake better logic for this 

            return JsonResponse({"status": "success", "message": "Notification received successfully."}, status=202)

        except Exception as e:
            # Handle any errors and respond with an error message
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)