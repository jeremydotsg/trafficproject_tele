import telepot
from .models import *
import requests
import json
from dotenv import load_dotenv
from telepot.namedtuple import *
import os
import time
import logging
from django.db.models import Q
import re
from aiohttp.web_response import json_response
from . import weather
from . import botqueue
from . import extract_text
from django.conf import settings

load_dotenv()
logger = logging.getLogger('trafficdb')
bot = None
bot_name = os.getenv('BOT_NAME', '')
# Change here for any settings
causeway_cameras = ["2701","2702","2704"]
tuas_cameras = ["4703","4713", "4712"]

photo_dict = {
    "causeway1": "2701",
    "causeway2": "2702",
    "tuas1": "4703",
    "tuas2": "4713"
    }

caption_dict = {
    "2701": "Woodlands Causeway (Towards Johor)",
    "2702": "Woodlands Checkpoint",
    "2704": "BKE (Woodlands Checkpoint) - Woodlands F/O",
    "4703": "Tuas Second Link",
    "4712": "AYE(Tuas) - Tuas Ave 8 Exit",
    "4713": "Tuas Checkpoint",
    }
msg_dict = {
    "start" : "Hello!\n\nTalk to me about SG JB Cross Border Travel. Here is what I can help you with!\n\nBy using this Bot, you agree to the Terms and Conditions viewable at /tnc.",
    "hello" : "Gwenchana... Everything is fine.",
    "junk" : "I don't understand you. Don't pay play!",
    "notallowed" : "Unchartered waters ahead!",
    "dashboard" : "Check out the crowdsourced Bus or Checkpoint Queue! https://t.me/CT_IMG_BOT/dashboard",
    "blacklist" : "Slow mode: Hey, you have found a hidden feature!. Others need my help too, so I need to put you on hold. Talk to you later!",
    "wait" : "Wait a moment...",
    "lta_tnc" : "\nNote: This bot uses the LTA's Traffic Images dataset accessed at the time of request and made available under the terms of the <a href=\"https://datamall.lta.gov.sg/content/datamall/en/SingaporeOpenDataLicence.html\">Singapore Open Data Licence version 1.0</a>.",
    "job" : "Triggered job manually.",
    "beta"  : "Beta mode: Currently in limited beta mode. Watch out when this bot is available.",
    "tnc" : "<b>Terms & Conditions</b>\nBy interacting with this Bot, you agree to the <a href=\"https://mygowhere.pythonanywhere.com/trafficdb/disclaimer\">disclaimer published here</a>.\n",
    "getrate" : "Getting rate from CIMB.",
    "geteverything" : "Retrieving all traffic cameras. This will take a while.",
    "getstats" : "Getting server stats.",
}

resp = {
    'ignored' : 'Request ignored due to not in scope.',
    'nogrp' : 'Group not in whitelist.',
    'nousr' : 'User not in whitelist.',
    'wrongptn' : 'Wrong pattern for command.',
    'wrongbot' : 'Wrong bot.',
    'rate' : 'Slow mode: Rate limited.',
    'junk' : 'Junk received from user.',
    'generic' : 'Error. See logs.',
    'beta' : 'Beta Mode: User not in whitelist.',
    'processed' : 'Processed. See the addtional response for any errors.',
    'ok' : 'Ok, request processed.',
    'batchoff': 'Batch job turned off due to maintenance or beta mode.'
    }
