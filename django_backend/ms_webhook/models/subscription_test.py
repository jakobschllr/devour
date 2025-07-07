

# from django.conf import settings
from subscription import MicrosoftSubscription
from django_backend.ms_webhook.models.manage_token import get_new_access_token, get_user_info

# settings.configure()

subscribtion_model = MicrosoftSubscription()

new_access_token = get_new_access_token()

user_info = get_user_info(new_access_token)

print(user_info)

user_id = user_info['id']


print(subscribtion_model.create_subscription(user_id, new_access_token))

# print(subscribtion_model.delete_subscription("87d298b0-7c4d-4116-95c2-c33854e48984",new_access_token))


