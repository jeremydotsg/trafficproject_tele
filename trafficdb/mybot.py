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

load_dotenv()
logger = logging.getLogger('trafficdb')
bot = None
bot_name = os.getenv('BOT_NAME', '')
# Change here for any settings
photo_dict = {
    "causeway1": "2701",
    "causeway2": "2702",
    "tuas1": "4703",
    "tuas2": "4713"
    }

caption_dict = {
    "causeway1": "Wdls Causeway Camera",
    "causeway2": "Wdls Checkpoint Camera",
    "tuas1": "Tuas 2nd Link Camera",
    "tuas2": "Tuas Checkpoint Camera"
    }
msg_dict = {
    "start" : "Hello!\nI am here to provide you useful information for your SG Cross Border Travel. You may press the buttons below or see the commands from the menu. By using this Bot, you agree to the Terms and Conditions available at /tnc.",
    "hello" : "Everything is fine.",
    "junk" : "Don't send me junk!",
    "notallowed" : "Not allowed to use this command!",
    "dashboard" : "Check out the dashboard. https://t.me/CT_IMG_BOT/dashboard",
    "blacklist" : "Slow mode: Hey, you have found a hidden feature!. Others need my help too, so I need to put you on hold. Talk to you later!",
    "wait" : "Wait a moment...",
    "lta_tnc" : "\nNote: This bot uses the LTA's Traffic Images dataset accessed at the time of request and made available under the terms of the <a href=\"https://datamall.lta.gov.sg/content/datamall/en/SingaporeOpenDataLicence.html\">Singapore Open Data Licence version 1.0</a>.",
    "streamnote" : "Note: The bot owners are not associated with the channels in the links.\nThe links are provided for informational purposes only. We do not guarantee accuracy, completeness, or suitability and do not accept any liabilities over the use of the information.\n\nBy proceeding, you accept the risks and do not hold us liable for anything arises from the use of the information.",
    "beta"  : "Beta mode: Currently in limited beta mode. Watch out when this bot is available.",
    "tnc" : "<b>Terms & Conditions</b>\nBy interacting with this Bot, you agree to the <a href=\"https://mygowhere.pythonanywhere.com/trafficdb/disclaimer\">disclaimer published here</a>.\n"
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
    'ok' : 'Ok, request processed.'
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
            elif command in ['causeway1','causeway2','tuas1','tuas2']:
                sendReplyPhoto(bot, command,chat_id,msg_id, is_group)
                return update_return_response(req_obj,'ok')            
            # Whitelist users (and groups) only commands
            elif command in ['reload','showall']:
                if check_whitelist(user_id):
                    if command in ['showall']:
                        sendReplyPhotoGroup(bot, chat_id, msg_id, is_group)
                        return update_return_response(req_obj,'ok')  
                    elif command == 'reload':
                        reloadPhotos(bot, chat_id, msg_id, is_group)
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

def sendReplyPhoto(bot, where, chat_id, msg_id, is_group):
    logger.info('Webhook :: Msg: ' + str(where))
    if not is_group: 
        bot.sendMessage(chat_id, msg_dict['wait'] + msg_dict['lta_tnc'], parse_mode="HTML")
    if where is None:
        bot.sendMessage(chat_id, msg_dict['junk'], reply_to_message_id=msg_id)
        return update_return_response(req_obj,'junk')
    else:
        #Call API and get URL
        photo_url=getSavePhoto(photo_dict[where])
        logger.info('Webhook :: Path: ' + str(photo_url))
        try:
            if not is_group: 
                bot.sendPhoto(chat_id, open(photo_url,'rb'), caption=caption_dict[where], reply_to_message_id=msg_id)
            else:
                bot.sendPhoto(chat_id, open(photo_url,'rb'), caption=caption_dict[where])
        except Exception as e:
            logger.error('Failed to send photo: {}'.format(e))
            if not is_group:
                bot.sendMessage(chat_id,'Failed to send photo.', reply_to_message_id=msg_id)
            else:
                bot.sendMessage(chat_id,'Failed to send photo.')

def sendReplyPhotoGroup(bot, chat_id, msg_id, is_group):
    # Get photo from LTA or local
    if not is_group: 
        bot.sendMessage(chat_id, msg_dict['wait'] + msg_dict['lta_tnc'], parse_mode="HTML")
    media_group = []
    for key, value in photo_dict.items():
        input_media = None
        photo_url = getSavePhoto(value)
        if photo_url:
            logger.info('Photo Path :: ' + str(photo_url))
            input_media = InputMediaPhoto(media=open(photo_url,'rb'),caption=caption_dict[key])
            media_group.append(input_media)
    if is_group:
        bot.sendMediaGroup(chat_id=chat_id, media=media_group)
    else:
        bot.sendMediaGroup(chat_id=chat_id, media=media_group, reply_to_message_id=msg_id)
    
def reloadPhotos(bot, chat_id, msg_id, is_group):
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
    if not is_group: 
        bot.sendMessage(chat_id, msg_to_send, reply_to_message_id=msg_id)
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
    if manual_resp:
        tele_req.json_response = {"response": str(resp[resp_code]), "bot_queue_resp": manual_resp}
        tele_req.save()  # Save the updated response
    else: 
        tele_req.json_response = {"response": str(resp[resp_code])}
        tele_req.save()  # Save the updated response
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='Terms and Conditions', callback_data='/tnc'),
               InlineKeyboardButton(text='Check or Update Queue', callback_data='/dashboard')],
               [InlineKeyboardButton(text=caption_dict['causeway1'], callback_data='/causeway1'),
               InlineKeyboardButton(text=caption_dict['causeway2'], callback_data='/causeway2')],
               [InlineKeyboardButton(text=caption_dict['tuas1'], callback_data='/tuas1'),
               InlineKeyboardButton(text=caption_dict['tuas2'], callback_data='/tuas2')],
               [InlineKeyboardButton(text='SG and JB Weather', callback_data='/weather')]
           ])
    bot.sendMessage(chat_id, msg_dict['start'], reply_markup=keyboard)