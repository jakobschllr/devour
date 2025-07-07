from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime as dt, timedelta

class IntegrationModel:
    def __init__(self, mongo_host_port):
        self.collection = "integrations"
        self.client = MongoClient(mongo_host_port)
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]
        self.encryptor = ""
        self.current_date = dt.now()

    # add new subscription id for user for scheduled microsoft teams meetings, in order to get transcripts by microsoft graph api
    def add_ms_teams_scheduled_meeting_subscription(self, microsoft_user_id: str, subscription_id: str, user_id: ObjectId, department_id: ObjectId, refresh_token: str):
        try:
            query = {"_id": microsoft_user_id}
            data = {
                "$set": {
                    "subscription_id": subscription_id,
                    "user_id": user_id,
                    "department_id": department_id,
                    "refresh_token": refresh_token,
                    "refresh_token_expires": self.current_date + timedelta(days=90)
                }
            }

            response = self.collection.update_one(query, data, upsert=True) # upsert=True to update or add if id does not exist

            if response.modified_count != 0 or response.upserted_id is not None:
                msg = f"Added or updated new scheduled ms teams subscription id for user {user_id}."
                print(msg)
                return {"status": "success", "data": msg}
            else:
                msg = f"Couldn't add new scheduled ms teams subscription id for user {user_id}."
                print(msg)
                return {"status": "failure", "data": msg}
        except Exception as e:
            print(f"Error occured while trying to add new subscription id. Error {e}")
            return {"status": "failure", "data": e}
        
    def get_microsoft_refresh_token(self, subscription_id: str):
        try:
            data = self.collection.find_one({'subscription_id': subscription_id})
            if data != None:
                # update expiry date:
                self.collection.update_one({"subscription_id": subscription_id}, {"$set": {"refresh_token_expires": self.current_date + timedelta(days=90)}})
                return {"status": "success", "data": data["refresh_token"]}
            else:
                msg = f"No microsoft user with id {subscription_id} was found in {self.collection}."
                print(msg)
                return {"status": "failure", "data": msg}

        except Exception as e:
            msg = f"Error while trying to find microsoft user with id {subscription_id} in {self.collection}."
            print(msg)
            return {"status": "failure", "data": msg}
        
    def get_user_data(self, subscription_id: str):
        try:
            data = self.collection.find_one({'subscription_id': subscription_id})
            if data != None:
                return {"status": "success", "data": {"user_id": data["user_id"], "department_id": data["department_id"]}}
            else:
                msg = f"Found no user that matches microsoft subscription id  {subscription_id} in {self.collection}."
                print(msg)
                return {"status": "failure", "data": msg}

        except Exception as e:
            msg = f"Error while trying to find user with microsoft subscription id {subscription_id} in {self.collection}."
            print(msg)
            return {"status": "failure", "data": msg}