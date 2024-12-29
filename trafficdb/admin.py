from django.contrib import admin
from .models import *

import trafficdb.models as models

@admin.register(models.Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'directionName', 'directionDesc', 'directionDisplay', 'createdTime', 'modifiedTime')
    list_filter = ('directionDisplay', 'createdTime', 'modifiedTime', 'id', 'directionName', 'directionDesc')

@admin.register(models.QueueType)
class QueueTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'queueTypeName', 'queueTypeDisplay', 'createdTime', 'modifiedTime')
    list_filter = ('queueTypeDisplay', 'createdTime', 'modifiedTime', 'id', 'queueTypeName')

@admin.register(models.QueueLength)
class QueueLengthAdmin(admin.ModelAdmin):
    list_display = ('id', 'queueLength', 'queueColor', 'queueLengthValue', 'queueTypeDisplay', 'createdTime', 'modifiedTime')
    list_filter = ('queueTypeDisplay', 'queueLengthValue', 'createdTime', 'modifiedTime', 'id', 'queueColor', 'queueLength')

class QueueStatusInline(admin.TabularInline):
    model = models.QueueStatus
    extra = 2

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        class BaseFormSet(formset):
            def get_queryset(self):
                qs = super().get_queryset()
                return qs.order_by('-createdTime')[:5]
        
        return BaseFormSet

@admin.register(models.Queue)
class QueueAdmin(admin.ModelAdmin):
    inlines = [QueueStatusInline]
    list_display = ('id', 'queueName', 'queueDesc', 'direction', 'queueType', 'createdTime', 'modifiedTime')
    list_filter = ('direction', 'queueType', 'createdTime', 'modifiedTime', 'id', 'queueName', 'queueDesc')

@admin.register(models.QueueStatus)
class QueueStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'queue', 'queueLength', 'queueIP', 'queueUserId', 'createdTime', 'modifiedTime')
    list_filter = ('id', 'queue', 'queueIP', 'queueUserId', 'queueLength', 'createdTime', 'modifiedTime')

@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    pass

@admin.register(models.BusArrival)
class BusArrivalAdmin(admin.ModelAdmin):
    list_display = ('bus_stop', 'service_no', 'operator', 'next_bus', 'next_bus_2', 'next_bus_3', 'createdTime', 'modifiedTime')

@admin.register(models.BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ('bus_stop', 'bus_stop_name')
    search_fields = ('bus_stop', 'bus_stop_name')

@admin.register(models.TelegramRequest)
class TelegramRequestAdmin(admin.ModelAdmin):
    list_display = ('update_id', 'from_id', 'from_first_name', 'from_username', 'created_at', 'modified_at')
    search_fields = ('update_id', 'from_id', 'from_first_name', 'from_username', 'created_at', 'modified_at')
    readonly_fields = ('created_at', 'modified_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(models.BlockedTgUser)
class BlockedTgUserAdmin(admin.ModelAdmin):
    list_display = ('from_id', 'start_at', 'end_at', 'created_at')

@admin.register(models.WhitelistTgUser)
class WhitelistTgUserAdmin(admin.ModelAdmin):
    list_display = ('from_id', 'start_at', 'end_at', 'created_at', 'is_admin')

@admin.register(models.WhitelistGroup)
class WhitelistGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'created_at', 'start_at', 'end_at', 'remarks')
    search_fields = ('group_id', 'remarks')

@admin.register(models.TgQueueUpdate)
class TgQueueUpdateAdmin(admin.ModelAdmin):
    list_display = ('update_id', 'command', 'parameters', 'user_id', 'created_at', 'modified_at')
    search_fields = ('update_id', 'command', 'parameters', 'user_id')
    list_filter = ('update_id', 'command', 'parameters', 'user_id', 'created_at', 'modified_at')
