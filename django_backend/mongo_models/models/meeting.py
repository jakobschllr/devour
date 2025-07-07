from pymongo import MongoClient
from bson import ObjectId

class MeetingModel:
    def __init__(self, mongo_host_port):
        self.collection = "meetings"
        self.client = MongoClient(mongo_host_port)
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]

    def add_meeting(self,
                    meeting_title: str,
                    date: str,
                    department_id: ObjectId,
                    transcript_id: str,
                    participants: list,
                    platform: str):

        # platform is microsoft_teams, zoom, google_meet

        try:
            data = {
                "meeting_title": meeting_title,
                "date": date,
                "department_id": department_id,
                "transcript_id": transcript_id,
                "was_scraped": False,
                "participants": participants,
                "platform": platform
            }

            ret_code = self.collection.insert_one(data)
            print(f"Meeting {meeting_title} was added to database: ", ret_code)
            return True

        except Exception:
            print(f"Meeting {meeting_title} could not be saved to database.")

    def change_transcript_state(self, meeting_id: ObjectId):
        try:
            self.collection.update_one({"_id": meeting_id}, {"$set": {"was_scraped": True}})
            print(f"was_scraped state of meeting with id {meeting_id} set to True.")
            return True
        except Exception as e:
            print(f"was_scraped state of meeting with id {meeting_id} couldn't be set to True.", e)
            return False