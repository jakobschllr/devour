import logging
from django.http import JsonResponse
from bson import ObjectId
import json
from pathlib import Path

from django.views.decorators.csrf import csrf_exempt # DAS DARF NICHT IN PRODUKTION GEHEN, csrf_exempt bei POST-Requests überall vor Produktion entfernen

from mongo_models.models.department import DepartmentModel
from mongo_models.models.user import UserModel
from mongo_models.models.chat import ChatModel
from mongo_models.models.integration import IntegrationModel

from encryption.text_encrypt import Encryptor

from chatbot.chatbot import Chat
from chatbot.chat_cache import ChatCache

from vector_database.database import Database

from ms_webhook.models.subscription import MicrosoftSubscription
from ms_webhook.models.manage_token import get_new_refresh_token, get_new_access_token, get_user_info

logging.basicConfig(filename='/home/jakobschiller/devour/backend_log/logfile.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(message)s')

encryptor = Encryptor()

mongo_host_port = "mongodb://localhost:27017"

department_model = DepartmentModel(mongo_host_port)
user_model = UserModel(mongo_host_port)
chat_model = ChatModel(mongo_host_port)
integration_model = IntegrationModel(mongo_host_port)

chat_cache = ChatCache(600) # create cache for chat objects; chat objects will be stored for 10 minutes after last prompt

# ==================================
# user related endpoints 
# ==================================

@csrf_exempt
def get_user_data(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data['user_id']
        user_id_obj = ObjectId(user_id)

        print("USER ID", user_id)

        user_collection_response = user_model.get_user_data(user_id_obj)

        if user_collection_response["status"] == "success":

            user_data = user_collection_response["data"]
            user_data['context'] = user_data['context']

            print("User Data", user_data)

            return JsonResponse({
                "status": 200,
                "data": user_data
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": user_collection_response
            })

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data['email']
        password = data['password']

        response = user_model.login(email=email, password=password)

        if response["status"] == "success":
            http_code = 200
        else:
            http_code = 500

        return JsonResponse({
            "status": http_code,
            "data": response
        })

# signup flow: signup (not saved to db yet) -> create or join department -> save department to db (if created newly) -> save user to db
@csrf_exempt
def signup_user(request):
    if request.method == "POST":
        data = json.loads(request.body)

        # create new user in user collection
        user_response = user_model.add_user(
            name=data['name'],
            password=data['password'],
            email=data['email'],
            role=data['role'],
            department_id=ObjectId(data['department_id']),
            department_name=data['department_name'],
            company_name=data['company_name'],
            is_admin=data['is_admin']
        )

        if user_response["status"] == "success":

            # add new user to department collection
            department_collection_response = department_model.add_employee(
                department_id=ObjectId(data['department_id']),
                employee_id=ObjectId(user_response["data"]["_id"])
            )
            if department_collection_response["status"]:
                print("Created new user with id: ", user_response["data"]["_id"])
                return JsonResponse({
                    "status": 200,
                    "data": user_response["data"]
                })
            else:
                print("User id couldn't be added to department.")
                return JsonResponse({
                    "status": 500,
                    "data": department_collection_response["data"]
                })
        else:
            print("The user couldn't be saved to user collection")
            return JsonResponse({
                    "status": 500,
                    "data": user_response["data"]
                })

@csrf_exempt
def delete_user(request):
    if request.method == "DELETE":
        data = json.loads(request.body)
        user_id = ObjectId(data["user_id"])
        chat_ids = data["chat_ids"]
        department_id = ObjectId(data["department_id"])

        # delete user
        deleted_user_response = user_model.delete_user(
            user_id=user_id
        )

        # delete chats of user
        successfully_deleted_chats = []
        chats_with_deletion_failure = []
        for id in chat_ids:
            deleted_chat_response = chat_model.delete_chat(
                chat_id=ObjectId(id)
            )
            if deleted_chat_response["status"] == "success":
                successfully_deleted_chats.append(True)
            else:
                chats_with_deletion_failure.append(id)

        deleted_chats = True if len(successfully_deleted_chats) == chat_ids else False

        # delete user_id from department
        deleted_from_department_response = department_model.delete_employee(
            department_id=department_id,
            employee_id=user_id
        )

        if deleted_user_response["status"] == "success" and deleted_chats and deleted_from_department_response["status"] == "success":
            return JsonResponse({
                "status": 200,
                "data": "Deleted user from user collection, deleted all the chats of user and removed user from department."
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": {
                    "user_collection_response": deleted_user_response,
                    "chat_collection_response": f"Chats that couldn't be deleted: {chats_with_deletion_failure}",
                    "department_collection_response": deleted_from_department_response
                }
            })

