from rest_framework import serializers
from .models import *
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'email']  

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user
    

class CommentSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    content = serializers.CharField()
    created_at = serializers.CharField()
    user = serializers.CharField()
    post = serializers.CharField()

    class Meta:
        model = Comment
        fields = '__all__'


class CommentTimeLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    comments = CommentTimeLineSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = '__all__'


class TimelineSerializer(serializers.Serializer):
    posts = PostSerializer(many=True, read_only=True)
