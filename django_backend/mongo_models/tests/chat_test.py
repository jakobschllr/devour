from bson import ObjectId
from dotenv import load_dotenv
from models.chat import ChatModel

model = ChatModel()
test_user_id = ObjectId("67c702c16dd1085d16bb6599")

# test create new chat
def new_chat():
    model.new_chat(
        user_id=test_user_id,
        name="Max Mustermann",
        title="How to change articel number",
    )

# test chat deletion
def delete_chat():
    model.delete_chat(
        chat_id=ObjectId("67c8c77c95bc830ed345b8e6")
    )

# test change of chat title
def change_title():
    model.change_chat_title(
        chat_id=ObjectId("67c8c0f4987d4486df57ae26"),
        new_title="Email to boss"
    )

# test add additional user
def add_additional_user():
    model.add_additional_user(
        chat_id=ObjectId("67c8c7c11d09ae780d779f54"),
        user_data={
            "id": ObjectId("22c8c3802c04253b9c3e8011"),
            "name": "Karl Marx"
        }
    )

# test remove additional user
def remove_additional_user():
    model.remove_additional_user(
        chat_id=ObjectId("67c8c7c11d09ae780d779f54"),
        user_id=ObjectId("22c8c3802c04253b9c3e8011")
    )

# run with: python3 -m tests.chat_test from directory mongo_models