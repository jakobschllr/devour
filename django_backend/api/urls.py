from django.urls import path
from . import views # import the views

# paths within the api app

urlpatterns = [
    path("get_user_data", views.get_user_data, name="get_user_data")
]