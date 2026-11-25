from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    TEACHER = "teacher"
    STUDENT = "student"
    ROLE_CHOICES = [(TEACHER, "O'qituvchi"), (STUDENT, "O'quvchi")]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    full_name = models.CharField(max_length=150, blank=True)
    school_class = models.CharField("Sinf", max_length=20, blank=True)

    @property
    def is_teacher(self):
        return self.role == self.TEACHER

    @property
    def is_student(self):
        return self.role == self.STUDENT

    def __str__(self):
        return f"{self.full_name or self.username} ({self.role})"
