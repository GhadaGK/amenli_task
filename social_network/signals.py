from django.db.models.signals import Signal
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .models import Follow, Like

user_followed = Signal()
user_unfollowed = Signal()
post_liked = Signal()
post_unliked = Signal()

@receiver(post_save, sender=Follow)
def user_followed_handler(sender, instance, created, **kwargs):
    if created:
        user_followed.send(sender=instance.follower, target_user=instance.following)

@receiver(post_delete, sender=Follow)
def user_unfollowed_handler(sender, instance, **kwargs):
    user_unfollowed.send(sender=instance.follower, target_user=instance.following)

@receiver(post_save, sender=Like)
def post_liked_handler(sender, instance, created, **kwargs):
    if created:
        post_liked.send(sender=instance.user, target_post=instance.post)

@receiver(post_delete, sender=Like)
def post_unliked_handler(sender, instance, **kwargs):
    post_unliked.send(sender=instance.user, target_post=instance.post)

