from django.urls import path
from .views import *

urlpatterns = [
    path('api/token/', AuthTokenView.as_view(), name='auth-token'),
    path('create_user/', UserCreateView.as_view(), name='create_user'),
    path('create_post/', CreatePostView.as_view(), name='create_post'),
    path('timeline/', TimelineView.as_view(), name='timeline'),
    path('add_comment/', AddCommentView.as_view(), name='add_comment'),
    path('follow_user/', FollowUserView.as_view(), name='follow_user'),
    path('unfollow_user/', UnfollowUserView.as_view(), name='unfollow_user'),
    path('like_post/', LikePostView.as_view(), name='like_post'),
    path('unlike_post/', UnlikePostView.as_view(), name='unlike_post'),
    path('logout/', LogoutView.as_view(), name='logout'),

]
