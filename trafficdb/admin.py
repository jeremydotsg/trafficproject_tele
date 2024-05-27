from django.contrib import admin
from .models import Direction, Queue, QueueType, QueueLength,QueueStatus    

# Register your models here.
# class DirectionAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ("Direction Config", {"fields": ["direction_text","direction_helptext","direction_display"]}),
#     ]
#     list_display = ["direction_text","direction_helptext","direction_display"]
#     #list_filter = ["pub_date"]
#     #list_display = ["question_text", "pub_date", "was_published_recently"]
#     #search_fields = ["question_text"]
#
# class QueueTypeAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ("Queue Type Config", {"fields": ["queue_type_display"]}),
#     ]
#     list_display = ["queue_type_display"]
#
#
#
# class QueueLengthAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ("Queue Length", {"fields": ["queue_length_text"]}),
#     ]
#     list_display = ["queue_length_text"]
#
# class QueueStatusInline(admin.TabularInline):
#     model = QueueStatus
#     extra = 3
#
# class QueueAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ("Queue Config", {"fields": ["direction_type","queue_display","queue_helptext","queue_type"]}),
#     ]
#     list_display = ["queue_display","direction_type","queue_helptext","queue_type"]
#     inlines = [QueueStatusInline]
#
# admin.site.register(Direction, DirectionAdmin)
# admin.site.register(QueueType, QueueTypeAdmin)
# admin.site.register(Queue, QueueAdmin)
# admin.site.register(QueueLength, QueueLengthAdmin)# vim: set fileencoding=utf-8 :
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
        'queueTypeDisplay',
        'queueColor',
        'createdTime',
        'modifiedTime',
    )
    list_filter = (
        'queueTypeDisplay',
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
    
def _register(model, admin_class):
    admin.site.register(model, admin_class)


_register(models.Direction, DirectionAdmin)
_register(models.QueueType, QueueTypeAdmin)
_register(models.QueueLength, QueueLengthAdmin)
_register(models.Queue, QueueAdmin)
