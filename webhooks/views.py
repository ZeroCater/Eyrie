from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from interface.models import Repo

from webhooks.models import GithubHook, GithubHookError, GithubHookAccessError, GithubHookContentError


@csrf_exempt
def github_webhook(request):
    github_hook = GithubHook(request)

    try:
        github_hook.process_request()
    except GithubHookAccessError:
        return HttpResponse(status=403)
    except GithubHookContentError:
        return HttpResponse(status=204)
    except GithubHookError as e:
        return HttpResponse(str(e), status=400)

    repo = Repo.objects.filter(full_name=github_hook.repository['full_name']).first()

    if not repo:
        return HttpResponse(status=204)

    # Ignore non-wiki branches
    if github_hook.branch_name != repo.wiki_branch:
        return HttpResponse(status=204)

    # Update repo privacy, if changed
    if repo.is_private != github_hook.repository['private']:
        repo.is_private = github_hook.repository['private']
        repo.save()

    file_change_data = github_hook.file_change_data
    repo.enqueue(file_change_data)

    return HttpResponse(status=202)
