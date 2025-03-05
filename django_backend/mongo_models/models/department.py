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

        department = self.collection.find_one({"_id": department_id})
        if department != None:
            main_vector_db_id = department["main_vector_db_id"]

        if main_vector_db_id != "":
            print(f"Vector db id  for department {department_id} was found")
            return main_vector_db_id
        else:
            print(f"No vector db id found for department {department_id}")
            return None

    def add_department(self,
                       department_name: str,
                       company_name: str,
                       first_user: dict,
                       ):
        
        try:
            data = {
                "department_name": department_name,
                "company_name": company_name,
                "employees": [first_user],
                "main_vector_db_id": ""
            }

            response_code = self.collection.insert_one(data)
            print(response_code)
            department_id = response_code.inserted_id
            department_id_string = str(department_id)

            # set main_vector_db_id:
            vector_db_id = department_id_string + "_main_vector_db"
            self.collection.update_one(
                {"_id": department_id},
                {"$set": {"main_vector_db_id": vector_db_id}}
            )

            print(f"New department with id {department_id_string} was saved in collection {self.collection}")
            return True

        except Exception as e:
            print(f"New department {department_name} couldn't be saved to collection {self.collection}. Error: ", e)
            return None

    def delete_department(self, department_id: ObjectId):
        try:
            response_code = self.collection.delete_one({ "_id": department_id })
            print(response_code)
            print(f"Deleted department with id {department_id}")
            return True
        
        except Exception as e:
            print(f"Couldn't delete department with id {department_id}", e)
            return False

    def add_employee(self, department_id: ObjectId, employee_data: dict):
        try:
            response_code = self.collection.update_one(
                {"_id": department_id},
                {"$push": {"employees": employee_data}}
            )
            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                print("Added employee data to department document: ", employee_data)
                return True
            else:
                print("Couldn't add new employee, department id might be wrong: ", department_id)
                return False
        
        except Exception as e:
            print(f"Employee data couldn't be saved to document of department {department_id}", e)
            return False

    def delete_employee(self, department_id: ObjectId, employee_id: ObjectId):
            try:
                response_code = self.collection.update_one(
                    {"_id": department_id},
                    {"$pull": {"employees": {'id': employee_id}}}
                )
                updated_data = response_code.raw_result["updatedExisting"]
                if updated_data:
                    print("Successfully deleted employee with id: ", employee_id)
                    return True
                else:
                    print("Couldn't delete employee, department id might be wrong: ", department_id)
                    return False
            
            except Exception as e:
                print(f"Employee data couldn't be saved to document of department {department_id}", e)
                return False