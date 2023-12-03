from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amenli_task.settings')

celery_app = Celery('social_network')

celery_app.config_from_object('django.conf:settings', namespace='CELERY')

celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
