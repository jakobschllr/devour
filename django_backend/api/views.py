from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from bson import ObjectId
import json

from mongo_models.models.department import DepartmentModel
from mongo_models.models.user import UserModel
from mongo_models.models.chat import ChatModel

department_model = DepartmentModel()
user_model = UserModel()
chat_model = ChatModel()

# API Endpoints:

def get_user_data(request):
    if request.method == "GET":
        data = json.loads(request.body)
        user_id = data.get("user_id")
        user_id_obj = ObjectId(user_id)

        user_data = user_model.get_user_data(user_id_obj)

        if user_data != None:
            return JsonResponse(user_data)
        else:
            return HttpResponse(status=500)
