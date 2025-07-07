from django.urls import path
from api import views

# paths within the api app

urlpatterns = [
    # user endpoints
    path("get_user_data", views.get_user_data, name="get_user_data"),
    path("login_user", views.login_user, name="login_user"),
    path("signup_user", views.signup_user, name="signup_user"),
    path("delete_user", views.delete_user, name="delete_user"),
    path("make_user_admin", views.make_user_admin, name="make_user_admin"),
    path("make_user_non_admin", views.make_user_non_admin, name="make_user_non_admin"),
    path("change_configuration", views.change_configuration, name="change_configuration"),
    path("update_user_context", views.update_user_context, name="update_user_context"),
    path("store_ms_teams_tokens", views.store_ms_teams_tokens, name="store_ms_teams_tokens"),

    # department endpoints
    path("create_department", views.create_department, name="create_department"),
    path("delete_department", views.delete_department, name="delete_department"),

    # chat endpoints
    path("create_chat", views.create_chat, name="create_chat"),
    path("load_chat", views.load_chat, name="load_chat" ),
    path("user_prompt", views.user_prompt, name="user_prompt"),
    path("change_chat_title", views.change_chat_title, name="change_chat_title"),
    path("add_additional_user", views.add_additional_user, name="add_additional_user"),
    path("remove_additional_user", views.remove_additional_user, name="remove_additional_user"),
    path("delete_chat", views.delete_chat, name="delete_chat"),
    path("update_chat_context", views.update_chat_context, name="update_chat_context")
]