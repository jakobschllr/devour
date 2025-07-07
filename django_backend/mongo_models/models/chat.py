from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

from encryption.text_encrypt import Encryptor

DATEnTIME = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

class ChatModel:
    def __init__(self, mongo_host_port: str):
        self.collection = "chats"
        self.client = MongoClient(mongo_host_port)
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]        

    def new_chat(self,
                 user_id: ObjectId,
                 title: str
                 ):
        try:
            data = {
                "title": "Neuer Chat",
                "primary_user": user_id,
                "additional_users": [],
                "content": [],
                "changed_at": DATEnTIME,
                "context": ""
            }

            response_code = self.collection.insert_one(data)
            chat_id = response_code.inserted_id

            data['_id'] = str(chat_id)
            data['primary_user'] = str(data['primary_user'])

            print(f"Added new chat with id {chat_id} to chat collection.")
            return {"status": "success", "data": data}

        except Exception as e:
            print("Connection to local MongoDB Server on port 27017 failed.", "Error: ", e)
            return {"status": "failure", "data": e}

    def update_chat_context(self, chat_id: ObjectId, chat_context: str):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$set": {'context': chat_context}})
            changed_chat_context = response_code.raw_result["updatedExisting"]
            if changed_chat_context:
                msg = "Changed chat context of chat " + str(chat_id)
                print(msg)
                return {"status": "success", "data": msg}
            else:
                msg = "Couldn't update chat context of chat" + str(chat_id)
                print(msg)
                return {"status": "failure", "data": msg}
        except Exception as e:
            msg = "Database Error while trying to update chat with id " + str(chat_id)
            print(msg)
            return {"status": "failure", "data": msg}

    def delete_chat(self, chat_id: ObjectId):
        try:
            response_code = self.collection.delete_one({ "_id": chat_id })
            print(response_code)
            if response_code.deleted_count != 0:
                msg = f"Deleted chat with id {chat_id}"
                print(msg)
                return {"status": "success", "data": msg}
            else:
                msg = f"Deletion unsuccessful. Check id: {chat_id}"
                print(msg)
                return {"status": "failure", "data": msg}
        except Exception as e:
            print("Exception occured while deleting chat with id ", chat_id, "Error: ", e)
            return {"status": "failure", "data": e}

    def get_chat_data(self, chat_id: ObjectId):
        try:
            data = self.collection.find_one({'_id': chat_id})

            data['_id'] = str(chat_id)
            data['primary_user'] = str(data['primary_user'])

            if data != None:
                print("Fetched chat data of chat with id ", chat_id)
                return {"status": "success", "data": data}
            else:
                msg = f"No chat with chat-id {chat_id} was found."
                print(msg)
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print("Error fetching chat data: ", e)
            return {"status": "failure", "data": e}

    def handle_prompt(self, chat_id: ObjectId, user_prompt: str, chatbot_response: str, auto_title=None):
        try:
            exchange = {
                "user_prompt": user_prompt,
                "chatbot_response": chatbot_response
            }

            # update chat history
            response_code = self.collection.update_one({ '_id': chat_id}, {"$push": {'content': exchange}})

            # update changed_at
            self.collection.update_one({ '_id': chat_id}, {"$set": {'changed_at': DATEnTIME}})

            if auto_title != None:
                self.collection.update_one({ '_id': chat_id}, {"$set": {'title': auto_title}})

            if response_code != None:
                msg = f"Updated chat with id {chat_id} with prompt and chatbot response"
                print(msg)
                return {"status": "success", "data": msg}
            else:
                msg = f"Couldn't update chat with new data. Check chat id: {chat_id}"
                return {"status": "failure", "data": msg}

        except Exception as e:
            print(e)
            return {"status": "failure", "data": e}

    def change_chat_title(self, chat_id: ObjectId, new_title: str):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$set": {'title': new_title}})
            self.collection.update_one({ '_id': chat_id}, {"$set": {'changed_at': DATEnTIME}})
            changed_chat_title = response_code.raw_result["updatedExisting"]
            if changed_chat_title:
                print("Changed chat title of chat with id ", chat_id)
                return {"status": "success", "data": new_title}
            else:
                msg = f"No chat with id {chat_id} gefunden."
                print(msg)
                return {"status": "failure", "data": msg}

        except Exception as e:
            print("Couldn't change title of chat with id ", chat_id, "Error: ", e)
            return {"status": "failure", "data": e}

    def add_additional_user(self, chat_id: ObjectId, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$push": {'additional_users': user_id}})
            self.collection.update_one({ '_id': chat_id}, {"$set": {'changed_at': DATEnTIME}})
            
            updated_chat_collection = response_code.raw_result["updatedExisting"]
            
            if updated_chat_collection:
                msg = f"Added user with id {user_id} to chat {chat_id}"
                print(msg)
                return {"status": "success", "data": msg}
            else:
                msg = f"Either user id {user_id} or chat id {chat_id} is invalid."
                return {"status": "failure", "data": msg}

        except Exception as e:
            print(f"Couldn't add user with id {user_id} to chat {chat_id}. Error: ", e)
            return {"status": "failure", "data": e}

    def remove_additional_user(self, chat_id: ObjectId, user_id: ObjectId):
        try:
            response_code = self.collection.update_one({ '_id': chat_id}, {"$pull": {'additional_users': user_id}})
            self.collection.update_one({ '_id': chat_id}, {"$set": {'changed_at': DATEnTIME}})

            updated_chat_collection = response_code.raw_result["updatedExisting"]

            if updated_chat_collection:
                msg = f"Removed user with if {user_id} from chat with id {chat_id}"
                print(msg)
                return {"status": "success", "data": msg}
            else:
                msg = f"Couldn't remove user with id {user_id} from chat with id {chat_id}. Id(s) might be wrong."
                print(msg)
                return {"status": "failure", "data": msg}

        except Exception as e:
            print(f"Couldn't remove user with {user_id} from chat {chat_id}. Error: ", e)
            return {"status": "failure", "data": e}