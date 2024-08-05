from .models import *
import re
from telepot.namedtuple import *
from django.db.models import Q

msg_dict = {
    "junk" : "Don't send me junk!",
    "blacklist" : "Slow mode: I know you are eager to help, but my resources are limited. Sorry that I need to put you on hold. Talk to you later!",
    }

def handle_command(bot, sender, user_id, chat_id, command, param, update_id, is_group):
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
        bot.sendMessage(chat_id, "Which direction do you wish to update?", reply_markup=keyboard)
    else:
        return "Nothing available for you to update."
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
            bot.sendMessage(chat_id, "Which queue do you wish to update?", reply_markup=keyboard)
        else:
            bot.sendMessage(chat_id, "No such queue. Is it in your dreams?")
    else:
        return "Incorrect parameters. Request ignored."
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
                return "No queue configured."
        else:
            return "No such queue. Is it in your dreams?"
    else:
        return "Incorrect parameters. Request ignored."
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
                bot.sendMessage(chat_id, "Updated for queue {}. Thank you for your feedback.".format(queues[0].queueName))
            except Exception as e:
                return "Error with Queue Update."
        else:
            return "Wrong Params"
    else:
        return "Wrong Params"
    return "Completed request."

def validate_params(params, num_params):
    test_pattern = r"^\d+(?: \d+)*$"
    matches = re.match(test_pattern, params)
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