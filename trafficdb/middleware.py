from django.http import HttpResponseForbidden

class BlockNonLocalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        print(request.META.get('X_REAL_IP'))
        # Block users who are not from the local host
        #if not request.META.get('X_REAL_IP') == '127.0.0.1':
        #    return HttpResponseForbidden()

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
