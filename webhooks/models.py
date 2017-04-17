import hashlib
import hmac
import json

from django.conf import settings


class GithubHookError(Exception):
    pass


class GithubHookAccessError(GithubHookError):
    pass


class GithubHookContentError(GithubHookError):
    pass


REQUIRED_KEYS = ['ref', 'before', 'commits']


class GithubHook(object):

    def __init__(self, request):
        self.request = request
        self.body = None

    def process_request(self):
        self.validate_header()
        self.process_body()
        self.validate_keys()
        self.generate_properties()

    @property
    def branch_name(self):
        return self.ref.replace('refs/heads/', '')

    def validate_header(self):
        if 'HTTP_X_HUB_SIGNATURE' not in self.request.META:
            raise GithubHookAccessError('Wrong signature')

        sig = self.request.META['HTTP_X_HUB_SIGNATURE']
        text = self.request.body

        secret = str.encode(settings.WEBHOOK_SECRET)
        signature = 'sha1=' + hmac.new(secret, msg=text, digestmod=hashlib.sha1).hexdigest()

        if not hmac.compare_digest(sig, signature):
            raise GithubHookAccessError('Signature does not match')

    def validate_keys(self):
        if not all(key in self.body for key in REQUIRED_KEYS):
            raise GithubHookContentError("Incomplete data")

    def generate_properties(self):
        for key, value in self.body.items():
            setattr(self, key, value)

    def process_body(self):
        try:
            self.body = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            raise GithubHookError("Invalid body format")

    @property
    def file_change_data(self):
        modified = []
        removed = []
        for commit in self.commits:
            modified += commit.get('modified', []) + commit.get('added', [])
            removed += commit.get('removed', [])

        removed = ["/{}".format(path) for path in removed]
        modified = ["/{}".format(path) for path in modified]
        return {'removed': removed, 'modified': modified}
