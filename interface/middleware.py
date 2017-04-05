from interface.models import UserProxy


class UserProxyMiddleware(object):
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated():
            request.user.__class__ = UserProxy
