from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from interface.models import Repo

from webhooks.models import GitHook, GitHookError, GitHookAccessError


@csrf_exempt
def github_webhook(request):
    git_hook = GitHook(request)

    try:
        git_hook.process_request()
    except GitHookAccessError:
        return HttpResponse(status=403)
    except GitHookError as e:
        return HttpResponse(str(e), status=400)

    repo = Repo.objects.filter(full_name=git_hook.repository['full_name']).first()

    if not repo:
        return HttpResponse(status=204)

    # Ignore non-wiki branches
    if git_hook.branch_name != repo.wiki_branch:
        return HttpResponse(status=204)

    # Update repo privacy, if changed
    if repo.is_private != git_hook.repository['private']:
        repo.is_private = git_hook.repository['private']
        repo.save()

    repo.enqueue()

    return HttpResponse(status=202)
