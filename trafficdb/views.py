# Standard library imports
from collections import Counter
from datetime import datetime, timedelta

# Related third party imports
from django.db.models import Avg, F, Max, OuterRef, Subquery
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.utils.functional import empty
from django.views import View, generic
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
import requests
import pytz
import logging

# Local application/library specific imports
from .forms import DivErrorList, QueueStatusForm
from .models import (BusArrival, BusStop, Category, Comment, Direction, Post, Queue,
                     QueueLength, QueueStatus, QueueType)
# from chartjs.views.lines import BaseLineChartView

logger = logging.getLogger('trafficdb')

#Create your views here.
@method_decorator(never_cache, name='dispatch')
class IndexView(View):
    def get(self,request):
        packed = {}
        direction_pack = {}
        logger.info('Dashboard :: Start')
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
        logger.info('Dashboard :: End')
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
    logger.info('Queue :: Start ' + str(queue_id))
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
                logger.info('Queue :: Error > five updates.')
    else:
        form = QueueStatusForm(error_class=DivErrorList)

    context = {
        'queue': queue,
        'queue_status': queue_status,
        'form': form
    }
    logger.info('Queue :: End - ' + str(queue_id))
    return render(request, 'trafficdb/queue_detail.html', context)

def disclaimer(request):
    logger.info('Disclaimer :: Start/End ')
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
        logger.info('Views - Real IP: ' + str(real_ip) + ', Remote IP: ' + str(remote_ip) + ', Forwarded IP: ' + str(forwarded_ip))
        if not real_ip:
            if not forwarded_ip:
                ip = remote_ip
            else:
                ip = forwarded_ip
        else:
            ip = real_ip
        return ip
    return ip

def get_bus_arrivals(request):
    logger.info('BusArrivals :: Start ')
    if request.method == 'GET':
        # The request is a POST request
        api_key = request.GET.get('secret_api_key')
        api_key_token = 'zCqKd62JYUOrtfTXiECJuC4yJiJYlFxj9vGkFtdaKP6fjfblABXXGxUe832IrjZc'
        if api_key_token == api_key:
            send_bus_request('46101')
            send_bus_request('46211')
            send_bus_request('46219')
            send_bus_request('46109')
            logger.info('BusArrivals :: End - Ok ')
            return HttpResponse('OK')
        else:
            logger.info('BusArrivals :: End - Denied due to token.')
            return HttpResponseForbidden('<h1>Access Denied</h1>')
    else:
        logger.info('BusArrivals :: End - Denied due to wrong method.')
        return HttpResponseForbidden('<h1>Access Denied</h1>')
    
def get_bus_arrivals_web():
    send_bus_request('46101')
    send_bus_request('46211')
    send_bus_request('46219')
    send_bus_request('46109')

def send_bus_request(bus_stop_code):
    logger.info('BusRequest :: Bus Stop Code' + bus_stop_code)
    # Get the current time
    current_time = timezone.now()
    # Calculate the time one hour ago from the current time
    mins_ago = current_time - timedelta(seconds=58)
    
    if not BusArrival.objects.filter(bus_stop=bus_stop_code,createdTime__gte=mins_ago):
        headers = {'AccountKey': 'v8nXM0XUTOie45jSW9tLzA=='}
        response = requests.get(f'http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2?BusStopCode={bus_stop_code}', headers=headers)
        data = response.json()
    
        for service in data['Services']:
            bus_arrival = BusArrival(bus_stop = data['BusStopCode'],
                service_no=service['ServiceNo'],
                operator=service['Operator'],
                next_bus=service['NextBus'],
                next_bus_2=service['NextBus2'],
                next_bus_3=service['NextBus3'],
            )
            bus_arrival.save()
    else:
        logger.info('BusRequest :: Not sent due to within 1 min.')
        