# Contains all the methods to process bot requests
def process_telebot_request(request, bot):

    # Store the raw JSON and other details in the database
    update = json.loads(request.body)
    update_id = update["update_id"]
    is_group = False
    is_process = False
    has_param = False
    
    message = extract_msg(update)
    sender = extract_sender(message)
    command = ""
    param = ""
    #print(sender)
    
    if message is None:  
        x = TelegramRequest.objects.create(
            update_id=update_id,
            message="See Raw JSON.",  # Convert the message dict to a JSON string
            from_id='0',
            from_is_bot=False,
            from_first_name='Non-Msg-Update',
            from_last_name='Non-Msg-Update',
            from_username='Non-Msg-Update',
            from_language_code='',
            raw_json=update  # Store the entire raw JSON
        )
        return update_return_response(x,'ignored')
    elif message is not None:
        chat_id = message["chat"]["id"]
        msg_id = message["message_id"]
        from_user = message["from"]
        req_obj = TelegramRequest.objects.create(
            update_id=update_id,
            message=message,  # Convert the message dict to a JSON string
            from_id=sender.get('id','999999999'), # If it is a bot, will extract from the chat object of a private chat
            from_is_bot=sender.get('is_bot', False),
            from_first_name=sender.get('first_name', ''),
            from_last_name=sender.get('last_name', ''),
            from_username=sender.get('username', ''),
            from_language_code=from_user.get('language_code', ''),
            raw_json=update  # Store the entire raw JSON
        )
        chat_type = message["chat"]["type"]
        user_id = sender.get('id','999999999')
        logger.info("Webhook :: Chat type: " + str(chat_type))
        
        chat_text = extract_chat_text(update)
        if chat_text is None:
            logger.info("Webhook :: Ignore message and save it.")
            return update_return_response(req_obj,'ignored')
                        
        # Process only if it is group or private chats
        if chat_type in ["group","supergroup"]:
            is_group = True
            # Check if the command is sent from Whitelisted group
            if check_whitelist_group(chat_id):
                # Proceed and check if it is sent by Whitelisted user.
                if check_whitelist(user_id):
                    pattern = r"/(\w+)@(\w+)"
                    match = re.match(pattern, chat_text)
                    print(match)
                    if match:
                        cmd, bm = match.groups()
                        if bm == bot_name:
                            is_process = True
                            command = cmd
                            
                            logger.info("Webhook :: Group command " + str(cmd))
                        else:
                            # No Response
                            is_process = False
                            logger.info("Webhook :: Group command for wrong bot received, bot_name " + str(bm))
                            return update_return_response(req_obj,'wrongbot')
                    else:
                        # No Response for wrong pattern.
                        logger.info("Webhook :: Group command :: Wrong pattern.")
                        return update_return_response(req_obj,'wrongptn')
                else:
                    # No Response for non whitelisted user
                    logger.info("Webhook :: Group command :: Non-whitelisted user.")
                    return update_return_response(req_obj,'nousr')
            else:
                # No Response for non whitelisted group
                logger.info("Webhook :: Group command :: Non-whitelisted group.")
                return update_return_response(req_obj,'nogrp')
            
        elif chat_type == "private":
            logger.info("Webhook :: Private Message from user " + str(user_id))
            # Bypass Rate Limit Check and use the botqueue's own rate limit check
            if not chat_text.startswith("/queue"):
                if check_requests_rate_and_block(bot, user_id,chat_id):
                    logger.info('Webhook :: Rate Check: User is blacklisted')
                    return update_return_response(req_obj,'rate')
            # Still check for whitelists
            if not check_whitelist(user_id) and not check_whitelist("9999"):
                bot.sendMessage(chat_id, msg_dict['beta'])
                return update_return_response(req_obj,'beta')
            pattern = r"\/(\w+)\s?([\w\s]*)"
            # print("Try parsing command: " + chat_text)
            match = re.match(pattern, chat_text)
            # non_num_pattern = r"\/(\w+)\s?[^\d\s]*$/gm"
            # matches_non_num = re.match(non_num_pattern,params)
            # print(matches_non_num)
            if match:
                command, param = match.groups()
                is_process = True
                if param:
                    has_param = True
                    #print("Parsed Param: " + param)
                else:
                    param = ""
                #print("Parsed Command: " + command)
                
                logger.info("Webhook :: Private command " + str(command) + " from user " + str(user_id))
            else:
                print("No Command: " + str(chat_text))
                logger.info("Webhook :: Private command :: Wrong Pattern.")
                return update_return_response(req_obj,'wrongptn')
            # else:
            #    logger.info("Webhook :: Msg sent from non-whitelisted user. Commit to database and not process command.")
        
        else:
            logger.info("Webhook :: Chat Type is not Group, Supergroup or Private. Ignoring request.")
            return update_return_response(req_obj,'junk')

        if is_process:
            # Start Command - Display a welcome message
            if has_param:
                if command in ['queueb','queuec','queued']:
                    res = botqueue.handle_command(bot, sender, user_id, chat_id, command, param, update_id, is_group)
                    return update_return_response(req_obj,'ok', res)
                else:
                    # print("Command not supposed to have parameters." + str(command))
                    bot.sendMessage(chat_id, msg_dict['junk'])
                    return update_return_response(req_obj,'junk')
            if command == 'queuestart':
                res = botqueue.handle_command(bot, sender, user_id, chat_id, command, param, update_id, is_group)
                return update_return_response(req_obj,'ok', res)
            elif command == 'start':
                send_start_reply(bot, chat_id, msg_id, is_group)
                return update_return_response(req_obj,'ok')
            elif command == 'hello':
                bot.sendMessage(chat_id, msg_dict['hello'])
                return update_return_response(req_obj,'ok')      
            elif command == 'weather':
                bot.sendMessage(chat_id, weather.get_weather(), parse_mode="HTML")
                return update_return_response(req_obj,'ok')      
            elif command == 'tnc':
                if not is_group: bot.sendMessage(chat_id, msg_dict['tnc'], reply_to_message_id=msg_id, parse_mode="HTML")
                return update_return_response(req_obj,'ok')
            elif command == 'dashboard':
                bot.sendMessage(chat_id, msg_dict['dashboard'], reply_to_message_id=msg_id) if not is_group else bot.sendMessage(chat_id, msg_dict['dashboard'])
                return update_return_response(req_obj,'ok')
            # Photo Commands - Send the photos over
            elif command in ['causeway','tuas']:
                sendReplyPhoto(bot, command,chat_id,msg_id, is_group)
                return update_return_response(req_obj,'ok')            
            # Whitelist users (and groups) only commands
            elif command in ['reload','showall','grpcctv','grpweather', 'getrate','getstats']:
                if check_admin(user_id):
                    if command in ['showall']:
                        sendReplyPhotoGroup(bot, chat_id, msg_id, is_group)
                        return update_return_response(req_obj,'ok')  
                    elif command == 'reload':
                        reloadPhotos(bot, chat_id, msg_id, is_group)
                        return update_return_response(req_obj,'ok') 
                    elif command == 'grpcctv':
                        bot.sendMessage(chat_id, msg_dict['job']) 
                        process_routine_job(req_obj,bot)
                        return update_return_response(req_obj,'ok')
                    elif command == 'grpweather':
                        bot.sendMessage(chat_id, msg_dict['job']) 
                        process_weather(req_obj,bot)
                        return update_return_response(req_obj,'ok') 
                    elif command == 'getrate':
                        bot.sendMessage(chat_id, msg_dict['getrate'])
                        bot.sendMessage(chat_id, extract_text.get_rate())
                        return update_return_response(req_obj,'ok') 
                    elif command == 'getstats':
                        bot.sendMessage(chat_id, msg_dict['getstats'])
                        bot.sendMessage(chat_id, get_server_stats())
                        return update_return_response(req_obj,'ok')
                else:
                    if not is_group:
                        bot.sendMessage(chat_id, msg_dict['notallowed'], reply_to_message_id=msg_id) 
                        return update_return_response(req_obj,'nousr')                       
            else:
                if not is_group:
                    bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
                return update_return_response(req_obj,'junk')  
        else:
            if not is_group:
                bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
            return update_return_response(req_obj,'junk')  
    else:
        logger.info("Webhook :: Not a message.")
        return update_return_response(req_obj,'ignored') 

