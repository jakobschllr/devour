from pymongo import MongoClient
from bson import ObjectId
import bcrypt

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
                "password": self.hash_pswrd(password),
                "name": name,
                "email": email,
                "role": role,
                "department_id": department_id,
                "department_name": department_name,
                "company_name": company_name,
                "active_chats": [],
                "external_integrations": [],
                "is_admin": is_admin,
            }

            ret_code = self.collection.insert_one(data)
            print(f"New user {name} was saved to db")
            return True

        except Exception:
            print(f"User {name} couldn't be saved to db")

    def delete_user(self, user_id: ObjectId):
        try:
            self.collection.delete_one({ "_id": user_id })
            print(f"Deleted user with id {user_id}.")
            return True
        
        except Exception as e:
            print(f"Couldn't delete user with id {user_id}", e)
            return False
        
    def add_admin(self, user_id: ObjectId):
        try:
            self.collection.update_one({"_id": user_id}, {"$set": {"is_admin": True}})
            print(f"User with id {user_id} is now an admin.")
            return True
        except Exception as e:
            print(f"Couldn't make user with id {user_id} an admin.")
            return False
        
    def add_chat(self, user_id: ObjectId, chat_id: ObjectId):
        try:
            self.collection.update_one(
                {"_id": user_id},
                {"$push": {"active_chats": chat_id}}
            )
            print(f"Added new chat to to user with id {user_id}")
            return True
        
        except Exception as e:
            print(f"Couldn't add new chat for user with id {user_id}", e)
            return False

    def delete_chat(self, user_id: ObjectId, chat_id: ObjectId):
        try:
            self.collection.update_one({"_id": user_id}, {"$pull": {"active_chats": chat_id}})
            print(f"Chat with id {chat_id} was deleted from user with id {user_id}")
            return True
        except Exception as e:
            print(f"Couldn't delete chat with id {chat_id} from user with id {user_id}")
            return False
        
    def hash_pswrd(self, text):
        salt = bcrypt.gensalt()
        hashed_text = bcrypt.hashpw(text.encode('utf-8'), salt)
        return hashed_text
    
    def check_pswrd(self, user_id: ObjectId, password: str):
        for doc in self.collection.find_one({"_id": user_id}):
            user_data = doc
        if user_data != None:
            hashed_password = user_data['password']
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

        else:
            print("User data couldn't be found.")
            return False