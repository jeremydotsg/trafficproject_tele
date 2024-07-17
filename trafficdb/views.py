# Standard library imports
from collections import Counter
from datetime import datetime, timedelta

# Related third party imports
from django.db.models import Avg, F, Max, OuterRef, Subquery, Q
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
import time
import uuid
import re
from telepot.namedtuple import InputMediaPhoto

# Local application/library specific imports
from .forms import DivErrorList, QueueStatusForm
from .models import (BusArrival, BusStop, Category, Comment, Direction, Post, Queue,
                     QueueLength, QueueStatus, QueueType, TelegramRequest, BlockedTgUser, WhitelistTgUser, WhitelistGroup)
# from chartjs.views.lines import BaseLineChartView
load_dotenv()
logger = logging.getLogger('trafficdb')

# Random String to protect endpoint
randstring = uuid.uuid4().hex

# Bot Settings
# Dev Only
is_dev = False
bot = None
bot_name = os.getenv('BOT_NAME', '')
if os.getenv('ENVIRONMENT') in ['dev']:
    from unittest.mock import MagicMock
    bot=MagicMock()
    is_dev=True
elif os.getenv('ENVIRONMENT') in ['devbot', 'prod']:

    proxy_url = os.getenv('PROXY_URL', '')
    tele_secret = os.getenv('TELE_SECRET', '')
    webhook_url = os.getenv('WEBHOOK_URL', '') + randstring +'/'
    

    if os.getenv('ENVIRONMENT') == 'prod':
        # Set up telepot with proxy
        telepot.api._pools = {
            'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=100),
        }
        telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=100))

    # Initialize bot with secret token
    bot = telepot.Bot(tele_secret)
    bot.setWebhook(webhook_url, max_connections=1)

#Photos for causeway
photo_dict = {
    "causeway1": "2701",
    "causeway2": "2702",
    "tuas1": "4703",
    "tuas2": "4713"
    }

caption_dict = {
    "causeway1": "Wdls Causeway (Bridge).",
    "causeway2": "Wdls Causeway (Twds Chkpt).",
    "tuas1": "Tuas 2nd Link (Bridge).",
    "tuas2": "Tuas 2nd Link (Twds Chkpt)."
    }
msg_dict = {
    "start" : "Hello!\nI am here to provide you useful information on the crossborder Bus Queues and more.\nBy using this bot, you accept that your details will be recorded for the purpose of processing your requests.\nFor Traffic photos, I need to talk to my counterparts so it will take a while before I respond.",
    "junk" : "Don't send me junk!",
    "notallowed" : "Not allowed to use this command!",
    "dashboard" : "Check out the dashboard. https://t.me/CT_IMG_BOT/dashboard",
    "blacklist" : "Slow mode: Hey, you have found a hidden feature!. Others need my help too, so I need to put you on hold. Talk to you later!",
    "wait" : "Wait a moment...\nOn the way!"

}
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

