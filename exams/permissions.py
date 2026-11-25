from rest_framework.permissions import BasePermission


class IsTeacher(BasePermission):
    message = "Bu amal faqat o'qituvchilar uchun."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_teacher)


class IsStudent(BasePermission):
    message = "Bu amal faqat o'quvchilar uchun."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)
