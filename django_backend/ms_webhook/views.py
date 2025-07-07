import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import os
from dotenv import load_dotenv
from jwt import PyJWKClient
import jwt
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from mongo_models.models.department import DepartmentModel
from ms_webhook.models.subscription import MicrosoftSubscription
from ms_webhook.models.manage_token import get_new_access_token
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from mongo_models.models.integration import IntegrationModel
from data_extraction.extraction_process.python_scripts.extractor import Extractor


logging.basicConfig(filename='/home/jakobschiller/devour/backend_log/logfile.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(message)s')

mongo_host_port = 'mongodb://localhost:27017'
ms_integration_model = IntegrationModel(mongo_host_port)

load_dotenv()
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = 'https://www.google.de/callback' #"http://localhost:3000/callback"
SCOPE = "OnlineMeetingTranscript.Read.All Calendars.Read User.Read OnlineMeetings.Read OnlineMeetings.ReadWrite" # Berechtigungen die notwendig sind
AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
PATH_TO_KEY = os.getenv('PATH_TO_KEY')
PATH_TO_TRANSCRIPT = os.getenv('PATH_TO_TRANSCRIPT')


@csrf_exempt
def home(request):
    logging.info("Home : Home")
    return HttpResponse("Welcome Home", status=200)

@csrf_exempt
def transcript_notification(request):
    """Handle Microsoft Graph API subscription notifications"""
    
    # Microsoft Graph validates webhook by sending a validationToken
    # Token should be sent back as text to be validated
    if(request.GET.get("validationToken", "")):
        validation_token = request.GET.get("validationToken", "")
        if validation_token:
            logging.info("Transcript Url validated")
            return HttpResponse(validation_token, content_type="text/plain", status=200)
        
    if request.method == "POST":
        try:

            logging.info("Received Transcript Notification Post Request")

            # Extractiong info from the request's body
            body = json.loads(request.body)
            value = body["value"]
            data = value[0]
            validation_tokens = body["validationTokens"]
            validation_token = validation_tokens[0]
            tenant_id = data["tenantId"]

            # Verifying the notification to ensure that it is sent by microsoft and to ensure 
            # This url is the intended reciepient
            if is_validation_token_valid([CLIENT_ID], tenant_id, validation_token):

                subscription_id = data.get('subscriptionId')
                notification_type = data.get('changeType')
                encrypted_data = data.get('encryptedContent')['data']
                encrypted_data_key = data.get('encryptedContent')['dataKey']

                logging.info("Subscription ID ", subscription_id)
                logging.info("Notification type ", notification_type)


                if encrypted_data and encrypted_data_key:
                    decrypted_data_key = decrypt_data_key(encrypted_data_key)
                    if(verify_signature(data, decrypted_data_key)):
                        logging.info("Data Signature validated")
                        decrypted_data = decrypt_data(encrypted_data, decrypted_data_key)
                        transcript_data = json.loads(decrypted_data)
                        save_transcript_to_database(transcript_data, subscription_id)
                        # save_transcript_to_file(transcript_data, get_access_token(subscription_id))
                    else:
                        logging.warning("Data Signature verification failed")
                        raise Exception("Data Signature check failed")

                return JsonResponse({"status": "success", "message": "Transcription decrypted successfully"}, status=202)

        except Exception as e:
            logging.error(f"Error : {e}") # Logging error
            return JsonResponse({"status": "Ok", "message": "Notification received"}, status=200)
    logging.warning("Invalid Request received")
    return JsonResponse({"status": "OK", "message": "Notification received"}, status=202)


def save_transcript_to_file(transcript_data, access_token):
    logging.info("Saving Transcript to file")

    try:
        transcript_text = get_transcript(transcript_data, access_token)
        transcript_call_id = transcript_data['callId']

        with open(PATH_TO_TRANSCRIPT + transcript_call_id + ".txt", 'w', encoding='utf-8') as file:
            file.write(transcript_text)

        logging.info("Transcript Saved succesfuly to file")

    except Exception as e:
        logging.info(f"Error occured while saving file {e}")
        raise e



