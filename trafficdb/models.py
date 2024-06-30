from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, get_default_timezone
from dateutil import parser
import datetime
import pytz

# Create your models here.

class Direction(models.Model):
    directionName = models.CharField(max_length=100)
    directionDesc = models.CharField(max_length=200)
    directionDisplay = models.BooleanField(default=True)
    createdTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    def __str__(self):
        return self.directionName

class QueueType(models.Model):
    queueTypeName = models.CharField(max_length=100)
    queueTypeDisplay = models.BooleanField(default=True)
    queueTypeDisplayOrder = models.IntegerField(default=0)
    createdTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    class Meta:
        verbose_name_plural = "Queue Types"
    def __str__(self):
        return self.queueTypeName

#Queue Length Options
class QueueLength(models.Model):
    queueLength = models.CharField(max_length=100)
    queueTypeDisplay = models.BooleanField(default=True)
    queueColor = models.CharField(max_length=100, default='')
    queueLengthValue = models.IntegerField()
    createdTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    class Meta:
        verbose_name_plural = "Queue Lengths"
    def __str__(self):
        return self.queueLength
        
class Queue(models.Model):
    queueName = models.CharField(max_length=100)
    queueDesc = models.CharField(max_length=200)
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE)
    queueType = models.ForeignKey(QueueType, on_delete=models.CASCADE)
    createdTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    def __str__(self):
        return f"{self.queueName}"
    
class QueueStatus(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    queueLength = models.ForeignKey(QueueLength, on_delete=models.CASCADE)
    queueIP = models.CharField(max_length=50,default=None, blank=True, null=True)
    createdTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=False,auto_now_add=True)
    class Meta:
        verbose_name_plural = "Queue Statuses"
    def __str__(self):
        return  str(self.queue) + ' - ' + str(self.queueLength)
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(minutes=30) <= self.createdTime <= now
    @classmethod
    def has_reached_update_limit(cls, ip_address):
        # Count the number of updates from the IP in the last hour
        recent_updates_count = cls.objects.filter(
            queueIP=ip_address,
            modifiedTime__gte=timezone.now() - timedelta(hours=1)
        ).count()
        return recent_updates_count >= 5

#For Blog
# blog/models.py
class Category(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("Category", related_name="posts")

    def __str__(self):
        return self.title

class Comment(models.Model):
    author = models.CharField(max_length=60)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey("Post", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author} on '{self.post}'"
    
class BusStop(models.Model):
    bus_stop = models.CharField(max_length=10)
    bus_stop_name = models.CharField(max_length=255)

class BusArrival(models.Model):
    bus_stop = models.CharField(max_length=10)
    service_no = models.CharField(max_length=10)
    operator = models.CharField(max_length=10)
    next_bus = models.JSONField()
    next_bus_2 = models.JSONField()
    next_bus_3 = models.JSONField()
    createdTime = models.DateTimeField(auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.service_no} on '{self.bus_stop}' at {self.createdTime}"
    
    def arrival_next_bus(self):
        estimated_arrival = self.next_bus.get('EstimatedArrival')
        if estimated_arrival:
            # Convert the string to a datetime object
            estimated_arrival = parser.parse(estimated_arrival)
            # Calculate the difference
            diff = estimated_arrival - self.createdTime.astimezone(pytz.timezone('Asia/Singapore'))
            # If the difference is negative, return 0
            return 'Arr' if diff.total_seconds() < 1 else int(diff.total_seconds()) // 60
        return None
    def arrival_next_bus2(self):
        estimated_arrival = self.next_bus_2.get('EstimatedArrival')
        if estimated_arrival:
            # Convert the string to a datetime object
            estimated_arrival = parser.parse(estimated_arrival)
            # Calculate the difference
            diff = estimated_arrival - self.createdTime.astimezone(pytz.timezone('Asia/Singapore'))
            # If the difference is negative, return 0
            return 'Arr' if diff.total_seconds() < 1 else int(diff.total_seconds()) // 60
        return None
    def arrival_next_bus3(self):
        estimated_arrival = self.next_bus_3.get('EstimatedArrival')
        if estimated_arrival:
            # Convert the string to a datetime object
            estimated_arrival = parser.parse(estimated_arrival)
            # Calculate the difference
            diff = estimated_arrival - self.createdTime.astimezone(pytz.timezone('Asia/Singapore'))
            # If the difference is negative, return 0
            return 'Arr' if diff.total_seconds() < 1 else int(diff.total_seconds()) // 60
        return None

class TelegramUpdate(models.Model):
    update_id = models.BigIntegerField()
    message = models.TextField()
    from_id = models.BigIntegerField()
    from_is_bot = models.BooleanField()
    from_first_name = models.CharField(max_length=255, blank=True, null=True)
    from_last_name = models.CharField(max_length=255, blank=True, null=True)
    from_username = models.CharField(max_length=255, blank=True, null=True)
    from_language_code = models.CharField(max_length=10, blank=True, null=True)
    raw_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Update ID: {self.update_id}" 