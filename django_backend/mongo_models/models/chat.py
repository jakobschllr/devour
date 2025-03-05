from pymongo import MongoClient
from bson import ObjectId


class ChatModel:
    def __init__(self):
        self.collection = "chats"
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]

    def new_chat(self,
                 user_id: ObjectId,
                 name: str,
                 title: str,
                 ):
        try:
            data = {
                "title": title,
                "primary_user": {
                    "user_id": user_id,
                    "name": name,
                },
                "additional_users": []
            }

            response_code = self.collection.insert_one(data)
            chat_id = response_code.inserted_id
            print(f"Added new chat with id {chat_id} to chat collection.")
            return chat_id

        except Exception as e:
            print("Connection to local MongoDB Server on port 27017 failed.", "Error: ", e)
            return None

    def delete_chat(self, chat_id: ObjectId):
        try:
            response_code = self.collection.delete_one({ "_id": chat_id })
            print(response_code)
            print("Deleted chat with id ", chat_id)
            return True
        except Exception as e:
            print("Couldn't delete chat with id ", chat_id, "Error: ", e)
            return False

    def change_chat_title(self, chat_id: ObjectId, new_title: str):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$set": {'title': new_title}})
            print(response_code)
            print("Changed chat title of chat with id ", chat_id)
            return True

        except Exception as e:
            print("Couldn't change title of chat with id ", chat_id, "Error: ", e)
            return False

    def add_additional_user(self, chat_id: ObjectId, user_data: dict):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$push": {'additional_users': user_data}})
            print(response_code)
            print(f"Added user {user_data['name']} to chat {chat_id}")
            return True

        except Exception as e:
            print(f"Couldn't add user {user_data['name']} to chat {chat_id}. Error: ", e)
            return False

    def remove_additional_user(self, chat_id: ObjectId, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$pull": {'additional_users': {'id': user_id}}})
            print(response_code)
            print(f"Removed user with id {user_id} from chat {chat_id}")
            return True

        except Exception as e:
            print(f"Couldn't remove user with {user_id} from chat {chat_id}. Error: ", e)
            return False