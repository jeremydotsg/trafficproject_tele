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
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import urllib3
import json
import os
import telepot

# Local application/library specific imports
from .forms import DivErrorList, QueueStatusForm
from .models import (BusArrival, BusStop, Category, Comment, Direction, Post, Queue,
                     QueueLength, QueueStatus, QueueType, TelegramUpdate)
# from chartjs.views.lines import BaseLineChartView
load_dotenv()
logger = logging.getLogger('trafficdb')


# Bot Settings
# Dev Only
is_dev = False
bot = None
if os.getenv('ENVIRONMENT') == 'dev':
    from unittest.mock import MagicMock
    bot=MagicMock()
    is_dev=True
# Prod Only
if os.getenv('ENVIRONMENT') == 'prod':
    # Load the .env file
    load_dotenv()
    
    # Get the variables from the environment
    proxy_url = os.getenv('PROXY_URL', '')
    tele_secret = os.getenv('TELE_SECRET', '')
    webhook_url = os.getenv('WEBHOOK_URL', '')
    
    # Set up telepot with proxy
    telepot.api._pools = {
        'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
    }
    telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))
    
    # Initialize bot with secret token
    bot = telepot.Bot(tele_secret)
    bot.setWebhook(webhook_url, max_connections=1)

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
        acct_key = os.getenv('ACCT_KEY')
        headers = {'AccountKey': acct_key}
        url = os.getenv('BUS_ARRIVAL_URL')
        response = requests.get(url + bus_stop_code, headers=headers)
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

@login_required
def bus_stop_view(request):
    logger.info('BusStop :: Start ')
    get_bus_arrivals_web()
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

def check_requests_rate(from_id):
    one_minute_ago = timezone.now() - timedelta(minutes=1)
    two_minutes_ago = timezone.now() - timedelta(minutes=2)

    requests_last_minute = TelegramUpdate.objects.filter(
        from_id=from_id, 
        created_at__gte=one_minute_ago
    ).count()

    requests_last_two_minutes = TelegramUpdate.objects.filter(
        from_id=from_id, 
        created_at__gte=two_minutes_ago
    ).count()

    return requests_last_minute >= 5 or requests_last_two_minutes >= 10

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        msg = json.loads(request.body)
        logger.info('Webhook :: Msg: ' + str(msg))
        
        # Store the raw JSON and other details in the database
        update_id = msg.get('update_id')
        message = msg.get('message', {})
        from_user = message.get('from', {})
        
        TelegramUpdate.objects.create(
            update_id=update_id,
            message=json.dumps(message),  # Convert the message dict to a JSON string
            from_id=from_user.get('id'),
            from_is_bot=from_user.get('is_bot', False),
            from_first_name=from_user.get('first_name', ''),
            from_last_name=from_user.get('last_name', ''),
            from_username=from_user.get('username', ''),
            from_language_code=from_user.get('language_code', ''),
            raw_json=msg  # Store the entire raw JSON
        )
        if "message" in msg:
            chat_id = message["chat"]["id"]
            msg_id = message["message_id"]
            if check_requests_rate(from_user.get('id')):
                if is_dev:
                    logger.info('Webhook :: Rate Check: Too many commands.')
                else: 
                    bot.sendMessage(chat_id, "Slow down!")
                return HttpResponse("OK")
            if "text" in message:
                text = message["text"]
                # Check if the text starts with '/'
                if text.startswith('/'):
                    # Process the command
                    command = text[1:].split()[0]  # Extract the command without the '/'
                    # Add your command processing logic here
                    # For example, if the command is 'start', send a welcome message
                    if command == 'start':
                        bot.sendMessage(chat_id, "Welcome! How can I help you today?")
                    elif command == 'hello':
                        bot.sendMessage(chat_id, "Hello! I am alive!")
                    elif command in ['causeway1','causeway2','tuas1','tuas2']:
                        sendReplyPhoto(command,chat_id,msg_id)
                    else:
                        bot.sendMessage(chat_id, "Command not recognized.")
                else:
                    bot.sendMessage(chat_id, "Don't send me junk!".format(text))
            else:
                bot.sendMessage(chat_id, "Don't send me junk!")
        return HttpResponse("OK")
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def sendReplyPhoto(where,chat_id,msg_id):
    logger.info('Webhook :: Msg: ' + str(where))
    photo_dict = {
        "causeway1": "2701",
        "causeway2": "2702",
        "tuas1": "4703",
        "tuas2": "4713"
        }
    caption_dict = {
        "causeway1": "Causeway (on bridge).",
        "causeway2": "Causeway (in SG).",
        "tuas1": "2nd Link (on bridge).",
        "tuas2": "2nd Link (in SG)."
        }
    if where is None:
        bot.sendMessage(chat_id, "Don't Play Play Lah!")
    else:
        #Call API and get URL
        photo_url=getPhotoUrlFromLTA(photo_dict[where])
        if is_dev:
            logger.info('Webhook :: URL: ' + str(photo_url))
        else: 
            bot.sendPhoto(chat_id, photo_url, caption=caption_dict[where], reply_to_message_id=msg_id)
        
def getPhotoUrlFromLTA(id):
    #Headers
    acct_key = os.getenv('ACCT_KEY')
    headers = {'AccountKey': acct_key,
        'accept': 'application/json'}
    
    url = os.getenv('TRAFFIC_IMAGES_URL')
    response = requests.get(url, headers=headers)
    data = response.json()
    
    image_link = next((camera['ImageLink'] for camera in data['value'] if camera['CameraID'] == id), None)
    return image_link

def validate_token(token_id,token_to_validate):
    #Get Token from env
    token = os.getenv(token_id, '')
    if token == token_to_validate:
        return True
    else:
        return False
    
