from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['user_id', 'username', 'password', 'first_name', 'last_name', 'user_type', 'department']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)