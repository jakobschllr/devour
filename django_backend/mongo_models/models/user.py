from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import bcrypt
from cryptography.fernet import Fernet
import base64
import os

class UserModel:
    def __init__(self):
        self.collection = "users"
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]

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
            data = {
                "password": self.__hash_pswrd(password),
                "name": name,
                "email": email,
                "role": role,
                "department_id": department_id,
                "department_name": department_name,
                "company_name": company_name,
                "active_chats": [],
                "integrations": {
                    "microsoft_teams": {
                        "refresh_token": ""
                    }
                },
                "is_admin": is_admin,
                "configurations": {
                    "indivivual_prompt": "",
                    "tone": "", # später weitere Konfigurationen ergänzen
                }
            }

            response_code = self.collection.insert_one(data) # ret_code includes ObjectId of new user
            print(response_code)
            print(f"New user {name} was saved to db")
            return True

        except Exception:
            print(f"User {name} couldn't be saved to db")

    def delete_user(self, user_id: ObjectId):
        try:
            response_code = self.collection.delete_one({ "_id": user_id })
            print(response_code)
            print(f"Deleted user with id {user_id}.")
            return True
        
        except Exception as e:
            print(f"Couldn't delete user with id {user_id}", e)
            return False
        
    def get_user_data(self, user_id: ObjectId):
        try:
            user_data = self.collection.find_one({'_id': user_id})
            if user_data != None:

                user_data.pop('password', None)
                user_data.pop('integrations', None)
                user_data['_id'] = str(user_data['_id'])
                user_data['department_id'] = str(user_data['department_id'])

                for i in range(0, len(user_data['active_chats'])):
                    user_data['active_chats'][i] = str(user_data['active_chats'][i])

                print(f"Fetched data of user {user_id} from collection.")
            else:
                print(f"No user with user id None was found in collection.")
            
            return user_data

        except Exception as e:
            print(f"Couldn't get data of user {user_id} from collection. Error: ", e)
            return None

    def make_admin(self, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$set": {"is_admin": True}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"User with id {user_id} is now an admin.")
                return True
            else:
                print("Couldn't make user an admin. User id might be wrong: ", user_id)
                return False
        except Exception as e:
            print(f"Couldn't make user with id {user_id} an admin. Error: ", e)
            return False

    def make_no_admin(self, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$set": {"is_admin": False}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"User with id {user_id} is no admin anymore.")
                return True
            else:
                print("Couldn't make user not an admin. User id might be wrong: ", user_id)
                return False
        except Exception as e:
            print(f"Couldn't make user with id {user_id} not an admin. Error: ", e)
            return False
        
    def add_chat(self, user_id: ObjectId, chat_id: ObjectId):
        try:
            response_code = self.collection.update_one(
                {"_id": user_id},
                {"$push": {"active_chats": chat_id}}
            )
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"Added new chat to to user with id {user_id}")
                return True
            else:
                print("Couldn't add new chat. User id might be wrong: ", user_id)
                return False
        
        except Exception as e:
            print(f"Couldn't add new chat for user with id {user_id}", e)
            return False

    def delete_chat(self, user_id: ObjectId, chat_id: ObjectId):
        try:
            response_code = self.collection.update_one({"_id": user_id}, {"$pull": {"active_chats": chat_id}})
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print(f"Chat with id {chat_id} was deleted from user with id {user_id}")
                return True
            else:
                print("Couldn't delete chat. User id might be wrong: ", user_id)
                return False
        except Exception as e:
            print(f"Couldn't delete chat with id {chat_id} from user with id {user_id}")
            return False

    def set_ms_teams_refresh_token(self, user_id: ObjectId, refresh_token: str):
        try:
            encrypted_token = self.encrypt_text(refresh_token)
            self.collection.update_one({'_id': user_id}, {"$set": {"integrations": {"microsoft_teams": {"refresh_token": encrypted_token}}}})
            print("Couldn't add ms teams refresh token. User id might be wrong: ", user_id)
            return False
        except Exception as e:
            print(f"Couldn't add new microsoft teams refesh token for user {user_id}")
            return False

    def get_msteams_refresh_token(self, user_id: ObjectId):
        try:
            user_data = self.collection.find_one({'_id': user_id})
            if user_data != None:
                encrypted_refresh_token = user_data["integrations"]["microsoft_teams"]["refresh_token"]
                decrypted_refresh_token = self.decrypt_text(encrypted_refresh_token)
                return decrypted_refresh_token
        
        except Exception as e:
            print(f"Couldn't get microsoft teams refresh token for user {user_id}")
            return False

    def change_configuration(self, user_id: ObjectId, config: str, change_value: str):
        # config could be 'individual_prompt', 'tone' etc
        try:
            if config == 'indivivual_prompt' or config == 'tone':
                response_code = self.collection.update_one({ '_id': user_id}, {"$set": {'configurations': {config: change_value}}})
                print(response_code)
                print(f"Successfully changed {config} to {change_value}")
                return True
            else:
                print(f"Configuration {config} is not valid.")
                return False
        except Exception as e:
            print(f"Couldn't change configuration {config} to {change_value} ", "Error: ", e)
            return False

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
    
    def check_pswrd(self, user_id: ObjectId, password: str):
        user_data = self.collection.find_one({"_id": user_id})
        if user_data != None:
            hashed_password = user_data['password']
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

        else:
            print("User data couldn't be found.")
            return False