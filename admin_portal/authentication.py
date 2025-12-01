from django.contrib.auth.backends import BaseBackend
from .models import AdminUser
from django.contrib.auth.hashers import check_password

class AdminUserBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = AdminUser.objects.get(email=email)
            if check_password(password, user.password):
                return user
        except AdminUser.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None