# endpoint to make user admin
@csrf_exempt
def make_user_admin(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = ObjectId(data['user_id'])

        user_collection_response = user_model.make_admin(user_id=user_id)

        if user_collection_response["status"] == "success":
            return JsonResponse({
                "status": 200,
                "data": user_id
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": user_collection_response
            })

# endpoint to make user no admin
@csrf_exempt       
def make_user_non_admin(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = ObjectId(data['user_id'])

        user_collection_response = user_model.make_non_admin(user_id=user_id)

        if user_collection_response["status"] == "success":
            return JsonResponse({
                "status": 200,
                "data": user_id
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": user_collection_response
            })

# endpoint to change individual user configurations (e.g. individual prompts, chat model tone etc.)
@csrf_exempt
def change_configuration(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(data)
        user_id = ObjectId(data["user_id"])
        configuration = data["configuration"]
        changed_value = data["changed_value"]

        user_collection_response = user_model.change_configuration(user_id=user_id, config=configuration, changed_value=changed_value)
        if user_collection_response["status"] == "success":
            return JsonResponse({
                "status": 200,
                "data": user_collection_response
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": user_collection_response
            })

@csrf_exempt
def store_ms_teams_tokens(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = ObjectId(data["user_id"])
        department_id = ObjectId(data["department_id"])
        authorization_token = data['authorization_token']

        # get refresh token and access token with authorization token
        access_token, refresh_token = get_new_refresh_token(authorization_token)
        microsoft_user_id = get_user_info(access_token)['id']

        print("Access Token: ", access_token)
        print("Refresh Token: ", refresh_token)

        # save microsoft user id to db
        microsoft_user_id_response = user_model.set_microsoft_user_id(
            user_id=user_id,
            microsoft_user_id=microsoft_user_id
        )

        # create subscription and get subscription id for user
        ms_subscription_model = MicrosoftSubscription()
        subscription_response = ms_subscription_model.create_subscription(microsoft_user_id, access_token)
        logging.info(f"Subscription response: {subscription_response}")

        subscription_id = subscription_response['id']

        # save refresh token to integrations db
        integrations_model_response = integration_model.add_ms_teams_scheduled_meeting_subscription(
            microsoft_user_id=microsoft_user_id,
            subscription_id=subscription_id,
            user_id=user_id,
            department_id=department_id,
            refresh_token=refresh_token
        )
        
        if integrations_model_response["status"] == "success" and microsoft_user_id_response["status"] == "success":
            http_code = 200
        else:
            http_code = 500

        return JsonResponse({
            "status": http_code,
            "data": {
                "integrations_model_response": integrations_model_response,
                "microsoft_user_id_response": microsoft_user_id_response,
            }
        })

@csrf_exempt
def update_user_context(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data["user_id"]
        user_id_obj = ObjectId(user_id)
        user_context = data["user_context"]

        user_model_response = user_model.change_context(user_id_obj, user_context)
        if user_model_response["status"] == "success":
            http_code = 200
        else:
            http_code = 500

        return JsonResponse({
            "status": http_code,
            "data": user_model_response["data"]
        })

# ==================================
# department related endpoints 
# ==================================

@csrf_exempt
def create_department(request):
    if request.method == "POST":
        data = json.loads(request.body)
        department_name = data['department_name']
        company_name = data['company_name']

        all_departments_path = "/home/jakobschiller/devour/department_vector_databases"

        department_collection_response = department_model.add_department(
            department_name=department_name,
            company_name=company_name,
            all_departments_path=all_departments_path
        )

        # create and save new vector db for department
        department_id = department_collection_response["data"]["department_id"]
        vector_db_path = f"{all_departments_path}/{department_id}"

        Path(vector_db_path).mkdir()

        vector_database = Database(
            path_to_db=vector_db_path,
            collection_name=department_id,
        )

        if department_collection_response["status"] == "success":
            http_code = 200
        else:
            http_code = 500
            
        return JsonResponse({
            "status": http_code,
            "data": department_collection_response
        })

@csrf_exempt
def delete_department(request):
     if request.method == "DELETE":
        data = json.loads(request.body)
        department_id = ObjectId(data['department_id'])
        user_ids = department_model.get_employees(
            department_id=department_id
        )["data"]

        # delete each user in department

        deleted_users = []
        user_with_failed_deletion = []
        for user_id in user_ids:
            deleted_user = user_model.delete_user(
                user_id=user_id
            )

            if deleted_user["status"] == "success":
                deleted_users.append(deleted_user)
            else:
                user_with_failed_deletion.append(user_id)

            # delete chats of user
            chat_ids = user_model.get_chat_ids(user_id)["data"]

            for chat_id in chat_ids:
                deleted_chat = chat_model.delete_chat(
                    chat_id=chat_id
                )
                
        all_users_deleted = True if len(deleted_users) == len(user_ids) else False

        # delete department
        deleted_department = department_model.delete_department(
            department_id=department_id
        )

        if deleted_department["status"] == "success" and all_users_deleted:
            return JsonResponse({
                "status": 200,
                "data": "Deleted department with all users within and all the chats of the users."
            })
        
        else:
            return JsonResponse({
                "status": 500,
                "data": {
                    "department_collection_response": deleted_department,
                    "user_collection_response": {
                        "deleted_user": deleted_users,
                        "user_with_failed_deletion": user_with_failed_deletion
                    }
                }
            })

# ==================================
# chat related endpoints 
# ==================================

# endpoint to create new chat
@csrf_exempt
def create_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = ObjectId(data['user_id'])
        user_prompt = data['user_prompt']

        chat_title = "Neuer Chat"

        # create chat in chat collection
        chat_collection_response = chat_model.new_chat(
            user_id=user_id,
            title=chat_title
        )

        chat_id = ObjectId(chat_collection_response["data"]['_id'])

        # load info of new chat
        chat_collection_response = chat_model.get_chat_data(chat_id)

        if chat_collection_response["status"] == "success":
            # add chat to user in user collection 
            user_collection_response = user_model.add_chat(
                user_id=user_id,
                chat_id=chat_id,
                chat_title=chat_title
            )

            if user_collection_response["status"] == "success":

                # send first prompt to new chat
                prompt_response = new_prompt(chat_id, user_id, user_prompt)
                prompt_response["data"]["chat_data"] = chat_collection_response["data"]
                return JsonResponse(prompt_response)

            else:
                return JsonResponse({
                    "status":  500,
                    "data": user_collection_response
                })
            
        else:
            return JsonResponse({
                "status":  500,
                "data": chat_collection_response
            })
        

#endpoint to change chat-context
@csrf_exempt
def update_chat_context(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = ObjectId(data['chat_id'])
        chat_context = data['chat_context']

        chat_collection_response = chat_model.update_chat_context(chat_id=chat_id, chat_context=chat_context)

        if chat_collection_response["status"] == "success":
            
            return JsonResponse({
                "status": 200,
                "data": chat_collection_response
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": chat_collection_response
            })


# endpoint to load and open existing chat
@csrf_exempt
def load_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = data['chat_id']
        chat_id_obj = ObjectId(chat_id)

        chat_collection_response = chat_model.get_chat_data(chat_id_obj)

        if chat_collection_response["status"] == "success":
            
            return JsonResponse({
                "status": 200,
                "data": chat_collection_response["data"] #decrypted_chat_data
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": chat_collection_response
            })

@csrf_exempt
def user_prompt(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = ObjectId(data['chat_id']) # containts id and chat history
        user_id = ObjectId(data['user_id'])
        user_prompt = data['user_prompt']
        return JsonResponse(new_prompt(chat_id, user_id, user_prompt))

def new_prompt(chat_id, user_id, user_prompt):
        chat_collection_response = chat_model.get_chat_data(chat_id=chat_id)

        if chat_collection_response["status"] == "success":

            # load chat history
            current_chat_history = []
            chat_history = chat_collection_response["data"]["content"]
            for chat in chat_history:
                exchange = {
                    "user_prompt": chat["user_prompt"],
                    "chatbot_response": chat["chatbot_response"]
                }
                current_chat_history.append(exchange)
                
            
            # load chat context
            chat_context = chat_collection_response["data"]["context"]

            # load user preferences
            user_collection_response = user_model.get_user_data(user_id=user_id)
            if user_collection_response['status'] == "success":
                user_data = user_collection_response['data']
                user_department = user_data['department_name']
                user_department_id = ObjectId(user_data['department_id'])
                user_name = user_data['name']
                user_role = user_data['role']
                user_individual_prompt = user_data['configurations']['individual_prompt']
                user_tone = user_data['configurations']['tone']
                user_context = user_data['context']

            # look whether title needs to be generated
            if chat_collection_response["data"]['title'] == "Neuer Chat":
                generate_auto_title = True
            
            else:
                generate_auto_title = False

            # load vector db path and collection name
            department_collection_response = department_model.get_vector_db_data(user_department_id)
            if department_collection_response['status'] == "success":
                vector_db_collection = department_collection_response['data']['vector_db_collection']
                vector_db_dir_path = department_collection_response['data']['vector_db_dir_path']
            else:
                return {
                    "status": 500,
                    "data": {
                        "department_collection_response": department_collection_response
                    }
                }

            # load or create chat object and give instructions
            chat_cache.update_chats()
            chat = chat_cache.get_chat(chat_id=chat_id) 
            if chat == None:
                # create new chat object and store in chat cache
                chat = Chat(
                    chat_history=current_chat_history,
                    chat_context=chat_context,
                    department=user_department,
                    user_name=user_name,
                    user_role=user_role,
                    individual_prompt=user_individual_prompt,
                    tone=user_tone,
                    user_context=user_context,
                    chat_context_limit=5, # amount of last exchanges that are provided to chatbot with each new prompt
                    collection_name=vector_db_collection,
                    db_path=vector_db_dir_path
                )
                chat_cache.add_chat(chat_obj=chat, chat_id=chat_id)
            
            chatbot_response, auto_title = chat.prompt_model(user_prompt=user_prompt, generate_auto_title=generate_auto_title)

            # update chat data in database
            if generate_auto_title:
                # update data in chat collection
                update_chat_history_response = chat_model.handle_prompt(
                    chat_id=chat_id,
                    user_prompt=user_prompt,
                    chatbot_response=chatbot_response,
                    auto_title=auto_title
                )
                # add new title to chat in user collection
                user_model.update_chat_title(user_id=user_id, chat_id=chat_id, new_chat_title=auto_title)
            else:
                # update data in chat collection
                update_chat_history_response = chat_model.handle_prompt(
                    chat_id=chat_id,
                    user_prompt=user_prompt,
                    chatbot_response=chatbot_response,
                )

            # update chat editedAt time in user collection
            editedAtTime = user_model.update_chat_editing_time(user_id=user_id, chat_id=chat_id)["data"]

            if update_chat_history_response["status"] == "success":
                exchange_obj = {
                    "user_prompt": user_prompt,
                    "chatbot_response": chatbot_response
                }

                if generate_auto_title:
                    return {
                        "status": 200,
                        "data": {
                            "exchange": exchange_obj,
                            "title": auto_title,
                            "editedAt": editedAtTime
                        }
                    }
                else:
                    return {
                        "status": 200,
                        "data": {
                            "exchange": exchange_obj,
                            "editedAt": editedAtTime
                        }
                    }

            else:
                return {
                    "status": 500,
                    "data": f"Couldn't update chat collection with new data from chatbot; chat collection response: {update_chat_history_response}"
                }

        else:
            return JsonResponse({
                "status": 500,
                "data": f"Couldn't load chat history from collection; chat collection response: {chat_collection_response}"
            })

# endpoint to change chat_title
@csrf_exempt
def change_chat_title(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = ObjectId(data['chat_id'])
        user_id = ObjectId(data["user_id"])
        new_title = data['new_title']

        chat_collection_response = chat_model.change_chat_title(
            chat_id=chat_id,
            new_title=new_title
        )


        user_collection_response = user_model.update_chat_title(
            user_id=user_id,
            chat_id=chat_id,
            new_chat_title=new_title
        )

        if chat_collection_response["status"] == "success" and user_collection_response == "success":
            return JsonResponse({
                "status": 200,
                "data": {
                    "chat_collection_response": chat_collection_response["data"],
                    "user_collection_response": user_collection_response["data"]
                    }
            })
        else:
            return JsonResponse({
                "status": 500,
                "data": {
                    "chat_collection_response": chat_collection_response["data"],
                    "user_collection_response": user_collection_response["data"]
                    }
            })

# endpoint to add additional user
@csrf_exempt
def add_additional_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = ObjectId(data['user_id'])
        chat_id = ObjectId(data['chat_id'])

        # add user_id to chat in database
        chat_collection_response = chat_model.add_additional_user(
            chat_id=chat_id,
            user_id=user_id
        )

        if chat_collection_response["status"] == "success":

            # add chat_id to user in database
            user_collection_response = user_model.add_chat(
                user_id=user_id,
                chat_id=chat_id
            )

            if user_collection_response["status"] == "success":
                return JsonResponse({
                    "status": 200,
                    "data": {
                        "user_id": user_id,
                        "chat_id": chat_id
                    }
                })

            else:
                return JsonResponse({
                    "status": 500,
                    "data": user_collection_response
                })

        else:
            return JsonResponse({
                "status": 500,
                "data": chat_collection_response
            })

# endpoint to remove additional user
@csrf_exempt
def remove_additional_user(request):
    if request.method == "DELETE":
        data = json.loads(request.body)
        user_id = ObjectId(data['user_id'])
        chat_id = ObjectId(data['chat_id'])

        # remove user_id from chat in database
        chat_collection_response = chat_model.remove_additional_user(
            chat_id=chat_id,
            user_id=user_id
        )

        if chat_collection_response["status"] == "success":

            # remove chat_id from user in database
            user_collection_response = user_model.delete_chat(
                user_id=user_id,
                chat_id=chat_id
            )

            if user_collection_response["status"] == "success":
                return JsonResponse({
                    "status": 200,
                    "data": {
                        "chat_collection_response": chat_collection_response,
                        "user_collection_response": user_collection_response
                    }
                })

            else:
                return JsonResponse({
                    "status": 500,
                    "data": user_collection_response
                })


        else:
            return JsonResponse({
                "status": 500,
                "data": chat_collection_response
            })

# delete chat
@csrf_exempt
def delete_chat(request):
    if request.method == "DELETE":
        data = json.loads(request.body)
        chat_id = ObjectId(data["chat_id"])
        user_id = ObjectId(data["user_id"])

        # delete chat from chat collection
        chat_collection_response = chat_model.delete_chat(
            chat_id=chat_id
        )

        if chat_collection_response["status"] == "success":

            # delete chat in user data
            user_collection_response = user_model.delete_chat(
                user_id=user_id,
                chat_id=chat_id
            )

            if user_collection_response["status"] == "success":
                return JsonResponse({
                    "status": 200,
                    "data": {
                        "chat_collection_response": chat_collection_response,
                        "user_collection_response": user_collection_response
                    }
                })

            else:
                return JsonResponse({
                    "status": 500,
                    "data": user_collection_response
                })

        else:
            return JsonResponse({
                "status": 500,
                "data": chat_collection_response
            })