def check_requests_rate_and_block(from_id,chat_id):

    #Time
    now = timezone.now()
    one_minute_ago = timezone.now() - timedelta(minutes=1)
    two_minutes_ago = timezone.now() - timedelta(minutes=2)

    #Whitelist
    whitelist_records = WhitelistTgUser.objects.filter(
        Q(from_id=from_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )
    if whitelist_records.exists():
        return False

    requests_last_minute = TelegramRequest.objects.filter(
        from_id=from_id,
        created_at__gte=one_minute_ago
    ).count()

    requests_last_two_minutes = TelegramRequest.objects.filter(
        from_id=from_id,
        created_at__gte=two_minutes_ago
    ).count()

    blocked_records = BlockedTgUser.objects.filter(
        Q(from_id=from_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )

    # Check if user is already blocked
    # Check if any records exist
    if blocked_records.exists():
        return True

    if requests_last_minute >= 5 or requests_last_two_minutes >= 10:
        BlockedTgUser.objects.create(from_id=from_id)
        bot.sendMessage(chat_id, msg_dict['blacklist'])
        logger.info("Webhook :: Rate Check: Blacklisting user " + str(from_id))
        return True

    return False

def check_whitelist(from_id):

    #Time
    now = timezone.now()

    #Whitelist
    whitelist_records = WhitelistTgUser.objects.filter(
        Q(from_id=from_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )
    if whitelist_records.exists():
        logger.info("Check Whitelist :: User is whitelisted :: Userid " + str(from_id))
        return True
    
    return False

def check_whitelist_group(group_id):

    #Time
    now = timezone.now()

    #Whitelist
    whitelist_records = WhitelistGroup.objects.filter(
        Q(group_id=group_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )
    if whitelist_records.exists():
        logger.info("Check Whitelist :: Group is whitelisted :: Groupid " + str(group_id))
        return True
    
    return False

@csrf_exempt
def webhook(request, ranid):
    if request.method == 'POST' and ranid == randstring:
        msg = json.loads(request.body)
        logger.info('Webhook :: Msg: ' + str(msg))
        # Store the raw JSON and other details in the database
        update_id = msg.get('update_id')
        message = msg.get('message', {})
        from_user = message.get('from', {})
        user_id = from_user.get('id')
        is_group = False
        is_process = False

        # Perform rate check before inserting into database
        if "message" in msg:
            chat_id = message["chat"]["id"]
            msg_id = message["message_id"]
            chat_type = message["chat"]["type"]
            chat_text = ""
            try:
                chat_text = message["text"]
            except Exception as e:
                logger.error("Webhook :: Ignore message and save it. {}".format(e)) 
                return HttpResponse("Request ignored.")
            logger.info("Webhook :: Chat type: " + str(chat_type))
            
            #if group
            if chat_type in ["group","supergroup"]:
                #check if the command is sent from Whitelisted group
                is_group = True
                if check_whitelist_group(chat_id):
                    #Proceed and check if it is sent by Whitelisted user.
                    if check_whitelist(user_id):
                        pattern = r"/(\w+)@(\w+)"
                        match = re.match(pattern, chat_text)
                        if match:
                            cmd, bm = match.groups()
                            if bm == bot_name:
                                is_process = True
                                command = cmd
                                logger.info("Webhook :: Group command " + str(cmd))
                            else:
                                is_process = False
                                logger.info("Webhook :: Group command for wrong bot received, bot_name " + str(bm))
                        else:
                            logger.info("Webhook :: Group command :: Wrong pattern.")
                else:
                    logger.info("Webhook :: Group command :: Non-whitelisted group.")
                
            elif chat_type == "private":
                logger.info("Webhook :: Private Message from user " + str(user_id))
                if check_requests_rate_and_block(user_id,chat_id):
                    logger.info('Webhook :: Rate Check: User is blacklisted')
                    return HttpResponse("Request ignored.")
                # if check_whitelist(user_id):
                # print("Webhook :: Whitelisted user :: ")
                pattern = r"/(\w+)"
                match = re.match(pattern, chat_text)
                if match:
                    command = match.group(1) 
                    is_process = True
                    logger.info("Webhook :: Private command " + str(command) + " from user " + str(user_id))
                else:
                    is_process = False
                    logger.info("Webhook :: Private command :: Wrong Pattern.")
                # else:
                #    logger.info("Webhook :: Msg sent from non-whitelisted user. Commit to database and not process command.")

            TelegramRequest.objects.create(
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

            if is_process:
                    # Add your command processing logic here
                    # For example, if the command is 'start', send a welcome message
                if command == 'start':
                    bot.sendMessage(chat_id, msg_dict['start'], reply_to_message_id=msg_id)
                elif command == 'hello':
                    bot.sendMessage(chat_id, msg_dict['start'], reply_to_message_id=msg_id)
                elif command in ['causeway1','causeway2','tuas1','tuas2']:
                    sendReplyPhoto(command,chat_id,msg_id)
                elif command in ['all1234','reload1234','showall']:
                    if check_whitelist(user_id):
                        if command in ['all1234','showall']:
                            print(is_group)
                            sendReplyPhotoGroup(chat_id,msg_id, is_group)
                        elif command == 'reload1234':
                            reloadPhotos(chat_id,msg_id)
                    else:
                        if not is_group:
                            bot.sendMessage(chat_id, msg_dict['notallowed'], reply_to_message_id=msg_id)                        
                elif command == 'dashboard':
                     bot.sendMessage(chat_id, msg_dict['dashboard'], reply_to_message_id=msg_id)
                else:
                    if not is_group:
                        bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
            else:
                if not is_group:
                    bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
        return HttpResponse("OK")
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def getPhotoUrlFromLTA(id):
    camera_id = None
    file_path = os.getenv('STATIC_IMG_PATH')
    img_full_path = os.path.join(file_path, f"image{id}.jpg")

    # Check if the file exists and was modified within the last 5 minutes
    if os.path.exists(img_full_path) and (time.time() - os.path.getmtime(img_full_path)) < 300:
        return img_full_path
    else:
        # Call LTA's API to pull all the images required
        acct_key = os.getenv('ACCT_KEY')
        headers = {'AccountKey': acct_key, 'accept': 'application/json'}

        # Get the URL from environment variable
        url = os.getenv('TRAFFIC_IMAGES_URL')
        
        # Make the request
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for item in data["value"]:
                if item["CameraID"] in photo_dict.values():
                    image_url = item["ImageLink"]
                    camera_id = item["CameraID"]
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        full_file_name = os.path.join(file_path, f"image{camera_id}.jpg")
                        with open(full_file_name, 'wb') as file:
                            file.write(image_response.content)
        return img_full_path

def sendReplyPhoto(where,chat_id,msg_id):
    logger.info('Webhook :: Msg: ' + str(where))
    bot.sendMessage(chat_id, msg_dict['wait'])
    if where is None:
        bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
    else:
        #Call API and get URL
        photo_url=getPhotoUrlFromLTA(photo_dict[where])
        if is_dev:
            logger.info('Webhook :: Path: ' + str(photo_url))
        else:
            logger.info('Webhook :: Path: ' + str(photo_url))
            try:
                bot.sendPhoto(chat_id, open(photo_url,'rb'), caption=caption_dict[where], reply_to_message_id=msg_id)
            except Exception as e:
                logger.error('Failed to send photo: {}'.format(e))
                bot.sendMessage(chat_id,'Failed to send photo.', reply_to_message_id=msg_id)

def sendReplyPhotoGroup(chat_id,msg_id,is_group):
    # Get photo from LTA or local
    bot.sendMessage(chat_id, msg_dict['wait'])
    media_group = []
    for key, value in photo_dict.items():
        input_media = None
        photo_url = getPhotoUrlFromLTA(value)
        if photo_url:
            logger.info('Photo Path :: ' + str(photo_url))
            input_media = InputMediaPhoto(media=open(photo_url,'rb'),caption=caption_dict[key])
            media_group.append(input_media)
    if is_group:
        bot.sendMediaGroup(chat_id=chat_id, media=media_group)
    else:
        bot.sendMediaGroup(chat_id=chat_id, media=media_group, reply_to_message_id=msg_id)
    
def reloadPhotos(chat_id, msg_id):
    file_path = os.getenv('STATIC_IMG_PATH')
    msg_to_send = ""
    logger.info('Reload Photos :: Start')
    
    for key, value in photo_dict.items():  # Corrected iteration over items
        img_full_path = os.path.join(file_path, f"image{value}.jpg")
        
        try:
            if os.path.exists(img_full_path):  # Corrected path check
                os.remove(img_full_path)
                logger.info(f"The file {img_full_path} has been deleted.")
                msg_to_send += 'Removed image' + value + '.jpg.\n'
            else:
                logger.info(f"The file {img_full_path} does not exist.")
                msg_to_send += 'Not exist image' + value + '.jpg.\n'
        except Exception as e:
            logger.error(f"Error deleting file {img_full_path}: {e}")
            msg_to_send += f" Error deleting image{value}.jpg.\n"

    msg_to_send += 'Completed all deletion. Proceed to pull new photos.'
    bot.sendMessage(chat_id, msg_to_send, reply_to_message_id=msg_id)
    sendReplyPhotoGroup(chat_id, msg_id, False)
    logger.info('Reload Photos :: End')


def validate_token(token_id,token_to_validate):
    #Get Token from env
    token = os.getenv(token_id, '')
    if token == token_to_validate:
        return True
    else:
        return False