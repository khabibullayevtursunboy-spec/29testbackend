from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role", "school_class"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    teacher_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "password", "full_name", "role", "school_class", "teacher_code"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        role = attrs.get("role", User.STUDENT)
        code = attrs.get("teacher_code", "")
        if role == User.TEACHER and settings.TEACHER_CODE and code != settings.TEACHER_CODE:
            raise serializers.ValidationError({"teacher_code": "O'qituvchi kodi noto'g'ri."})
        if role == User.STUDENT and not attrs.get("full_name"):
            raise serializers.ValidationError({"full_name": "Ism-familiyani kiriting."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("teacher_code", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
