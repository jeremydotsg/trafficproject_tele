from django.contrib import admin
from .models import Direction, Queue, QueueType, QueueLength,QueueStatus
from .models import Category, Comment, Post

from django.contrib import admin

import trafficdb.models as models


class DirectionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'directionName',
        'directionDesc',
        'directionDisplay',
        'createdTime',
        'modifiedTime',
    )
    list_filter = (
        'directionDisplay',
        'createdTime',
        'modifiedTime',
        'id',
        'directionName',
        'directionDesc',
    )


class QueueTypeAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'queueTypeName',
        'queueTypeDisplay',
        'createdTime',
        'modifiedTime',
    )
    list_filter = (
        'queueTypeDisplay',
        'createdTime',
        'modifiedTime',
        'id',
        'queueTypeName',
    )


class QueueLengthAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'queueLength',
        'queueColor',
        'queueLengthValue',
        'queueTypeDisplay',
        'createdTime',
        'modifiedTime',
    )
    list_filter = (
        'queueTypeDisplay',
        'queueLengthValue',
        'createdTime',
        'modifiedTime',
        'id',
        'queueColor',
        'queueLength',
    )

class QueueStatusInline(admin.TabularInline):
    model = QueueStatus
    choice = 10

class QueueAdmin(admin.ModelAdmin):
    inlines=[QueueStatusInline]
    list_display = (
        'id',
        'queueName',
        'queueDesc',
        'direction',
        'queueType',
        'createdTime',
        'modifiedTime',
    )
    list_filter = (
        'direction',
        'queueType',
        'createdTime',
        'modifiedTime',
        'id',
        'queueName',
        'queueDesc',
    )

class QueueStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'queue',
        'queueLength',
        'queueIP',
        'createdTime',
        'modifiedTime',
    )
    list_filter = (
        'id',
        'queue',
        'queueIP',
        'queueLength',
        'createdTime',
        'modifiedTime',
    )

class CategoryAdmin(admin.ModelAdmin):
    pass

class PostAdmin(admin.ModelAdmin):
    pass

class CommentAdmin(admin.ModelAdmin):
    pass

def _register(model, admin_class):
    admin.site.register(model, admin_class)


_register(models.Direction, DirectionAdmin)
_register(models.QueueType, QueueTypeAdmin)
_register(models.QueueLength, QueueLengthAdmin)
_register(models.Queue, QueueAdmin)
_register(models.QueueStatus, QueueStatusAdmin)

_register(models.Category, CategoryAdmin)
_register(models.Post, PostAdmin)
_register(models.Comment, CommentAdmin)