def getSavePhoto(id):
    file_path = settings.STATIC_ROOT
    img_full_path = os.path.join(file_path, f"image{id}.jpg")

    # Check if the file exists and was modified within the last 5 minutes
    if os.path.exists(img_full_path) and (time.time() - os.path.getmtime(img_full_path)) < 300:
        return img_full_path

    # Call LTA's API to pull all the images required
    acct_key = os.getenv('ACCT_KEY')
    headers = {'AccountKey': acct_key, 'accept': 'application/json'}
    url = os.getenv('TRAFFIC_IMAGES_URL')

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for item in data["value"]:
            if item["CameraID"] in tuas_cameras or item["CameraID"] in causeway_cameras:
                image_url = item["ImageLink"]
                camera_id = item["CameraID"]
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    full_file_name = os.path.join(file_path, f"image{camera_id}.jpg")
                    with open(full_file_name, 'wb') as file:
                        file.write(image_response.content)
    return img_full_path

def sendReplyPhoto(bot, where, chat_id, msg_id, is_group):
    logger.info('Webhook :: Msg: ' + str(where))
    
    if not is_group: 
        bot.sendMessage(chat_id, msg_dict['wait'] + msg_dict['lta_tnc'], parse_mode="HTML")
    
    if where is None:
        bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
        return update_return_response(req_obj, 'junk')
    
    # Determine the camera list based on the checkpoint
    camera_list = causeway_cameras if where == "causeway" else tuas_cameras if where == "tuas" else []

    # Pull all the photos in the media group
    media_group = [
        InputMediaPhoto(media=open(getSavePhoto(camera), 'rb'), caption=caption_dict[camera])
        for camera in camera_list if getSavePhoto(camera)
    ]

    try:
        bot.sendMediaGroup(chat_id, media=media_group, reply_to_message_id=msg_id if not is_group else None)
    except Exception as e:
        logger.error('Failed to send photo: {}'.format(e))
        bot.sendMessage(chat_id, 'Failed to send photo.', reply_to_message_id=msg_id if not is_group else None)

