from .models import *
from dotenv import load_dotenv
from datetime import timedelta
from django.utils import timezone
from telepot.namedtuple import *
from django.db.models import Q, Avg

import os
import re

load_dotenv()

msg_dict = {
    "junk" : "I am here to help, don't send me junk please!",
    "blacklist" : "🐢 Slow mode: I know you are eager to help, but my resources are limited. Sorry that I need to put you on hold. Talk to you later!",
    }

def handle_command(bot, user_id, chat_id, command, param, update_id, is_group):
    print("Handle Command: " + command)
    print("Handle Params: " + param)
    msg = ""
    if log_command(update_id, chat_id, command, param):
        if check_rate_limit(bot, chat_id):
            return "Blacklist"
        if command == "queuestart":
            return handle_get_dir(bot, chat_id)
        # /queueb <dirid>
        elif command.startswith("queueb"):
            return handle_get_dir_queue(bot, chat_id, param)
        # /queuec <queueid>
        elif command.startswith("queuec"):
            return handle_get_queue(bot, chat_id, param)
        # /queued <queueid> <status>
        elif command.startswith("queued"):
            return handle_get_update_queue(bot, chat_id, param)
    else:
        return "Processing Failed."
    return msg

def handle_get_dir(bot, chat_id):
    directions = get_direction_list()
    buttons = []
    if directions:
        for direction in directions:
            buttons.append([InlineKeyboardButton(text=direction.directionName, callback_data='/queueb '+ str(direction.id))])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        bot.sendMessage(chat_id, "🔄 Which direction do you wish to update?", reply_markup=keyboard)
    else:
        return "❌ Nothing available for you to update."
    return "Completed request."

def handle_get_dir_queue(bot, chat_id, param):
    params = validate_params(param, 1)
    if params:
        queues = Queue.objects.filter(direction_id=params[0]).order_by('-queueType__queueTypeDisplayOrder')
        buttons = []
        if queues:
            for queue in queues:
                if "gate" in queue.queueName.lower():
                    emoji = "🚪"
                else:
                    emoji = "🚌"
                buttons.append([InlineKeyboardButton(text=f"{emoji} {queue.queueName}", callback_data='/queuec ' + str(queue.id))])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            bot.sendMessage(chat_id, "🫂 Which queue do you wish to update?", reply_markup=keyboard)
        else:
            bot.sendMessage(chat_id, "❌ No such queue. Is it in your dreams?")
    else:
        return "❌ Incorrect parameters. Request ignored."
    return "Completed request."

def handle_get_queue(bot, chat_id, param):
    params = validate_params(param, 1)
    if params:
        queues = Queue.objects.filter(id=params[0])
        if queues:
            queueLengths = QueueLength.objects.filter(queueTypeDisplay=True).order_by('id')
            buttons = []
            if queueLengths:
                for queueLength in queueLengths:
                    buttons.append([InlineKeyboardButton(text=queueLength.queueLength, callback_data='/queued '+ str(params[0]) + ' ' + str(queueLength.id))])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                bot.sendMessage(chat_id, "🚥 How packed is the {} queue?".format(queues[0].queueName), reply_markup=keyboard)
            else:
                return "❌ No queue configured."
        else:
            return "❌ No such queue. Is it in your dreams?"
    else:
        return "❌ Incorrect parameters. Request ignored."
    return "Completed request."

def handle_get_update_queue(bot, chat_id, param):
    params = validate_params(param, 2)
    if params:
        queues = Queue.objects.filter(id=params[0])
        queuelengths = QueueLength.objects.filter(id=params[1])
        if queues and queuelengths:
            try:
                QueueStatus.objects.create(
                    queue = queues[0],
                    queueLength = queuelengths[0],
                    queueUserId = chat_id                
                    )
                bot.sendMessage(chat_id, "✅ Updated for queue {}.\n\nThank you for your feedback.".format(queues[0].queueName))
            except Exception as e:
                return "❌ Error with Queue Update."
        else:
            return "❌ Wrong Params"
    else:
        return "❌ Wrong Params"
    return "Completed request."

def validate_params(params, num_params):
    print("Test for pattern :: " + params)
    test_pattern = r"^\d+(?: \d+)*$"
    matches = re.match(test_pattern, params)
    print(matches)
    non_num_pattern = r"/[^\d\s]*$/gm"
    matches_non_num = re.match(non_num_pattern,params)
    if matches_non_num:
        print("Matches non num")
        return None
    if matches:
        params_list = params.split(" ")
        print(params_list)
        if len(params_list) != num_params:
            return None
        else:
            return params_list
    return None

