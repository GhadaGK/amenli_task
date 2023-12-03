from rest_framework import status
from django.urls import reverse
from rest_framework.test import APIClient
from django.test import TestCase
from .models import *

class TestViews(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_token_view_with_a_new_user_that_has_no_token(self):
        self.user = CustomUser.objects.create_user(
            username= 'testuser',
            password= 'testpassword',
            email='testuser@gmail.com'
        )
        url = reverse('auth-token')
        data = {'username': "testuser", 'password': "testpassword"}
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.json()

    def test_auth_token_view_with_a_new_user_that_has_active_token(self):
        self.user = CustomUser.objects.create_user(
            username= 'testuser',
            password= 'testpassword',
            email='testuser@gmail.com'
        )
        url = reverse('auth-token')
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.json()
        data = {'username': "testuser", 'password': "testpassword"}
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "You should logout first to login from another device!" in response.json().get('details')

    def test_auth_token_view_with_no_user_and_no_active_token(self):
        url = reverse('auth-token')
        data = {'username': 'new', 'password': 'new'}
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Invalid credentials, You should register user first' in response.json().get('details')

    def test_create_user_view(self):
        url = reverse('create_user')
        data = {'username': 'createuser', 'password': 'createpassword' , 'email': 'createuser@gmail.com' } 
        response = self.client.post(url, data,  format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_user_view_with_pre_existing_email(self):
        url = reverse('create_user')
        data = {'username': 'ghada', 'password': 'admin' , 'email': 'ghadagamalkarim@gmail.com' } 
        response = self.client.post(url, data,  format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_post_view(self):
        token = Token.objects.filter(is_active = True).last()
        content = 'Test post content'
        url = reverse('create_post')
        data = {'user_id': token.user.id, 'content': content}
        headers = {'Authorization': f'{token.token}'}
        response = self.client.post(url, data, headers=headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.filter(content= content).exists()

    def test_create_post_view_with_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        content = 'Test post content'
        url = reverse('create_post')
        data = {'user_id': token.user.id, 'content': content}
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_post_view_with_inactivated_token(self):
        Token.objects.filter(is_active = True).update(is_active = False)
        token = Token.objects.filter(is_active = False).last()
        content = 'Test post content'
        url = reverse('create_post')
        data = {'user_id': token.user.id, 'content': content}
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_timeline_view(self):
        token = Token.objects.filter(is_active = True).last()
        url = reverse('timeline')
        headers = {'Authorization': f'{token.token}'}
        response = self.client.get(path = url, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert 'posts' in response.data

    def test_timeline_view_with_no_header_authentication(self):
        url = reverse('timeline')
        response = self.client.get(path = url)
        assert response.status_code == 400
        assert 'posts' not in response.data

    def test_add_comment_view(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        post = Post.objects.create(user=token.user, content='Test post content')
        url = reverse('add_comment')
        data = {'user_id': token.user.id, 'post_id': post.id, 'content': 'Test comment content'}
        response = self.client.post(path = url, data = data, headers = headers)
        assert response.status_code == status.HTTP_201_CREATED
        assert Comment.objects.filter(content='Test comment content').exists()

    def test_add_comment_view_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        post = Post.objects.create(user=token.user, content='Test post content')
        url = reverse('add_comment')
        data = {'user_id': token.user.id, 'post_id': post.id, 'content': 'Test comment content'}
        response = self.client.post(path = url, data = data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_comment_view_inactive_token(self):
        Token.objects.filter(is_active = True).update(is_active = False)
        token = Token.objects.filter(is_active = False).last()
        headers = {'Authorization': f'{token.token}'}
        post = Post.objects.create(user=token.user, content='Test post content')
        url = reverse('add_comment')
        data = {'user_id': token.user.id, 'post_id': post.id, 'content': 'Test comment content'}
        response = self.client.post(path = url, data = data, headers = headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_like_post_view(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('like_post')
        post = Post.objects.last()
        response = self.client.post(url, {'post_id': post.id}, headers =headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_like_post_view_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        url = reverse('like_post')
        post = Post.objects.last()
        response = self.client.post(url, {'post_id': post.id}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_like_post_view_with_inactive_token(self):
        Token.objects.filter(is_active = True).update(is_active = False)
        token = Token.objects.filter(is_active = False).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('like_post')
        post = Post.objects.last()
        response = self.client.post(url, {'post_id': post.id}, headers =headers, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unlike_post_view(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('like_post')
        post = Post.objects.last()
        response = self.client.post(url, {'post_id': post.id}, headers =headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        url = reverse('unlike_post')
        response = self.client.delete(url, {'post_id': post.id}, headers = headers, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_unlike_post_view_with_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('like_post')
        post = Post.objects.last()
        response = self.client.post(url, {'post_id': post.id}, headers =headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        url = reverse('unlike_post')
        response = self.client.delete(url, {'post_id': post.id}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_follow_user_view(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('follow_user')
        following = Token.objects.filter(is_active = True).exclude(token = token.token).last().user
        response = self.client.post(url, {'following_id': following.id}, headers= headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_follow_user_when_follower_user_equal_following_user(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('follow_user')
        following = Token.objects.get(user= token.user, is_active = True).user
        response = self.client.post(url, {'following_id': following.id}, headers= headers, format='json')
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    def test_follow_user_view_with_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        url = reverse('follow_user')
        following = Token.objects.filter(is_active = True).exclude(token = token.token).last().user
        response = self.client.post(url, {'following_id': following.id},  format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_follow_user_view_with_inactive_token(self):
        Token.objects.filter(is_active = True).update(is_active = False)
        token = Token.objects.filter(is_active = False).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('follow_user')
        following = Token.objects.filter(is_active = False).exclude(token = token.token).last().user
        response = self.client.post(url, {'following_id': following.id}, headers= headers, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unfollow_user_view(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('follow_user')
        following = Token.objects.filter(is_active = True).exclude(token = token.token).last().user
        response = self.client.post(url, {'following_id': following.id}, headers= headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        url = reverse('unfollow_user')
        response = self.client.delete(url, {'following_id': following.id}, headers=headers, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_unfollow_user_view_with_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('follow_user')
        following = Token.objects.filter(is_active = True).exclude(token = token.token).last().user
        response = self.client.post(url, {'following_id': following.id}, headers= headers, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        url = reverse('unfollow_user')
        response = self.client.delete(url, {'following_id': following.id}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout(self):
        token = Token.objects.filter(is_active = True).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('logout')
        response = self.client.post(url, headers = headers)
        assert response.status_code == status.HTTP_200_OK
        assert Token.objects.filter(user=token.user, is_active=False).exists()

    def test_logout__with_no_header_authentication(self):
        token = Token.objects.filter(is_active = True).last()
        url = reverse('logout')
        response = self.client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Token.objects.filter(user=token.user, is_active=True).exists()

    def test_logout_with_inactive_token(self):
        Token.objects.filter(is_active = True).update(is_active = False)
        token = Token.objects.filter(is_active = False).last()
        headers = {'Authorization': f'{token.token}'}
        url = reverse('logout')
        response = self.client.post(url, headers = headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Token.objects.filter(user=token.user, is_active=False).exists()
