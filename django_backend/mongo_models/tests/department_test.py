from models.department import DepartmentModel
from bson import ObjectId
from dotenv import load_dotenv

model = DepartmentModel()
test_user_id = ObjectId("67c702c16dd1085d16bb6599")
test_user2_id = ObjectId("67c733c16dd1085d16cc2311")
test_department_id = ObjectId("67c77249ca5d851048c25fcc")

# test add department
def add_department():
    model.add_department(
        department_name="Sales",
        company_name="Muster GmbH",
        first_user={
            "name": "Max Mustermann",
            "id": test_user_id
        }
    )

# test delete department
def delete_department():
    model.delete_department(
        department_id=ObjectId("67c77b868a4958085edecdf1")
    )

# test get main vector db id
def get_main_vector_db_id():
    main_vector_db_id = model.get_main_vector_db_id(
        department_id=test_department_id
    )
    print(main_vector_db_id)

# test add employee
def add_employee():
    model.add_employee(
        department_id=test_department_id,
        employee_data={
            "name": "Karla Musterfrau",
            "id": test_user2_id
        }
    )

# test delete employee
def delete_employee():
    model.delete_employee(
        department_id=test_department_id,
        employee_id=test_user2_id
    )

# run with: python3 -m tests.department_test from directory mongo_models