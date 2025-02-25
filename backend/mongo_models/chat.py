from pymongo import MongoClient


try:
    client = MongoClient("mongodb://localhost:27017")

    db = client["devour_database"]

    collection = db["chats"]

    data = {
        "title": "",
        "data_reference": "",
        "active_users": [
            {
                "user_id": 0,
                "name": "",
            }
        ],
        "configurations": {
            "indivivual_prompt": "",
            "tone": "", # später weitere Konfigurationen ergänzen
        }
    }

    ret_code = collection.insert_one(data)

    print(ret_code)

except Exception:
    print("Connection to local MongoDB Server on port 27017 failed.")