from rest_framework.permissions import BasePermission


class IsCounselor(BasePermission):
    message = "Bu işlem yalnızca rehberler içindir."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_counselor)


class IsStudent(BasePermission):
    message = "Bu işlem yalnızca öğrenciler içindir."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsParent(BasePermission):
    message = "Bu işlem yalnızca veliler içindir."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_parent)
