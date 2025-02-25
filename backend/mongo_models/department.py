from pymongo import MongoClient
from bson import ObjectId

class DepartmentModel:
    def __init__(self):
        self.collection = "departments"
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]

    def get_main_vector_db_id(self, department_id: ObjectId):
        main_vector_db_id = ""

        for doc in self.collection.find_one({"_id": department_id}):
            if doc != None:
                main_vector_db_id = doc["main_vector_db_id"]

        if main_vector_db_id != "":
            print(f"Vector db id  for department {department_id} was found")
            return main_vector_db_id
        else:
            print(f"No vector db id found for department {department_id}")
            return None

    def add_department(self,
                       department_name: str,
                       company_name: str,
                       admin_user: dict,
                       ):
        
        try:
            data = {
                "department_name": department_name,
                "company_name": company_name,
                "employees": [admin_user],
                "main_vector_db_id": "",
                "meetings": []
            }

            ret_obj = self.collection.insert_one(data)
            id_string = ret_obj.inserted_id
            department_id = ObjectId(id_string)

            # set main_vector_db_id:
            vector_db_id = id_string + "_main_vector_db"
            self.collection.update_one(
                {"_id": department_id},
                {"$set": {"main_vector_db_id": vector_db_id}}
            )

            print(f"New department with id {id_string} was saved in collection {self.collections}")
            return True

        except Exception as e:
            print(f"New department {department_name} couldn't be saved to collection {self.collection}. Error: ", e)
            return None

    def delete_department(self, department_id: ObjectId):
        try:
            self.collection.delete_one({ "_id": department_id })
            print(f"Deleted department with id {department_id}")
            return True
        
        except Exception as e:
            print(f"Couldn't delete department with id {department_id}", e)
            return False
        
    def add_meeting(self, department_id: ObjectId, meeting_data: dict):
        try:
            self.collection.update_one(
                {"_id": department_id},
                {"$push": {"meetings": meeting_data}}
            )
            print("Added meeting data to department document: ", meeting_data)
            return True
        
        except Exception as e:
            print(f"Meeting data couldn't be saved to document of department {department_id}", e)
            return False

    def add_employee(self, department_id: ObjectId, employee_data: dict):
        try:
            self.collection.update_one(
                {"_id": department_id},
                {"$push": {"employees": employee_data}}
            )
            print("Added employee data to department document: ", employee_data)
            return True
        
        except Exception as e:
            print(f"Employee data couldn't be saved to document of department {department_id}", e)
            return False
