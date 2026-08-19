from django.contrib import admin
from .models import Comment, Reply, Rating, Report

admin.site.register(Comment)
admin.site.register(Reply)
admin.site.register(Rating)
admin.site.register(Report)



