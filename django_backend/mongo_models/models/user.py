from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import bcrypt
from cryptography.fernet import Fernet
import base64
import os
from pathlib import Path
from datetime import datetime


def getCurrentTime():
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

class UserModel:
    def __init__(self, mongo_host_port: str):
        self.collection = "users"
        self.client = MongoClient(mongo_host_port)
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]
        self.encryptor = ""

    def get_chat_ids(self, user_id: ObjectId):
        user_data = self.collection.find_one({"_id": user_id})
        if user_data != None:
            return {"status": "success", "data": user_data['active_chats']}
        else:
            msg = f"No user with id {user_id} was found. Mongo response: {user_data}"
            print(msg)
            return {"status": "failure", "data": []}
        
    def update_chat_title(self, user_id: ObjectId, chat_id: ObjectId, new_chat_title: str):
        try:
            response_code = self.collection.update_one({"_id": user_id, "active_chats.chat_id": chat_id}, {"$set": {"active_chats.$.chat_title": new_chat_title}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"Updated chat title of chat {chat_id}")
                return {"status": "success", "data": new_chat_title}
            else:
                msg = f"Couldn't update chat title of chat: {chat_id}."
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Error while trying to update chat title of chat {chat_id}. Error: ", e)
            return {"status": "failure", "data": e}
        
    def update_chat_editing_time(self, user_id: ObjectId, chat_id: ObjectId):
        try:
            current_time = getCurrentTime()
            response_code = self.collection.update_one({"_id": user_id, "active_chats.chat_id": chat_id}, {"$set": {"active_chats.$.editedAt": current_time}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"Updated editedAt time of chat {chat_id}")
                return {"status": "success", "data": current_time}
            else:
                msg = f"Couldn't update editedAt time of chat: {chat_id}."
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Error while trying to update editedAt time of chat {chat_id}. Error: ", e)
            return {"status": "failure", "data": e}

    def transform_object_ids(self, user_data): # method to convert all ObjectIds to strings
        user_data['_id'] = str(user_data['_id'])
        user_data['department_id'] = str(user_data['department_id'])

        for i in range(0, len(user_data['active_chats'])):
            user_data['active_chats'][i]["chat_id"] = str(user_data['active_chats'][i]["chat_id"])
        return user_data

    def add_user(self,
                 name: str,
                 password: str,
                 email: str,
                 role: str,
                 department_id: ObjectId,
                 department_name: str,
                 company_name: str,
                 is_admin: bool
                 ):
        try:
            user_data = {
                "password": self.__hash_pswrd(password),
                "name": name,
                "email": email,
                "role": role,
                "department_id": department_id,
                "department_name": department_name,
                "company_name": company_name,
                "active_chats": [],
                "integrations": {
                    "microsoft_user_id": ""
                },
                "is_admin": is_admin,
                "configurations": {
                    "individual_prompt": "",
                    "tone": "", # später weitere Konfigurationen ergänzen
                },
                "context": ""
            }

            response_code = self.collection.insert_one(user_data) # ret_code includes ObjectId of x user

            user_data['_id'] = response_code.inserted_id
            user_data.pop('password', None)
            user_data.pop('integrations', None)

            user_data = self.transform_object_ids(user_data)

            print(f"New user {name} was saved to db")
            return {"status": 'success', "data": user_data}

        except Exception as e:
            print(f"User {name} couldn't be saved to db. Error: ", e)
            return {"status": 'failure', "data": e}

    def delete_user(self, user_id: ObjectId):
        try:
            response_code = self.collection.delete_one({ "_id": user_id })
            msg = f"Deleted user with id {user_id}."
            print(msg)
            return {"status": "success", "data": msg}
        
        except Exception as e:
            print(f"Exception occured while deleting user with id {user_id}", e)
            return {"status": "failure", "data": e}
        
    def change_context(self, user_id: ObjectId, new_context: str):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$set": {"context": new_context}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"Context of user with id {user_id} was updated.")
                return {"status": "success", "data": new_context}
            else:
                msg = f"Couldn't update context of user with id: {user_id}"
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Couldn't edit context of user with id {user_id}. Error: ", e)
            return {"status": "failure", "data": e}

    def get_user_data(self, user_id: ObjectId):
        try:
            user_data = self.collection.find_one({'_id': user_id})
            if user_data != None:

                user_data.pop('password', None)
                user_data.pop('integrations', None)

                user_data = self.transform_object_ids(user_data)

                print(f"Fetched data of user {user_id} from collection.")
                return {"status": "success", "data": user_data}
            else:
                msg = f"Couldn't find user data for user with id {user_id} in collection"
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Couldn't get data of user {user_id} from collection. Error: ", e)
            return {"status": "failure", "data": e}

    def make_admin(self, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$set": {"is_admin": True}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"User with id {user_id} is now an admin.")
                return {"status": "success", "data": user_id}
            else:
                msg = f"Couldn't make user with id: {user_id} an admin."
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Couldn't make user with id {user_id} an admin. Error: ", e)
            return {"status": "failure", "data": e}

    def make_non_admin(self, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$set": {"is_admin": False}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"User with id {user_id} is no admin anymore.")
                return {"status": "success", "data": user_id}
            else:
                msg = f"Couldn't make user with id: {user_id} not an admin."
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Error while trying to make user with id {user_id} not an admin. Error: ", e)
            return {"status": "failure", "data": e}
        
    def add_chat(self, user_id: ObjectId, chat_id: ObjectId, chat_title):
        try:
            chat = {
                "chat_id": chat_id,
                "chat_title": chat_title,
                "editedAt": getCurrentTime()
                }

            response_code = self.collection.update_one(
                {"_id": user_id},
                {"$push": {"active_chats": chat}}
            )
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                msg = f"Added new chat to to user with id {user_id}"
                print(msg)
                return {"status": "success", "data": chat}
            else:
                msg = f"Couldn't add new chat. User id might be wrong: {user_id}"
                print(msg)
                return {"status": "failure", "data": msg}
        
        except Exception as e:
            print(f"Couldn't add new chat for user with id {user_id}", e)
            return {"status": "failure", "data": e}

    def delete_chat(self, user_id: ObjectId, chat_id: ObjectId):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$pull": {"active_chats": {"chat_id": chat_id}}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                msg = f"Chat with id {chat_id} was deleted from user with id {user_id}"
                return {"status": "success", "data": msg}
            else:
                msg = f"Couldn't delete chat. User id might be wrong: {user_id}"
                return {"status": "failure", "data": msg}
        except Exception as e:
            print(f"Couldn't delete chat with id {chat_id} from user with id {user_id}")
            return {"status": "failure", "data": e}

    def set_microsoft_user_id(self, user_id: ObjectId, microsoft_user_id: str):
        try:
            response_code = self.collection.update_one({'_id': user_id}, {"$set": {"integrations": {"microsoft_user_id": microsoft_user_id}}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                msg = f"Updated microsoft user id of user {user_id}"
                return {"status": "success", "data": msg}
            else:
                msg = f"Couldn't update microsoft user id of user {user_id}"
                return {"status": "failure", "data": msg}
        except Exception as e:
            msg = f"Error while updating microsoft user id of user {user_id}. Error: {e}"
            return {"status": "failure", "data": e}

    def change_configuration(self, user_id: ObjectId, config: str, changed_value: str):
        # config could be 'individual_prompt', 'tone' etc
        try:
            if config == 'individual_prompt' or config == 'tone':
                response_code = self.collection.update_one({ '_id': user_id}, {"$set": {f"configurations.{config}": changed_value}})
                updated_data = response_code.raw_result["updatedExisting"]
                if updated_data:
                    print(f"Successfully changed {config} to {changed_value}")
                    return {"status": "success", "data": str(user_id)}
                else:
                    msg = f"Couldn't update document, check user id: {str(user_id)}"
                    return {"status": "failure", "data": msg}
            else:
                msg = f"Configuration {config} is not valid."
                return {"status": "failure", "data": msg}
        except Exception as e:
            print(f"Error while trying to change configuration {config} to {changed_value} for user {str(user_id)} ", "Error: ", e)
            return {"status": "failure", "data": e}

    def encrypt_text(self, text):
        key = self.__get_encryption_key()
        cipher = Fernet(key)
        encrypted_token = cipher.encrypt(bytes(text, 'utf-8'))
        return encrypted_token
    
    def decrypt_text(self, text):
        key = self.__get_encryption_key()
        cipher = Fernet(key)
        decrypted_token = cipher.decrypt(text)
        return decrypted_token

    def __get_encryption_key(self): # private method, shouldn't be visible from outside
        load_dotenv()
        return os.getenv('ENCRYPTION_KEY')

    def __hash_pswrd(self, text): # private method, shouldn't be visible from outside
        salt = bcrypt.gensalt()
        hashed_text = bcrypt.hashpw(text.encode('utf-8'), salt)
        return hashed_text
    
    def login(self, email: str, password: str):
        user_data = self.collection.find_one({"email": email})
        if user_data != None:
            hashed_password = user_data['password']
            pswrd_correct = bcrypt.checkpw(password.encode('utf-8'), hashed_password)
            if pswrd_correct:
                user_data.pop('password', None)
                user_data.pop('integrations', None)
                user_data = self.transform_object_ids(user_data)

                print("User was found and password is correct.")
                return {"status": 'success', "data": user_data}
            else:
                msg = "Password not correct."
                print(msg)
                return {"status": 'failure', "data": msg}

        else:
            msg = f"No user with email: {email} was found."
            print(msg)
            return {"status": 'failure', "user_data": msg} 

    def update_context(self, user_id: ObjectId, new_context: str):
        try:
            response_code = self.collection.update_one({ '_id': user_id}, {"$set": {'context': new_context}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"Successfully updated user context of user {user_id}")
                return {"status": "success", "data": user_id}
            else:
                msg = f"Couldn't update document, check user id: {user_id}"
                return {"status": "failure", "data": msg}
        except Exception as e:
            print(f"Error while trying to update context for user {user_id} ", "Error: ", e)
            return {"status": "failure", "data": e}