from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserProfile = get_user_model()
        try:
            user = UserProfile.objects.get(email=username)
        except UserProfile.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None