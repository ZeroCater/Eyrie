import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from interface.models import Repo


@csrf_exempt
def WebhookView(request):
    if 'HTTP_X_HUB_SIGNATURE' not in request.META:
        return HttpResponse(status=403)

    sig = request.META['HTTP_X_HUB_SIGNATURE']
    text = request.body

    secret = str.encode(settings.WEBHOOK_SECRET)
    signature = 'sha1=' + hmac.new(secret, msg=text, digestmod=hashlib.sha1).hexdigest()

    if not hmac.compare_digest(sig, signature):
        return HttpResponse(status=403)

    try:
        body = json.loads(text.decode('utf-8'))
        assert body
    except ValueError:
        return HttpResponse('Invalid JSON body.', status=400)

    try:
        repo = Repo.objects.get(full_name=body['repository']['full_name'])
    except Repo.DoesNotExist:
        return 'Repo not registered'

    if 'ref' not in body or not body['head_commit'] or \
            body['ref'].rsplit('/', maxsplit=1)[1] != repo.wiki_branch:  # Ignore non-wiki branches
        return HttpResponse(status=204)

    # Update repo privacy, if changed
    if repo.is_private != body['repository']['private']:
        repo.is_private = body['repository']['private']
        repo.save()

    auth = repo.user.get_auth()
    if not auth:
        return 'User for repo not logged in'

    repo.enqueue(auth)

    return HttpResponse(status=202)
