from django.urls import path
from .views import transcript_notification
from .views import lifecycle_notification

urlpatterns = [
    path('transcript_notification/', transcript_notification, name='transcript-notification'),
    path('lifecycle_notification/', lifecycle_notification, name='lifecycle-notification')
]
