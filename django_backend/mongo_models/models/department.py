from pymongo import MongoClient
from bson import ObjectId

class DepartmentModel:
    def __init__(self, mongo_host_port: str):
        self.collection = "departments"
        self.client = MongoClient(mongo_host_port)
        self.db = self.client["devour_database"]
        self.collection = self.db[self.collection]

    def get_employees(self, department_id: ObjectId):
        department = self.collection.find_one({"_id": department_id})
        if len(department['employees']) > 0:
            return {"status": "success", "data": department['employees']}
        else:
            return {"status": "failure", "data": []}

    def get_vector_db_data(self, department_id: ObjectId):
        try:
            print("Passed Department ID: ", department_id)
            print(type(department_id))
            department_data = self.collection.find_one({"_id": department_id})
            print(department_data)
            if department_data != None:
                print(f"Fetched department data of department with id {department_data['_id']}")
                return {
                    "status": "success",
                    "data": {
                        "vector_db_collection": department_data['vector_db_collection'],
                        "vector_db_dir_path": department_data['vector_db_dir_path']
                        }
                    }
            else:
                msg = f"Couldn't find data of department with id: {department_data}"
                return {"status": "failure", "data": msg}
            
        except Exception as e:
            print(f"Error while trying to find department {department_data}. Error: ", e)
            return {"status": "failure", "data": e}

    def add_department(self,
                       department_name: str,
                       company_name: str,
                       all_departments_path: str
                       ):
        
        try:
            data = {
                "department_name": department_name,
                "company_name": company_name,
                "employees": [],
                "vector_db_collection": "",
                "vector_db_dir_path": ""
            }

            response_code = self.collection.insert_one(data)
            department_id = response_code.inserted_id
            department_id_string = str(department_id)

            # set main_vector_db_id:
            self.collection.update_one(
                {"_id": department_id},
                {"$set": {"vector_db_collection": department_id_string}}
            )

            # save vector db path
            vector_db_dir_path = f"{all_departments_path}/{department_id_string}"
            self.collection.update_one(
                {"_id": department_id},
                {"$set": {"vector_db_dir_path": vector_db_dir_path}}
            )

            msg = f"New department with id {department_id_string} was saved in collection {self.collection}"
            print(msg)
            return {"status": "success", "data": {"msg": msg, "department_id": department_id_string}}

        except Exception as e:
            msg = f"New department {department_name} couldn't be saved to collection {self.collection}. Error: ", e
            return {"status": "failure", "data": e}

    def delete_department(self, department_id: ObjectId):
        try:
            response_code = self.collection.delete_one({ "_id": department_id })
            print(response_code)
            msg = f"Deleted department with id {department_id}"
            return {"status": "success", "data": msg}
        
        except Exception as e:
            print(f"Couldn't delete department with id {department_id}", e)
            return {"status": "failure", "data": e}

    def add_employee(self, department_id: ObjectId, employee_id: ObjectId):
        try:
            response_code = self.collection.update_one(
                {"_id": department_id},
                {"$push": {"employees": employee_id}}
            )

            updated_data = response_code.raw_result["updatedExisting"]
            if updated_data:
                msg = f"Added data of user {employee_id} to document of department {department_id}"
                return {"status": "success", "data": msg}
            else:
                msg = f"Couldn't add data of user {employee_id} to document of department {department_id}"
                print(msg)
                return {"status": "failure", "data": msg}
        
        except Exception as e:
            msg = f"Error while adding data of user {employee_id} to document of department {department_id}"
            return {"status": "failure", "data": msg}

    def delete_employee(self, department_id: ObjectId, employee_id: ObjectId):
            try:
                response_code = self.collection.update_one(
                    {"_id": department_id},
                    {"$pull": {"employees": employee_id}}
                )
                updated_data = response_code.raw_result["updatedExisting"]
                if updated_data:
                    msg = f"Successfully deleted employee with id: {employee_id}"
                    print(msg)
                    return {"status": "success", "data": msg}
                else:
                    msg = f"Couldn't delete employee, department id might be wrong:{department_id}"
                    print(msg)
                    return {"status": "failure", "data": msg}
            
            except Exception as e:
                print(f"Employee data couldn't be saved to document of department {department_id}", e)
                return {"status": "failure", "data": e}