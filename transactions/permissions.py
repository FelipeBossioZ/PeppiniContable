from rest_framework import permissions
from .models import License
from datetime import date

class HasValidLicense(permissions.BasePermission):
    """
    Custom permission to only allow users with a valid license to access the API.
    """
    def has_permission(self, request, view):
        try:
            license = request.user.license
            if license.is_active and license.expiration_date >= date.today():
                return True
        except License.DoesNotExist:
            return False
        return False