# class LineChartJSONView(BaseLineChartView):
#     def get_labels(self):
#         """Return the labels for the x-axis."""
#         bus_arrivals = BusArrival.objects.all()
#         sg_tz = pytz.timezone('Asia/Singapore')
#         labels = [timezone.localtime(arrival.createdTime, sg_tz).strftime('%Y-%m-%d %H:%M:%S') for arrival in bus_arrivals]
#         return labels[::5]  # Return every 5th label
#
#     def get_data(self):
#         """Return dataset to plot."""
#         bus_arrivals = BusArrival.objects.all()
#         sg_tz = pytz.timezone('Asia/Singapore')
#
#         # Group bus arrivals by bus stop code and service number
#         grouped_arrivals = {}
#         for arrival in bus_arrivals:
#             key = (arrival.bus_stop, arrival.service_no)
#             if key not in grouped_arrivals:
#                 grouped_arrivals[key] = []
#             estimated_arrival = parse_datetime(arrival.next_bus['EstimatedArrival'])
#             estimated_arrival = timezone.localtime(estimated_arrival, sg_tz)
#             created_time = timezone.localtime(arrival.createdTime, sg_tz)
#             time_difference = (estimated_arrival - created_time).total_seconds() / 60  # in minutes
#             grouped_arrivals[key].append(time_difference)
#
#         # Return every 5th time difference for each group
#         return {key: values[::5] for key, values in grouped_arrivals.items()}
#
# line_chart = TemplateView.as_view(template_name='trafficdb/line_chart.html')
# line_chart_json = LineChartJSONView.as_view()

# class LineChartJSONView(BaseLineChartView):
#
#     def get_labels(self):
#         labels = [bus_arrival.createdTime for bus_arrival in BusArrival.objects.filter().all() if bus_arrival.createdTime]
#         return labels
#
#     def get_providers(self):
#         providers = BusArrival.objects.filter().values_list('service_no', 'bus_stop').distinct()
#         providers = [f'{service_no},{bus_stop}' for service_no, bus_stop in providers]
#         return providers
#
#     def get_data(self):
#         data = []
#         providers = self.get_providers()
#         labels = self.get_labels()
#         sg_tz = pytz.timezone('Asia/Singapore')
#         for provider in providers:
#             service_no, bus_stop = provider.split(',')
#             provider_data = []
#             for label in labels:
#                 bus_arrival = BusArrival.objects.filter(service_no=service_no, bus_stop=bus_stop, createdTime=label).first()
#                 if bus_arrival:
#                     estimated_arrival = parse_datetime(bus_arrival.next_bus['EstimatedArrival'])
#                     if estimated_arrival:
#                         estimated_arrival = timezone.localtime(estimated_arrival, sg_tz)
#                         created_time = timezone.localtime(bus_arrival.createdTime, sg_tz)
#                         time_difference = (estimated_arrival - created_time).total_seconds() / 60
#                         provider_data.append(time_difference)
#                 else:
#                     provider_data.append('')  # append None if there is no bus arrival for this label
#             data.append(provider_data)
#         return data
#
# line_chart = TemplateView.as_view(template_name='trafficdb/line_chart.html')
# line_chart_json = LineChartJSONView.as_view()

@login_required
def bus_stop_view(request):
    logger.info('BusStop :: Start ')
    #get_bus_arrivals_web()
    arrivals = []
    # First, we get the latest 'modifiedTime' for each 'bus_stop' and 'service_no'
    latest_times = BusArrival.objects.values('bus_stop', 'service_no').annotate(
        latest_time=Max('createdTime')
    )
    for entry in latest_times:
        latest_record = BusArrival.objects.filter(
            bus_stop=entry['bus_stop'], 
            service_no=entry['service_no'], 
            createdTime=entry['latest_time']
        ).first()
        if latest_record:
            # Get the BusStop entry with the same bus_stop code
            bus_stop_entry = get_object_or_404(BusStop, bus_stop=latest_record.bus_stop)
            # Add the friendly name as an attribute to the latest_record object
            latest_record.bus_stop_name = bus_stop_entry.bus_stop_name
            arrivals.append(latest_record)
    
    arrivals = sorted(arrivals, key=lambda x: (x.bus_stop, x.service_no))
    logger.info('BusStop :: End ')
    return render(request, 'trafficdb/bus_stop.html', {'arrivals': arrivals})
