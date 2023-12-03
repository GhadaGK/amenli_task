from .models import *
from .serializers import *
from .signals import user_followed, user_unfollowed, post_liked, post_unliked
from django.db import transaction
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.http import JsonResponse
from .utils import generate_tokens
from .tasks import send_comment_notification_email
from rest_framework import generics, permissions, status
from rest_framework.response import Response

class AuthTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            access_token, refresh_token = generate_tokens(user)
            if Token.objects.filter(user = user).count() == 0 :
                token = Token.objects.create(user = user , token = access_token , is_active = True)
                token.save()
                return JsonResponse({
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                })
            elif Token.objects.get(user = user).is_active == False:
                Token.objects.filter(user=user).update(is_active=True)
                return JsonResponse({
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                })
            elif Token.objects.get(user = user).is_active == True:
                return JsonResponse({ 'details': "You should logout first to login from another device!"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return JsonResponse({'details': 'Invalid credentials, You should register user first'}, status=status.HTTP_401_UNAUTHORIZED)


class UserCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]  


class CreatePostView(generics.CreateAPIView):
    class InputSerializer(serializers.Serializer):
        user_id = serializers.IntegerField()
        content = serializers.CharField()

    @transaction.atomic
    def post(self, request):
        inputSerializer = self.InputSerializer(data=request.data)
        inputSerializer.is_valid(raise_exception=True)
        request_body = inputSerializer.validated_data
        user_id = request_body.get('user_id')
        content = request_body.get('content')
        try :
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
            elif Token.objects.get(user__id = user_id).token != authorization_header or Token.objects.filter(user__id=user_id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
            else :
                    user = CustomUser.objects.get(id = user_id)
                    post = Post.objects.create(user = user, content = content)
                    post.save()
                    return Response( {"details" :" Post is created successfully" }, status= status.HTTP_201_CREATED )
        except:
            return Response( {"details" :"Invalid data"}, status= status.HTTP_400_BAD_REQUEST)


class TimelineView(generics.ListAPIView):
    serializer_class = TimelineSerializer

    @transaction.atomic
    def get_queryset(self):
        authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
        if authorization_header == None or authorization_header == "":
            return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
        user = Token.objects.get(token = authorization_header).user
        if Token.objects.get(user__id = user.id).token != authorization_header or Token.objects.filter(user__id=user.id, is_active=False).exists():
            return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
        following_ids = user.following.values_list('following_id', flat=True)
        return Post.objects.filter(user__id__in=following_ids).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        try :
            queryset = self.get_queryset()
            serializer = self.get_serializer({'posts': queryset})
            return Response(serializer.data)
        except :
            return Response( {"details" :"Invalid credentials"}, status= status.HTTP_400_BAD_REQUEST)


class AddCommentView(generics.CreateAPIView):
    class InputSerializer(serializers.Serializer):
        user_id = serializers.IntegerField()
        post_id = serializers.IntegerField()
        content = serializers.CharField()

    @transaction.atomic
    def post(self, request):
        inputSerializer = self.InputSerializer(data=request.data)
        inputSerializer.is_valid(raise_exception=True)
        request_body = inputSerializer.validated_data
        user_id = request_body.get('user_id')
        post_id = request_body.get('post_id')
        content = request_body.get('content')
        try:
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            user = CustomUser.objects.get(id = user_id)
            post = Post.objects.get(id = post_id)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
            elif Token.objects.get(user__id = user_id).token != authorization_header or Token.objects.filter(user__id=user_id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
            comment = Comment.objects.create(user = user, post = post, content = content)
            comment.save()
            post_author_email = comment.post.user.email
            send_comment_notification_email.delay(post_author_email, comment.content)        
            return Response( {"details" :" Comment is created successfully and Email is sent successfully" }, status= status.HTTP_201_CREATED )
        except:
            return Response( {"details" :"Invalid data"}, status= status.HTTP_400_BAD_REQUEST)


class FollowUserView(generics.CreateAPIView):
    class InputSerializer(serializers.Serializer):
        following_id = serializers.IntegerField()

    @transaction.atomic
    def post(self, request):
        inputSerializer = self.InputSerializer(data=request.data)
        inputSerializer.is_valid(raise_exception=True)
        request_body = inputSerializer.validated_data
        following_id = request_body.get('following_id')
        try :
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)    
            follower = Token.objects.get(token = authorization_header).user
            following = CustomUser.objects.get(id = following_id)
            if follower.id == following.id : 
                return Response({"detail": "Can't follow yourself"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            if Token.objects.get(user__id = follower.id).token != authorization_header or Token.objects.filter(user__id=follower.id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
            follow = Follow.objects.create(follower = follower ,following = following)
            follow.save()
            try :
                user_followed.send(sender=follower, target_user=following)
            except :
                return Response({"detail": "A duplicate follow is attempted."}, status=status.HTTP_406_NOT_ACCEPTABLE)
            return Response( {"details" :" Following process is performed successfully" }, status= status.HTTP_201_CREATED )
        except :
            return Response( {"details" :"Invalid data"}, status= status.HTTP_400_BAD_REQUEST)


class UnfollowUserView(generics.GenericAPIView):
    class InputSerializer(serializers.Serializer):
        following_id = serializers.IntegerField()
        
    @transaction.atomic
    def delete(self, request):
        inputSerializer = self.InputSerializer(data=request.data)
        inputSerializer.is_valid(raise_exception=True)
        request_body = inputSerializer.validated_data
        following_id = request_body.get('following_id')
        try :
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
            follower = Token.objects.get(token = authorization_header).user
            following = CustomUser.objects.get(id = following_id)
            if follower.id == following.id : 
                return Response({"detail": "Can't unfollow yourself"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            if Token.objects.get(user__id = follower.id).token != authorization_header or Token.objects.filter(user__id=follower.id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
            Follow.objects.filter(follower = follower ,following = following).delete()
            try : 
                user_unfollowed.send(sender=follower, target_user=following)
            except :
                return Response({"detail": "A duplicate unfollow is attempted."}, status=status.HTTP_406_NOT_ACCEPTABLE)
            return Response({"details" :" Unfollowing process is performed successfully" }, status= status.HTTP_200_OK )
        except :
            return Response( {"details" :"Invalid data"}, status= status.HTTP_400_BAD_REQUEST)


class LikePostView(generics.CreateAPIView):
    class InputSerializer(serializers.Serializer):
        post_id = serializers.IntegerField()

    @transaction.atomic
    def post(self, request):
        inputSerializer = self.InputSerializer(data=request.data)
        inputSerializer.is_valid(raise_exception=True)
        request_body = inputSerializer.validated_data
        post_id = request_body.get('post_id')
        try :
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
            user = Token.objects.get(token = authorization_header).user
            post = Post.objects.get(id = post_id)
            if Token.objects.get(user__id = user.id).token != authorization_header or Token.objects.filter(user__id=user.id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN) 
            like = Like.objects.create(user = user ,post = post)
            like.save()
            try :
                post_liked.send(sender=user, target_post=post)
            except :
                return Response({"detail": "A duplicate like is attempted."}, status=status.HTTP_406_NOT_ACCEPTABLE)
            return Response( {"details" :" Like process is performed successfully" }, status= status.HTTP_201_CREATED )
        except :
            return Response( {"details" :"Invalid data"}, status= status.HTTP_400_BAD_REQUEST)


class UnlikePostView(generics.GenericAPIView):
    class InputSerializer(serializers.Serializer):
        post_id = serializers.IntegerField()
        
    @transaction.atomic
    def delete(self, request):
        inputSerializer = self.InputSerializer(data=request.data)
        inputSerializer.is_valid(raise_exception=True)
        request_body = inputSerializer.validated_data
        post_id = request_body.get('post_id')
        try :
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
            user = Token.objects.get(token = authorization_header).user
            post = Post.objects.get(id = post_id)
            if Token.objects.get(user__id = user.id).token != authorization_header or Token.objects.filter(user__id=user.id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
            Like.objects.filter(user = user ,post = post).delete()
            try : 
                post_unliked.send(sender=user, target_user=post)
            except :
                return Response({"detail": "A duplicate unlike is attempted."}, status=status.HTTP_406_NOT_ACCEPTABLE)
            return Response({"details" :" Unlike process is performed successfully" }, status= status.HTTP_200_OK )
        except :
            return Response( {"details" :"Invalid data"}, status= status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    @transaction.atomic
    def post(self, request):
        try :
            authorization_header = self.request.META.get('HTTP_AUTHORIZATION', None)
            if authorization_header == None or authorization_header == "":
                return Response({"detail": "User is not allowed to perform this action because the token is None."}, status=status.HTTP_403_FORBIDDEN)
            user = Token.objects.get(token = authorization_header).user
            if Token.objects.get(user__id = user.id).token != authorization_header or Token.objects.filter(user__id=user.id, is_active=False).exists():
                return Response({"detail": "User is not allowed to perform this action because the token is inactive."}, status=status.HTTP_403_FORBIDDEN)
            Token.objects.filter(user=user).update(is_active=False)
        except Exception as e:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)