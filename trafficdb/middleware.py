from django.http import HttpResponseForbidden
import requests
import logging

class BlockNonLocalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        logger = logging.getLogger('trafficdb_middleware')
        # Get the client's IP address
        ip = None
        full_url = None
        if request:
            full_url = request.get_full_path()
            real_ip = request.META.get("X_REAL_IP", "")
            remote_ip = request.META.get("REMOTE_ADDR", "")
            forwarded_ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
            logger.info('Middleware - Real IP: ' + str(real_ip) + ', Remote IP: ' + str(remote_ip) + ', Forwarded IP: ' + str(forwarded_ip))
            if not real_ip:
                if not forwarded_ip:
                    ip = remote_ip
                else:
                    ip = forwarded_ip
            else:
                ip = real_ip
        # Add in cron-job IP and localhost
        ip_list = ["116.203.129.16", "116.203.134.67", "23.88.105.37", "128.140.8.200", "127.0.0.1"]
        if ip in ip_list:
            logger.info('Middleware - IP: ' + str(ip) + ', Matched IP_LIST & Skipped , Path: ' + str(full_url) )
            return self.get_response(request)
        
        # Check the IP's country using an IP geolocation API
        response = requests.get(f'http://ip-api.com/json/{ip}')
        if response.status_code == 200:
            country = response.json().get('country')
            logger.info('Middleware - IP: ' + str(ip) + ', Country: ' + str(country) +', Path: ' + str(full_url) )
            if country not in ['Singapore','Malaysia']:
                return HttpResponseForbidden('<h1>Access Denied</h1>')
        
        # If the IP is from Singapore or Malaysia, or if the API call failed, continue processing
        return self.get_response(request)