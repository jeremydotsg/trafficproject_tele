from django.db import models
from django.utils import timezone
from datetime import timedelta
import datetime

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
        return now - datetime.timedelta(hour=1) <= self.createdTime <= now
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