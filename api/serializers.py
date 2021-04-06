from .models import Post, Comment, Like, PostBackUp
from rest_framework import serializers


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "author", "title", "content", "date", "likes_count"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author", "post", "content", "date"]


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["author", "post", "date"]


class PostBackUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostBackUp
        fields = ["id", "post", "content", "date"]
