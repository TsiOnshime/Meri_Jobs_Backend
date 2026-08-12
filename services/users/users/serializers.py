from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'full_name', 'language', 'phone', 'location', 'bio', 'role', 'created_at', 'last_login']
        read_only_fields = ['id', 'created_at', 'last_login']


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8)
    name = serializers.CharField(required=True, max_length=255)
    full_name = serializers.CharField(required=False, max_length=255, allow_blank=True)
    language = serializers.ChoiceField(choices=[('en', 'English'), ('am', 'Amharic')], required=False, default='en')
    phone = serializers.CharField(required=False, max_length=20, allow_blank=True)
    location = serializers.CharField(required=False, max_length=255, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    
    def validate_password(self, value):
        # Add password strength validation
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)