def get_direction_list():
    return Direction.objects.filter(directionDisplay=True)

def log_command(update_id, chat_id, command, param):
    try:
        TgQueueUpdate.objects.create(
            update_id=update_id,
            user_id=chat_id,
            command=command,
            parameters=param)
    except Exception as e:
        print(e)
        return False
    
    return True

def check_rate_limit(bot, chat_id):
    # True for rate_limit, false for no rate limit
    # Time
    print("In rate limit.")
    now = timezone.now()
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    
    #Whitelist
    whitelist_records = WhitelistTgUser.objects.filter(
        Q(from_id=chat_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )
    if whitelist_records.exists():
        print("whitelist")
        return False
    # else:
    #     return True
    blocked_records = BlockedTgUser.objects.filter(
        Q(from_id=chat_id),
        Q(start_at__lt=now),
        Q(end_at__isnull=True) | Q(end_at__gt=now)
    )

    # Check if user is already blocked
    # Check if any records exist
    if blocked_records.exists():
        print("blocklist")
        return True
    
    requests_five_minute = TgQueueUpdate.objects.filter(
        user_id=chat_id,
        created_at__gte=five_minutes_ago
    ).count()
    print(requests_five_minute)
    
    if requests_five_minute >= 25:
        BlockedTgUser.objects.create(from_id=chat_id)
        bot.sendMessage(chat_id, msg_dict['blacklist'])
        print("Rate limited.")
        print("Queue Bot :: Rate Check: Blacklisting user " + str(chat_id))
        return True
    
    return False



def get_queue(html=False):
    direction_pack = []
    # Get the current time
    current_time = timezone.now()
    # Calculate the time one hour ago from the current time
    one_hour_ago = current_time - timedelta(minutes=60)

    # Get the number of directions
    for each_direction in Direction.objects.filter(directionDisplay=True).order_by('id').all():
        direction_info = f"<strong>🧭 Direction: {each_direction.directionName}</strong>\n"
        queue_type_pack = []
        # Get the queue types
        for each_queue_type in QueueType.objects.filter(queueTypeDisplay=True).order_by('-queueTypeDisplayOrder').all():
            queue_type_info = f"  <strong>{each_queue_type.queueTypeName}</strong>\n"
            queue_pack = []
            # Get the queues
            for each_queue in Queue.objects.filter(direction=each_direction, queueType=each_queue_type).all():
                # Subquery to get the latest createdTime for each queue
                queue_statuses = QueueStatus.objects.filter(queue=each_queue, createdTime__gte=one_hour_ago).select_related('queue', 'queueLength').all()
                # Calculate the average queueLengthValue for each Queue
                average_queue_lengths = queue_statuses.values('queue__queueName').annotate(averageLength=Avg('queueLength__queueLengthValue')).all()
                # Main query to get the latest queueLength for each queue
                # if not average_queue_lengths:
                #     queue_info = f"    {'🚪' if 'gate' in each_queue.queueName.lower() else '🚌'} {each_queue.queueName}: - \n"
                queue_info = ''
                if average_queue_lengths:
                    for queue_status in average_queue_lengths:
                        avg_length = queue_status['averageLength']
                        if avg_length < 1:
                            emoji = '🟢🟢'
                        elif avg_length <= 2:
                            emoji = '🟢🟡'
                        elif avg_length <= 3:
                            emoji = '🟡🟡'
                        elif avg_length <= 4:
                            emoji = '🟡🔴'
                        else:
                            emoji = '🔴🔴'
                        queue_info = f"    {'🚪' if 'gate' in each_queue.queueName.lower() else '🚌'} {each_queue.queueName}: {emoji}\n"
                        queue_pack.append(queue_info)
            if queue_pack:
                queue_type_pack.append('' + queue_type_info + '' + ''.join(queue_pack))
        if queue_type_pack:
            direction_pack.append("" + direction_info + "".join(queue_type_pack)) 
        else:
            direction_pack.append("" + direction_info + "No reports.\n")
                
    result = " ".join(direction_pack)
    result += "\n\n*Queue conditions reported within the past hour. \n*Report queue @" + os.getenv('BOT_NAME') + "."
    if html:
        result = result.replace("\n", "<br />")
    return result

