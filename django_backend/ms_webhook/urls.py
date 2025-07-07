from django.urls import path
from .views import transcript_notification
from .views import lifecycle_notification
from .views import home

urlpatterns = [
    path('transcript_notification/', transcript_notification, name='transcript-notification'),
    path('lifecycle_notification/', lifecycle_notification, name='lifecycle-notification'),
    path('home/', home, name='webhook-home')
]