def decrypt_data_key(encrypted_data_key) -> bytes:
    """
    Decrypt the encrypted data key using the private key.
    
    :param encrypted_data_key: The base64 encoded encrypted data key from the notification.
    :return: The decrypted data key as bytes.
    """
    try:
        # Load your private key (you need to generate the private key and have access to it)
        with open(PATH_TO_KEY, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        
        # Decode the base64 encoded encrypted data key
        encrypted_data_key_bytes = base64.b64decode(encrypted_data_key)

        # Decrypt the data key using the private key
        decrypted_data_key = private_key.decrypt(
            encrypted_data_key_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )

        return decrypted_data_key
    except Exception as e:
        logging.error(f"Error while decrypting data key: {e}")
        raise e


def decrypt_data(encrypted_data, decrypted_data_key):
    """
    Decrypt the encrypted data using the decrypted data key.
    
    :param encrypted_data: The base64 encoded encrypted data from the notification.
    :param decrypted_data_key: The decrypted data key as bytes.
    :return: The decrypted data as a string.
    """

    try:
        # Decode the base64 encoded encrypted data
        encrypted_data_bytes = base64.b64decode(encrypted_data)

        # Initialize the cipher with the decrypted data key and IV (initialization vector)
        iv = decrypted_data_key[:16]  # Assuming the first 16 bytes are the IV
        cipher = Cipher(algorithms.AES(decrypted_data_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        decrypted_data_bytes = decryptor.update(encrypted_data_bytes) + decryptor.finalize()

        # Remove padding characters (PKCS7 padding)
        padding_length = decrypted_data_bytes[-1]
        decrypted_data_bytes = decrypted_data_bytes[:-padding_length]

        # Return the decrypted data as a string (assuming it's UTF-8 encoded)
        decrypted_data_str = decrypted_data_bytes.decode("utf-8")
        return decrypted_data_str
    except Exception as e:
        raise e

    


@csrf_exempt
def lifecycle_notification(request):
    """
    Handles the lifecycle notifications for subscribtions to ms Teams 
    """
    
    if(request.GET.get("validationToken", "")):
                validation_token = request.GET.get("validationToken", "")
                if validation_token:
                    logging.info("Validated Lifcecycle Notification Url")
                    return HttpResponse(validation_token, content_type="text/plain", status=200)
                
                
    if request.method == "POST":
        try:
            
            # Parse the incoming JSON request body
            raw_data = json.loads(request.body)

            data = raw_data['value'][0]

            # Extract the necessary fields from the request data
            subscription_id = data.get('subscriptionId')
            expiration_date = data.get("subscriptionExpirationDateTime")
            lifecycle_event = data.get("lifecycleEvent")
            client_state = data.get("clientState")

            # Verifying the secret client code is correct 
            if not client_state == CLIENT_SECRET:
                logging.warning("Incorrect Client Secret")
                return HttpResponse("Notification received", status=202)

            logging.info(f"""Got notification for Subscribtion :
                         Subscribtion Id: {subscription_id} 
                         Expiration Date: {expiration_date} 
                         Lifecycle Event: {lifecycle_event}""")

            if(lifecycle_event == "reauthorizationRequired"):
                logging.info("Trying to renew Subscription")
                isrenewed = renew_subscription(subscription_id)
                if(isrenewed):
                    logging.info("Subscribtion renewed")
                    return HttpResponse("Subscribtion Renewed", status=202)

            elif(lifecycle_event == "missed"):
                logging.info("Missed a Notification")
                return HttpResponse("Notification received", status=202)

            # Subscribtion was deleted and action needs to be taken 
            elif(lifecycle_event == "subscriptionRemoved"):
                logging.info("Subscribtion Deleted")
                # TODO Delete Subscribtion in database and maybe request a new 
                return HttpResponse("Subscribtion Deleted", status=202)


            return HttpResponse("Lifecycle event not understood", status=400)

        except Exception as e:
            # Handle any errors and respond with an error message
            logging.error("Error : ", str(e))
            return HttpResponse(str(e), status=400)
    logging.warning("Invalid Request")
    return HttpResponse("Notification Received.", status=200)


def renew_subscription(subscription_id):
    try:
        access_token = get_access_token(subscription_id)
        url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        new_expiration_date = (datetime.now(timezone.utc) + timedelta(days=3)).replace(microsecond=0).isoformat()
        data = {
            "expirationDateTime": new_expiration_date
        }

        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            logging.info(f"Subscription renewed successfully! \nNew Date : {new_expiration_date}")
            return True
        else:
            logging.error(f"Error renewing subscription: {response.text}")
            return False
    except Exception as e:
        logging.error(str(e))


def verify_signature(data, decryted_symmetric_key):
    """Verify the signature of the incoming request"""
    try:
        # Extract the signature 
        expected_signature = data.get("encryptedContent")["dataSignature"]

        encrypted_payload = data.get("encryptedContent")["data"]
    
        encrypted_payload_decoded = base64.b64decode(encrypted_payload)
        signature = base64.b64encode(hmac.new(decryted_symmetric_key, encrypted_payload_decoded, hashlib.sha256).digest()).decode('utf-8')

        logging.info(f"Expected Signature: {expected_signature}")
        logging.info(f"Actual Signature: {signature}")

        # Compare the signatures
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logging.info(f"Error verifying signature.")
        raise e


def get_transcript(transcript_data : json, access_token):
    """
    Fetches the transcript from the provided transcript data
    :param :transcript_data The decrypted data from Microsoft's transcript notification
    :param :access_token The user's access token
    :retutn: TRanscript as Text
    """
    # access_token = get_new_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'text/vtt'
    }
    try:
        user_id = transcript_data['meetingOrganizer']['user']['id']   
        meeting_id = transcript_data['meetingId']
        transcript_id = transcript_data['id']
        full_trancript_url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content?format=text/vtt"
        logging.info(f"URL to the Transcript : {full_trancript_url}" )
        response = requests.get(full_trancript_url, headers=headers)
        if response.status_code == 200:
            transcript_text = response.text
            logging.info(f"Transcript fetched successfully")
            return transcript_text
        else:
            raise Exception("Error fetching Transcript")
    except Exception as e:
        logging.error(f"Error occurred while fetching transcript")
        raise e


def get_openid_configuration():
    url = "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def is_validation_token_valid(app_ids, tenant_id, serialized_token):
    try:
        # Fetch OpenID configuration

        openid_config = get_openid_configuration()
        # logging.info(f"Config: {openid_config}")
        jwks_url = openid_config["jwks_uri"]
        # logging.info(f"JWKS URL: {jwks_url}")

        # Fetch JWKS keys from the given URL
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(serialized_token).key

        # Decode and verify the token
        decoded_token = jwt.decode(
            serialized_token,
            signing_key,
            algorithms=["RS256"],
            audience=app_ids,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            options={"verify_exp": True}
        )

        logging.info("Tokens validted successfully")

        return True
    except Exception as e:
        logging.error("Could not validate token")
        logging.error(str(e))
        return False


def get_access_token(subscription_id : str):
    """
    Fetches the access Token from the database using the subscribtion id.
    """

    try:

        refresh_token_response = ms_integration_model.get_microsoft_refresh_token(subscription_id)

        refresh_token = None

        if(refresh_token_response['status'] == 'success'):
            refresh_token = refresh_token_response['data']

        else:
            raise Exception("Refresh Token Not Found")


        access_token = get_new_access_token(refresh_token)

        logging.info("Access Token found")

        return access_token

    except Exception as e:
        logging.error("Error While Getting Access Token")
        raise e


def save_transcript_to_database(transcript_data, subscription_id):
    try:
        access_token = get_access_token(subscription_id)
        response = ms_integration_model.get_user_data(subscription_id)
        if response['status'] != 'success':
            logging.error("Subscribtion Id or Mongo DB error")
            raise Exception("Subscribtion id error")
        
        department_id = response['data']['department_id']
        department_model = DepartmentModel(mongo_host_port)
        department_response = department_model.get_vector_db_data(department_id)
        if department_response['status'] != 'success':
            logging.error("Department model error")
            raise Exception("Department Model Error")

        department_data = department_response['data']
        vector_db_path = department_data['vector_db_dir_path']
        vector_db_collection = department_data['vector_db_collection']
        extractor = Extractor(vector_db_path, vector_db_collection)
        transcript_text = get_transcript(transcript_data, access_token)
        extractor.extract(transcript_text)
        extractor.add_to_db()

    except Exception as e:
        logging.error(str(e))
        save_transcript_to_file(transcript_data, access_token)



