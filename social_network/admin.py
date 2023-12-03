from django.contrib import admin
from .models import *

admin.site.register(Post)

admin.site.register(Comment)

admin.site.register(Follow)

admin.site.register(Like)

admin.site.register(Token)
