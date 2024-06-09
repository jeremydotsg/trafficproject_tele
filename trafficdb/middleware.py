from django.http import HttpResponseForbidden
import requests

class BlockNonLocalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the client's IP address
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
        
        # Check the IP's country using an IP geolocation API
        print(ip)
        response = requests.get(f'http://ip-api.com/json/{ip}')
        if response.status_code == 200:
            country = response.json().get('country')
            print(country)
            if country not in ['Singapore','Malaysia']:
                return HttpResponseForbidden('<h1>Access Denied</h1>')
        
        # If the IP is from Singapore or Malaysia, or if the API call failed, continue processing
        return self.get_response(request)