def sendReplyPhotoGroup(bot, chat_id, msg_id, is_group):
    # Notify user if not in a group
    if not is_group: 
        bot.sendMessage(chat_id, msg_dict['wait'] + msg_dict['lta_tnc'], parse_mode="HTML")
    
    # Combine camera lists
    camera_list = causeway_cameras + tuas_cameras
    
    # Pull all the photos in the media group
    media_group = [
        InputMediaPhoto(media=open(getSavePhoto(camera), 'rb'), caption=caption_dict[camera])
        for camera in camera_list if getSavePhoto(camera)
    ]

    try:
        bot.sendMediaGroup(chat_id=chat_id, media=media_group)
    except Exception as e:
        logger.error('Failed to send photo: {}'.format(e))
        bot.sendMessage(chat_id, 'Failed to send photo.', reply_to_message_id=msg_id if not is_group else None)
    
def reloadPhotos(bot, chat_id, msg_id, is_group):
    file_path = os.getenv('STATIC_IMG_PATH')
    msg_to_send = ""
    logger.info('Reload Photos :: Start')
    
    camera_list = None
    
    camera_list = causeway_cameras + tuas_cameras
    
    for camera in camera_list:  # Corrected iteration over items
        img_full_path = os.path.join(file_path, f"image{camera}.jpg")
        
        try:
            if os.path.exists(img_full_path):  # Corrected path check
                os.remove(img_full_path)
                logger.info(f"The file {img_full_path} has been deleted.")
                msg_to_send += 'Removed image' + camera + '.jpg.\n'
            else:
                logger.info(f"The file {img_full_path} does not exist.")
                msg_to_send += 'Not exist image' + camera + '.jpg.\n'
        except Exception as e:
            logger.error(f"Error deleting file {img_full_path}: {e}")
            msg_to_send += f" Error deleting image{camera}.jpg.\n"

    msg_to_send += 'Completed all deletion. Proceed to pull new photos.'
    if not is_group: 
        bot.sendMessage(chat_id, msg_to_send)
    else:
        bot.sendMessage(chat_id, msg_dict['wait'])
    sendReplyPhotoGroup(bot, chat_id, msg_id, is_group)
    logger.info('Reload Photos :: End')
    
def check_requests_rate_and_block(bot, from_id,chat_id):

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

def check_admin(from_id):

    #Time
    now = timezone.now()

    #Whitelist
    whitelist_records = WhitelistTgUser.objects.filter(
        Q(from_id=from_id),
        Q(start_at__lt=now),
        Q(is_admin=True),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )
    if whitelist_records.exists():
        logger.info("Check Admin :: User is Admin :: Userid " + str(from_id))
        return True
    
    return False

