from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views import View
from django.views import generic
from django.utils import timezone
from django.db.models import F, Max, OuterRef, Subquery
from .models import Queue, Direction, QueueStatus, QueueType, QueueLength, Post, Comment, Category
from .forms import QueueStatusForm, DivErrorList
from django.utils.functional import empty
from django.db.models import Avg
from datetime import timedelta
import datetime
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

#Create your views here.
@method_decorator(never_cache, name='dispatch')
class IndexView(View):
    def get(self,request):
        packed = {}
        direction_pack = {}

        # Get the current time
        current_time = timezone.now()
        # Calculate the time one hour ago from the current time
        one_hour_ago = current_time - timedelta(minutes=60)

        # Get the number of directions
        for each_direction in Direction.objects.all():
            queue_type_pack = {}
            # Get the queue types
            for each_queue_type in QueueType.objects.filter(queueTypeDisplay=True).order_by('-queueTypeDisplayOrder').all():
                queue_pack = {}
                # Get the queues
                for each_queue in Queue.objects.filter(direction=each_direction, queueType=each_queue_type).all():
                    # Subquery to get the latest createdTime for each queue
                    queue_statuses = QueueStatus.objects.filter(queue=each_queue,createdTime__gte=one_hour_ago).select_related('queue', 'queueLength').all()
                    # Calculate the average queueLengthValue for each Queue
                    average_queue_lengths = queue_statuses.values('queue__queueName').annotate(averageLength=Avg('queueLength__queueLengthValue')).all()
                    # Main query to get the latest queueLength for each queue
                    if not average_queue_lengths:
                        queue_pack[each_queue] = ''
                    else:
                        for queue_status in average_queue_lengths:
                            queue_pack[each_queue] = queue_status
                queue_type_pack[each_queue_type] = queue_pack
            direction_pack[each_direction.directionName] = queue_type_pack

        data = {
            'packed': direction_pack
        }
        return render(request, 'trafficdb/index.html', data)

# @method_decorator(never_cache, name='dispatch')
# class IndexView(View):
#     def get(self,request):
#         packed = {}
#         direction_pack = {}
#
#         # Get the current time
#         current_time = timezone.now()
#         # Calculate the time one hour ago from the current time
#         one_hour_ago = current_time - timedelta(minutes=60)
#
#         # Query to get all QueueStatus entries with their related Queue and QueueLength
#         # that were created within the last hour
#         queue_statuses = QueueStatus.objects.filter(createdTime__gte=one_hour_ago,queueLength__queueTypeDisplay=True).select_related('queue','queueLength')
#         # Calculate the average queueLengthValue for each Queue
#         average_queue_lengths = queue_statuses.values('queue__queueName').annotate(averageLength=Avg('queueLength__queueLengthValue'))
#
#         # This will give you a queryset with the queue name and the average queue length
#         for queue_info in average_queue_lengths:
#             print(str(queue_info))
#
#         #Get the number of directions
#         for each_direction in Queue.objects.values_list('direction',flat=True).distinct():
#             queue_pack = {}
#             #Get the queues
#             direction_name = Direction.objects.get(id=each_direction).directionName
#             print(direction_name)
#             for each_queue in Queue.objects.filter(direction=each_direction).all():
#                 # Subquery to get the latest createdTime for each queue
#                 queue_statuses = QueueStatus.objects.filter(queue=each_queue,createdTime__gte=one_hour_ago).select_related('queue', 'queueLength').all()
#                 print(queue_statuses)
#                 # Calculate the average queueLengthValue for each Queue
#                 average_queue_lengths = queue_statuses.values('queue__queueName').annotate(averageLength=Avg('queueLength__queueLengthValue')).all()
#                 # Main query to get the latest queueLength for each queue
#                 if not average_queue_lengths:
#                     queue_pack[each_queue] = ''
#                 else:
#                     for queue_status in average_queue_lengths:
#                         print('Status:' + str(queue_status))
#                         queue_pack[each_queue] = queue_status
#                 direction_pack[direction_name] = queue_pack
#
#         #print(direction_pack)
#         data = {
#             'packed': direction_pack
#         }
#         #print(data)
#         return render(request, 'trafficdb/index.html', data)


def queue_list(request):
    queues = Queue.objects.all()
    queue_statuses = QueueStatus.objects.select_related('queue').all()
    context = {
        'queues': queues,
        'queue_statuses': queue_statuses
    }
    return render(request, 'trafficdb/queue_list.html', context)

def queue_detail(request, queue_id):
    queue = get_object_or_404(Queue, id=queue_id)

    # Get the current time
    current_time = timezone.now()
    # Calculate the time one hour ago from the current time
    one_hour_ago = current_time - timedelta(minutes=60)

    queue_status = QueueStatus.objects.filter(queue=queue,createdTime__gte=one_hour_ago).order_by('-createdTime').first()
    if request.method == 'POST':
        form = QueueStatusForm(request.POST, error_class=DivErrorList)
        ip_address = get_client_ip(request)
        if form.is_valid():
            if not QueueStatus.has_reached_update_limit(ip_address):
                new_status = form.save(commit=False)
                new_status.queueIP = ip_address
                new_status.queue = queue
                new_status.save()
                return redirect('trafficdb:queue_detail', queue_id=queue.id)
            else:
                # Pass the form with errors back to the template
                form = QueueStatusForm(error_class=DivErrorList)
                print('Error >= 5')
    else:
        form = QueueStatusForm(error_class=DivErrorList)

    context = {
        'queue': queue,
        'queue_status': queue_status,
        'form': form
    }
    return render(request, 'trafficdb/queue_detail.html', context)

def disclaimer(request):
    return render(request, 'trafficdb/disclaimer.html')
# class IndexView(generic.ListView):
#     template_name = "trafficdb/index.html"
#     context_object_name = "queueStatusList"
#
#     def get_queryset(self):
#         """
#         Return the last five published questions (not including those set to be
#         published in the future).
#         """
#         return QueueStatus.objects.filter(createdTime__lte=timezone.now()).order_by("-createdTime")[
#             :5
#         ]



def blog_index(request):
    posts = Post.objects.all().order_by("-created_on")
    context = {
        "posts": posts,
    }
    return render(request, "trafficdb/blog_index.html", context)


def blog_category(request, category):
    posts = Post.objects.filter(
        categories__name__contains=category
    ).order_by("-created_on")
    context = {
        "category": category,
        "posts": posts,
    }
    return render(request, "trafficdb/category.html", context)

def blog_detail(request, pk):
    post = Post.objects.get(pk=pk)
    comments = Comment.objects.filter(post=post)
    context = {
        "post": post,
        "comments": comments,
    }

    return render(request, "trafficdb/detail.html", context)

def get_client_ip(request):
    """Get the client IP address from the request object."""
    ip = None
    if request:
        real_ip = request.META.get("X_REAL_IP", "")
        remote_ip = request.META.get("REMOTE_ADDR", "")
        forwarded_ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
        print('Views - Real IP: ' + str(real_ip) + ', Remote IP: ' + str(remote_ip) + ', Forwarded IP: ' + str(forwarded_ip))
        if not real_ip:
            if not forwarded_ip:
                ip = remote_ip
            else:
                ip = forwarded_ip
        else:
            ip = real_ip
        return ip
    return ip