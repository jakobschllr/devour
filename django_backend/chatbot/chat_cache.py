from chatbot.chatbot import Chat
from datetime import datetime
from bson import ObjectId

class ChatCache:
    def __init__(self, cache_duration: int):
        self.cache_duration = cache_duration
        self.active_chats = {}

    def add_chat(self, chat_obj: Chat, chat_id: ObjectId):
        chat_id = str(chat_id)
        time_now = datetime.now()
        self.active_chats[chat_id] = {
            "chat_object": chat_obj,
            "edited_at": time_now
        }
        print(f"Added chat {chat_id} to chat cache")

    def get_chat(self, chat_id: ObjectId):
        current_time = datetime.now()
        chat_id = str(chat_id)
        all_chat_ids = [key for key, value in self.active_chats.items()]

        if chat_id in all_chat_ids:
            print(f"Loaded chat {chat_id} from chat cache")
            self.active_chats[chat_id]["edited_at"] = current_time       
            return self.active_chats[chat_id]["chat_object"]
        else:
            print(f"No chat with id {chat_id} in chat cache")
            return None

    def update_chats(self):
        current_time = datetime.now()
        updated_chats = {}
        for key, value in self.active_chats.items():
            time_difference = (current_time - value["edited_at"]).total_seconds()
            if time_difference < self.cache_duration:
                updated_chats[key] = value
            else: print("Chat object with id {key} deleted.")
        
        self.active_chats = updated_chats
        print("Chat Cache: ", self.active_chats)