def check_whitelist_group(group_id):

    #Time
    now = timezone.now()

    #Whitelist for group
    whitelist_records = WhitelistGroup.objects.filter(
        Q(group_id=group_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )
    if whitelist_records.exists():
        logger.info("Check Whitelist :: Group is whitelisted :: Groupid " + str(group_id))
        return True
    
    return False

def update_return_response(tele_req, resp_code, manual_resp=None):
    # Assuming tele_req is a TelegramRequest object
    if tele_req:
        if manual_resp:
            tele_req.json_response = {"response": str(resp[resp_code]), "bot_queue_resp": manual_resp}
            tele_req.save()  # Save the updated response
        else: 
            tele_req.json_response = {"response": str(resp[resp_code])}
            tele_req.save()  # Save the updated response
    else:
        return {"response": str(resp[resp_code])}
    return tele_req.json_response

def extract_msg(update):
    message  = None
    if "message" in update:
        message = update["message"]
    elif "callback_query" in update:
        is_callback = True
        message = update["callback_query"]["message"]
    else:
        print("Bot :: No Message")
    return message

def extract_chat_text(update):
    chat_text = None
    # If message is available, pull it from message.chat.text, otherwise if it is a callback, then callback.data
    if "message" in update:
        print("Message: " + str(update))
        try:
            chat_text = update["message"]["text"]
        except Exception as e:
            print(chat_text)
            return chat_text
    elif "callback_query" in update:
        try:
            chat_text = update["callback_query"]["data"]
        except Exception as e:
            return chat_text
        print(chat_text)
    else:
        print("Bot :: No Message")
    
    print(chat_text)
    return chat_text

def extract_sender(message):
    sender = None
    from_sender = None
    chat_sender = None
    if message is not None:
        # Try extracting the "from"
        if "from" in message:
            from_sender = message["from"]
            if from_sender["is_bot"]:
                if "chat" in message:
                    if "type" in message["chat"]:
                        if message["chat"]["type"] == "private":
                            chat_sender = message["chat"]
                            return chat_sender
            return from_sender
    return sender

def send_start_reply(bot, chat_id, msg_id, is_group):
    keyboard_buttons = [
                [InlineKeyboardButton(text="🚥 Report Bus & Checkpoint Queue", callback_data='/queuestart')],
                [InlineKeyboardButton(text='🚥 Check Bus & Checkpoint Queue (Web)', callback_data='/dashboard')],
                [InlineKeyboardButton(text='⛅ SG & JB Weather', callback_data='/weather')],
                [InlineKeyboardButton(text="Causeway", callback_data='/causeway'),
                 InlineKeyboardButton(text="Tuas", callback_data='/tuas')],
                [InlineKeyboardButton(text='T&Cs', callback_data='/tnc')],
           ]
    if check_admin(chat_id):
        keyboard_buttons += [[InlineKeyboardButton(text='Admin Functions', callback_data='/start')],
                             [InlineKeyboardButton(text='Show Chkpt Cams', callback_data='/showall'),InlineKeyboardButton(text='Reload Chkpt Cams', callback_data='/reload')],
                             [InlineKeyboardButton(text='Send Chkpt Cams (Grp)', callback_data='/grpcctv'),InlineKeyboardButton(text='Send Weather (Grp)', callback_data='/grpweather')],
                             [InlineKeyboardButton(text='Get Stats', callback_data='/getstats'),InlineKeyboardButton(text='Get CIMB Rate', callback_data='/getrate')],]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    bot.sendMessage(chat_id, msg_dict['start'], reply_markup=keyboard)
    
    
def process_routine_job(request, bot):
    chat_list_str = os.getenv('CHAT_ID', '')
    if not check_whitelist("9999"):
        return update_return_response(None,'batchoff')
    # Split the string into a list by commas
    chat_list = chat_list_str.split(',')
    for chat_id in chat_list:
        sendReplyPhotoGroup(bot, chat_id, '', True)
        
    return update_return_response(None,'ok')

def process_rate_job(request, bot):
    chat_list_str = os.getenv('CHAT_RATE_ID', '')
    if not check_whitelist("9999"):
        return update_return_response(None,'batchoff')
    # Split the string into a list by commas
    chat_list = chat_list_str.split(',')
    for chat_id in chat_list:
        bot.sendMessage(chat_id, "CIMB Rate: " + str(extract_text.get_rate()))
        
    return update_return_response(None,'ok')

def process_weather(request, bot):
    chat_list_str = os.getenv('CHAT_ID', '')
    if not check_whitelist("9999"):
        return update_return_response(None,'batchoff')
    # Split the string into a list by commas
    chat_list = chat_list_str.split(',')
    for chat_id in chat_list:
        bot.sendMessage(chat_id, weather.get_weather(), parse_mode="HTML")
        
    return update_return_response(None,'ok')

def refresh_lta_image_web():
    camera_list = causeway_cameras + tuas_cameras
    
    for camera in camera_list:  # Corrected iteration over items
        getSavePhoto(camera)
        
def get_server_stats():
    stat_str = "Server Stats"
    stat_str += "\nServer: " + os.getenv('ENVIRONMENT')
    # stat_str += "/nStatic Path" +  os.getenv('ENVIRONMENT')
    return stat_str

def get_everything():
    getSavePhoto("2701", True)
    url_str = ""
    return url_str