from celery import shared_task
from django.core.mail import send_mail
import logging
from .models import *
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task
def send_comment_notification_email(post_author_email, comment_content):
    try:
        subject = 'New Comment Notification'
        message = f'Hello,\n\nA new comment has been added to your post. Comment: {comment_content}'
        from_email = "ghadagk98@gmail.com"
        recipient_list = [post_author_email]
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        logger.error(f"Error sending email: {e}")

@shared_task
def send_feedback_email():
    posts = Post.objects.all()
    for post in posts :
        post_author_email = post.user.email
        created_time = post.created_at
        current_time = timezone.now()
        comments = Comment.objects.filter(post__id = post.id).count()
        if current_time - created_time > timedelta(minutes=48):
            subject = 'Feedback for Your Post'
            message = f'Your post has reached {comments} impressions so far, View it now.'
            from_email = "ghadagk98@gmail.com"
            recipient_list = [post_author_email]
            send_mail(subject, message, from_email, recipient_list)