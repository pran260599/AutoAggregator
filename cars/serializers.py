# AutoAggregator/cars/serializers.py

from rest_framework import serializers
from .models import Car, Review, CarView, CarSave, SearchQuery
from django.contrib.auth import get_user_model # <--- Import get_user_model

User = get_user_model() # <--- Define User model

class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

# New: Serializer for Django's built-in User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email'] # Only expose necessary fields

class CarViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarView
        fields = '__all__'
        read_only_fields = ('user', 'view_date',)

class CarSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarSave
        fields = '__all__'
        read_only_fields = ('user', 'save_date',)

class SearchQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQuery
        fields = '__all__'
        read_only_fields = ('user', 'timestamp',)

# New: User serializer for registration (handles password hashing)
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True) # Password is write-only

    class Meta:
        model = User
        fields = ['username', 'email', 'password'] # Fields for registration

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user