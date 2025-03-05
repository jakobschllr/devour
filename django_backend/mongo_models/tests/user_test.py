from models.user import UserModel
from bson import ObjectId
from dotenv import load_dotenv
import os

# create UserModel
user_model = UserModel()
test_department_id = ObjectId("123452340235454203492309")
test_user_id = ObjectId("67c702c16dd1085d16bb6599")
user_test_password = "test12345"
test_chat_id = ObjectId("43580a345b03a2c340283225")

# add user
def add_user():
    user_model.add_user(
        name="Max Mustermann",
        password=user_test_password,
        email="max.mustermann@gmail.com",
        role="Sales Associate",
        department_id=test_department_id,
        department_name="Sales",
        company_name="Muster GmbH",
        is_admin=True
)

# delete user
def delete_user():
    user_model.delete_user(
        user_id=ObjectId("67c77f2ca064cbd6985e4329")
    )

# make user an admin
def make_admin():
    user_model.make_admin(
        user_id=test_user_id
    )

# change user from admin to no admin
def make_no_admin():
    user_model.make_no_admin(
        user_id=test_user_id
    )

# test adding a chat
def add_chat():
    user_model.add_chat(
        user_id=test_user_id,
        chat_id=test_chat_id
    )

# test delete chat
def delete_chat():
    user_model.delete_chat(
        user_id=test_user_id,
        chat_id=ObjectId("43580a345b03a2c34028342b")
    )

# test setting the ms teams refresh token
def set_ms_teams_refresh_token():
    load_dotenv()
    refresh_token = os.getenv('MS_REFRESH_TOKEN')
    user_model.set_ms_teams_refresh_token(
        user_id=test_user_id,
        refresh_token=refresh_token
    )

# test getting the ms teams refresh token
def get_ms_teams_refresh_token():
    refresh_token = user_model.get_msteams_refresh_token(
        user_id=test_user_id
    )
    print("Refresh Token", refresh_token)

# check if inputted user password is correct
def check_password():
    password_is_correct = user_model.check_pswrd(
        user_id=test_user_id,
        password=user_test_password
    )
    print(password_is_correct)

# test configurations
def change_config():
    user_model.change_configuration(
        user_id=ObjectId("67c702c16dd1085d16bb6599"),
        config='tone',
        change_value='professional and friendly'
    )

# test get user_data
def get_user_data():
    data = user_model.get_user_data(
        user_id=ObjectId("67c702c16dd1085d16bb6599")
    )
    print(data)

# run with: python3 -m tests.user_test from directory mongo_models
