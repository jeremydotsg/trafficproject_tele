# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import QueueStatus

@receiver(post_save, sender=QueueStatus)
def clear_cache(sender, instance, **kwargs):
    cache_key = 'queue_status_{}'.format(instance.queue.id)
    cache.delete(cache_key)
