from django.http import HttpResponseForbidden
from dotenv import load_dotenv
import requests
import logging
import os

# Load the .env file
load_dotenv()

class BlockNonLocalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger = logging.getLogger('trafficdb_middleware')
     
        #if Prod, proceed check 
        if os.getenv('ENVIRONMENT') == 'prod':
            logger.info('Middleware :: Rule 1 - Path :: ' + str(request.path))
            # Rule 1 - Bypass check if the requested path is "/trafficdb/webhook/"
            if request.path == "/trafficdb/webhook/":
                logger.info('Middleware :: Rule 1 - Path :: Bypassed for path webhook')
                return self.get_response(request)
            # Rule 2 - Get the client's IP address
            ip = None
            full_url = None
            if request:
                full_url = request.get_full_path()
                real_ip = request.META.get("X_REAL_IP", "")
                remote_ip = request.META.get("REMOTE_ADDR", "")
                forwarded_ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
                logger.info('Middleware :: Rule 2 - Get IP :: Real IP: ' + str(real_ip) + ', Remote IP: ' + str(remote_ip) + ', Forwarded IP: ' + str(forwarded_ip))
                if not real_ip:
                    if not forwarded_ip:
                        ip = remote_ip
                    else:
                        ip = forwarded_ip
                else:
                    ip = real_ip
            # Rule 2a - Bypass whitelisted IP
            # Get the string from the environment variable
            ip_list_str = os.getenv('IP_LIST', '')
            
            # Split the string into a list by commas
            ip_list = ip_list_str.split(',')
            if ip in ip_list:
                logger.info('Middleware :: Rule 2a - Bypass whitelisted IP :: IP ' + str(ip) + ', Whitelisted IP Matched , Path: ' + str(full_url) )
                return self.get_response(request)
                
            #Rule 2b - Allow Singapore/ Malaysia IPs
            # Check the IP's country using an IP geolocation API
            response = requests.get(f'http://ip-api.com/json/{ip}')
            if response.status_code == 200:
                country = response.json().get('country')
                logger.info('Middleware :: Rule 2b - Allow SGMY :: ' + str(ip) + ', Detected Country: ' + str(country) +', Path: ' + str(full_url) )
                if country not in ['Singapore','Malaysia']:
                    logger.info('Middleware :: Rule 2b - Allow SGMY :: ' + str(ip) + ', Denied Country: ' + str(country) +', Path: ' + str(full_url) )
                    return HttpResponseForbidden('<h1>Access Denied.</h1>')
            # If the IP is from Singapore or Malaysia, or if the API call failed, continue processing
            return self.get_response(request)
        else:
            #Other envs turn off the check.
            return self.get_response(request)