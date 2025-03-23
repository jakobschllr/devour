from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from datetime import timezone
# from urllib.parse import urlencode
# from msgraph import GraphServiceClient
import base64

# ms teams transcript documentation: https://learn.microsoft.com/en-us/graph/api/onlinemeeting-list-transcripts?view=graph-rest-1.0&tabs=python

load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
CERTIFICATE_PATH = os.getenv("ENCRYPTION_CERTIFICATE_PATH")
REDIRECT_URI = 'https://www.google.de/callback' #"http://localhost:3000/callback"
AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
TRANSCRIPT_NOTIFICATION_URL = "https://a3eb-141-41-238-69.ngrok-free.app/ms_webhook/transcript_notification/"
LIFECYCLE_NOTIFICATION_URL="https://a3eb-141-41-238-69.ngrok-free.app/ms_webhook/lifecycle_notification/"


class MicrosoftSubscription:
    
    def __init__(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, change_type="created", transcript_notification_url=TRANSCRIPT_NOTIFICATION_URL, life_cycle_notification_url=LIFECYCLE_NOTIFICATION_URL, encryption_certificate_path=CERTIFICATE_PATH):
        """
        Class to manage subscription to microsoft team's transcripts

        :param client_id: The App's Azure ID
        :param client_scecret: CLient's status or secret in Azure
        :param change_type: The change types to subscribe to (Created, deleted, updated) are the possible values.\n
                            By default it's just created because you just need to know when new transcripts are created
        """
        self.client_id = client_id
        self.change_type = change_type
        self.notification_url = transcript_notification_url
        self.client_secret = client_secret
        self.encryption_certificate = self.__load_certification(encryption_certificate_path)
        self.encryption_certificate_id = "My-Self-Signed-Certificate"
        self.lifecycle_notification_url = life_cycle_notification_url


    def create_subscription(self, user_id, access_token):
        """
        Creates a subscription for Microsoft Teams transcripts for a particular user.\n
        The subscription is valid for max3 days after which it should be renewed.\n
        The notifications (New transcript notifications and Lifecycle notifications of the subscribtion) will be sent to the urls provided when creating this object

        :param user_id: The ID of the user for whom the subscription is created.
        :param access_token: The access token for authentication.
        :return: The response JSON if the subscription is created successfully, None otherwise.\n
                 The JSON contains info like subscription id, urls, user id, expiration date etc.
        """
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        expiration_date = (datetime.now(timezone.utc) + timedelta(days=3)).replace(microsecond=0).isoformat()
        data = {
            "changeType": self.change_type,
            "notificationUrl": self.notification_url,
            "resource": f"users/{user_id}/onlineMeetings/getAllTranscripts",
            "expirationDateTime": str(expiration_date),
            "includeResourceData": True,
            "lifecycleNotificationUrl": self.lifecycle_notification_url,
            "encryptionCertificate": self.encryption_certificate,
            "encryptionCertificateId": self.encryption_certificate_id,
            "clientState": self.client_secret
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print("Subscription created successfully!")
            return response.json()
        else:
            print(f"Error creating subscription: {response.text}")
            return None


    def delete_subscription(self, subscription_id, access_token):
        """
        Deletes an existing subscription.

        :param subscription_id: The ID of the subscription to be deleted.
        :param access_token: The user access token for authentication.
        :return: True if the subscription is deleted successfully, False otherwise.
        """
        if not subscription_id:
            print("No subscription to delete.")
            return None
        url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print("Subscription deleted successfully!")
            return True
        else:
            print(f"Error deleting subscription: {response.text}")
            return False


    def __load_certification(self, cert_path):
        """
        Loads and validates the encryption certificate.

        :param cert_path: The path to the encryption certificate file.
        :return: The base64 encoded certificate string.
        :raises ValueError: If the certificate file is not found or invalid.
        """
        if not cert_path or not os.path.exists(cert_path):
            raise ValueError("Certificate file not found")
        with open(cert_path, "r") as f:
            cert_base64 = f.read().strip().replace("\n", "").replace("\r", "")
        # Validate
        try:
            decoded_cert = base64.b64decode(cert_base64, validate=True)
            return cert_base64
        except Exception as e:
            print("Invalid Base64 certificate:", e)

