from django.http import Http404
from .serializers import (
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
    PostBackUpSerializer,
)
from .models import Post, Comment, Like, PostBackUp
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import QueryDict
from datetime import datetime


def get_object(pk: int, table):
    """Get object from table by PrimaryKey."""
    try:
        return table.objects.get(pk=pk)
    except:
        raise Http404


class PostList(APIView):
    """Processing home URL."""

    def get(self, request):
        """Get all posts info from Post model and return all post contained JSON."""
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Receive data from request and save to DB."""
        data = dict(request.data)
        data = {key: value[0] for key, value in data.items()}
        data["author"] = str(request.user.id)
        # Protection from custom user likes number input
        data["likes_count"] = 0

        data_query_dict = QueryDict("", mutable=True)
        data_query_dict.update(data)
        serializer = PostSerializer(data=data_query_dict)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get full post info."""
        post = get_object(pk, Post)
        data = PostSerializer(post).data
        data["likes_count"] = len(Like.objects.filter(post=pk))
        comments = Comment.objects.filter(post=pk)
        data["comments"] = [CommentSerializer(comment).data for comment in comments]
        return Response(data)

    def put(self, request, pk):
        """Edit post and backup previous version."""
        post = get_object(pk, Post)
        data = dict(request.data)
        # After conversion QueryDict to dict values were packed in lists so values were unpacked
        data = {key: value[0] for key, value in data.items()}

        data["author"] = str(post.author.id)
        data["likes_count"] = post.likes_count
        data_query_dict = QueryDict("", mutable=True)
        data_query_dict.update(data)
        serializer = PostSerializer(post, data=data_query_dict)
        # Make backup of previous post version and save it to backup table (just in case).
        backup_data = {"post": post.id, "content": post.content, "date": post.date}
        backup_data_query_dict = QueryDict("", mutable=True)
        backup_data_query_dict.update(backup_data)
        backup_serializer = PostBackUpSerializer(data=backup_data_query_dict)
        if backup_serializer.is_valid():
            backup_serializer.save()
        if serializer.is_valid():
            if post.author.id == request.user.id:
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Post delete."""
        post = get_object(pk, Post)
        if post.author.id == request.user.id:
            post.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class PostLike(APIView):
    def get(self, request, pk):
        """Like or unlike post."""
        post_id = get_object(pk, Post).id
        user_id = request.user.id
        data_dict = {"author": user_id, "post": post_id}

        # Convert dict to QueryDict
        data_query_dict = QueryDict("", mutable=True)
        data_query_dict.update(data_dict)

        serializer = LikeSerializer(data=data_query_dict)
        qs = Like.objects.filter(author=user_id)
        user_liked_post = [like.post.id for like in qs]
        post = Post.objects.get(pk=post_id)
        # Check if user already liked post
        if post_id not in user_liked_post:
            if serializer.is_valid():
                post.likes_count += 1
                post.save()
                serializer.save()
            return Response(
                f"You liked post {post_id}.", status=status.HTTP_201_CREATED
            )
        else:
            # Like remove if user already liked post
            like = Like.objects.get(author=user_id, post=post_id)
            post.likes_count -= 1
            post.save()
            like.delete()
            return Response(
                f"You unliked post {post_id}.", status=status.HTTP_204_NO_CONTENT
            )


class PostComment(APIView):
    def get(self, request, pk):
        """Get all post comments."""
        comments = Comment.objects.filter(post_id=pk)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        """Add comment to post."""
        data = dict(request.data)
        post_id = get_object(pk, Post).id
        data = {key: value[0] for key, value in data.items()}
        data["author"] = str(request.user.id)
        data["post"] = post_id
        data_query_dict = QueryDict("", mutable=True)
        data_query_dict.update(data)
        serializer = CommentSerializer(data=data_query_dict)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete comment from post."""
        comment = get_object(pk, Comment)
        if comment.author.id == request.user.id:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self, request, pk):
        """Edit comment."""
        comment = self.get_object(pk, Comment)
        data = dict(request.data)
        data = {key: value[0] for key, value in data.items()}
        data["date"] = comment.date
        data["author"] = comment.author.id
        data["post"] = comment.post.id
        data_query_dict = QueryDict("", mutable=True)
        data_query_dict.update(data)
        serializer = CommentSerializer(comment, data=data_query_dict)
        if serializer.is_valid():
            if comment.author.id == request.user.id:
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Analytics(APIView):
    """Get all likes on given date interval."""

    def get(self, request, date_from, date_to):
        date_from = datetime.strptime(date_from, "%Y-%m-%d")
        date_to = datetime.strptime(date_to, "%Y-%m-%d")
        likes = Like.objects.filter(date__range=[date_from, date_to])
        serializer = LikeSerializer(likes, many=True)
        likes_count = len(list(serializer.data))
        return Response(f"{likes_count} likes in total.")


class PostBackup(APIView):
    def get_backups_by_post(self, pk):
        """Get all backups by post PrimaryKey."""
        results = PostBackUp.objects.filter(post=pk)
        if not results:
            raise Http404
        return results

    def get(self, response, pk):
        backups = self.get_backups_by_post(pk)
        backup_serializer = PostBackUpSerializer(backups, many=True)
        return Response(backup_serializer.data)
