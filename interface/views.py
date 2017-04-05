import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from github import UnknownObjectException, BadCredentialsException
from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.views import auth

from interface.mixins import StaffRequiredMixin
from interface.models import Build, Repo, Result, UserProxy
from interface.utils import get_github, get_page_number_list


class BuildDetailView(generic.DetailView):
    model = Build

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['repo'] = self.object.repo
        is_collab = context['repo'].user_is_collaborator(request.user)
        context['is_owner'] = is_collab
        issues = self.object.get_issues()
        context['issues'] = issues if issues.totalCount > 0 else False

        if self.object.repo.is_private and not is_collab:
            raise Http404('You are not allowed to view this Build')

        context['results'] = self.object.results.all()

        return self.render_to_response(context)


class RepoDetailView(generic.DetailView, generic.UpdateView):
    model = Repo
    slug_field = 'full_name'
    slug_url_kwarg = 'full_name'
    template_name = 'interface/repo_detail.html'

    fields = ['default_branch']

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        is_collab = self.object.user_is_collaborator(request.user)
        context['is_owner'] = is_collab

        if self.object.is_private and not is_collab:
            raise Http404('You are not allowed to view this Repo')

        if is_collab:
            url = reverse('badge', kwargs={'full_name': self.object.full_name})
            context['absolute_url'] = self.request.build_absolute_uri(self.request.path)
            context['badge_url'] = self.request.build_absolute_uri(url)
            g = get_github(self.object.user)
            grepo = g.get_repo(self.object.full_name)
            context['branches'] = [i.name for i in grepo.get_branches()]

        ref = request.GET.get('ref', False)
        context['ref'] = ref
        if ref:
            build_results = Build.objects.filter(repo=self.object, ref=ref)
        else:
            build_results = Build.objects.filter(repo=self.object)
        paginator = Paginator(build_results, 20)

        page = self.request.GET.get('page')
        try:
            context['builds'] = paginator.page(page)
        except PageNotAnInteger:
            context['builds'] = paginator.page(1)
        except EmptyPage:
            context['builds'] = paginator.page(paginator.num_pages)

        if paginator.num_pages > 1:
            context['pages'] = get_page_number_list(context['builds'].number, paginator.num_pages)

        context['num_objects'] = paginator.count

        return self.render_to_response(context)

    def form_valid(self, form):
        self.object = self.get_object()
        redirect = super(RepoDetailView, self).form_valid(form)
        statuses = self.request.POST.get('statuses', False)
        if statuses == 'on' and not self.object.webhook_id:
            self.object.add_webhook(self.request)
        elif not statuses and self.object.webhook_id:
            self.object.remove_webhook()
        return redirect

    def form_invalid(self, form):
        # TODO: Submit form via ajax, show error message if invalid
        # I have no idea how someone would submit an invalid form
        return render(self.request, 'interface/500.html')


class RepoListView(LoginRequiredMixin, generic.ListView):
    template_name = 'interface/repo_list.html'

    def get(self, request, *args, **kwargs):
        g = get_github(self.request.user)
        try:
            repos = [r for r in g.get_user().get_repos()]
        except BadCredentialsException:
            UserSocialAuth.objects.filter(user=request.user).delete()
            return redirect(reverse('social:begin', args=['github'])) + '?next=' + request.path

        self.object_list = Repo.objects.filter(
            full_name__in=[i.full_name for i in repos],
            disabled=False
        ).annotate(builds_count=Count('builds'))

        names = [x.full_name for x in self.object_list]

        filtered = []
        for repo in repos:
            if repo.full_name not in names:
                filtered.append(repo)

        context = self.get_context_data()
        context['repos'] = filtered

        context['welcome'] = request.GET.get('welcome', False)

        return self.render_to_response(context)


class RepoDeleteView(generic.DetailView):
    model = Repo
    slug_field = 'full_name'
    slug_url_kwarg = 'full_name'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(RepoDeleteView, self).dispatch(request, *args, **kwargs)

    def soft_delete(self, request):
        obj = self.get_object()

        if not obj.user_is_collaborator(request.user):
            raise Http404('You are not allowed to delete this repo')

        obj.soft_delete()

    def get(self, request, *args, **kwargs):
        self.soft_delete(request)
        return redirect(reverse('repo_list'))

    def delete(self, request, *args, **kwargs):
        self.soft_delete(request)
        return HttpResponse(status=204)


@login_required
def ProcessRepo(request, full_name):
    user = request.user
    g = get_github(request.user)
    grepo = g.get_repo(full_name)

    if not grepo.full_name:
        raise Http404('Repo not found')

    guser = g.get_user(user.username)
    is_collab = grepo.has_in_collaborators(guser)

    if not is_collab and grepo.private:
        raise Http404('You are not a collaborator of this repo')

    try:
        repo = Repo.objects.get(full_name=grepo.full_name)
        repo.disabled = False
        repo.is_private = grepo.private
        repo.save()
    except Repo.DoesNotExist:
        repo = Repo.objects.create(
            full_name=grepo.full_name,
            user=user,
            default_branch=grepo.default_branch,
            is_private=grepo.private
        )

    if not repo.webhook_id:
        try:
            repo.add_webhook(request)
        except UnknownObjectException:
            raise Http404('Github failed to create a hook')

    # Lint all open branches
    auth = request.user.get_auth()

    for branch in grepo.get_branches():
        build, created = Build.objects.get_or_create(
            repo=repo,
            ref=branch.name,
            sha=branch.commit.sha
        )
        if created:
            build.enqueue(auth)

    url = reverse('repo_detail', kwargs={'full_name': repo.full_name})
    return redirect(url)


@login_required
def Rebuild(request, pk):
    try:
        build = Build.objects.get(id=pk)
    except Build.DoesNotExist:
        raise Http404('Build does not exist')

    if not request.user.is_staff:
        g = get_github(request.user)
        grepo = g.get_repo(build.repo.full_name)

        if not grepo.full_name:
            raise Http404('Repo not found')

        guser = g.get_user(request.user.username)
        is_collab = grepo.has_in_collaborators(guser)

        if not is_collab:
            raise Http404('You are not a collaborator of this repo')

    Result.objects.filter(build=build).delete()

    auth = request.user.get_auth()
    build.enqueue(auth)

    return redirect(reverse('build_detail', kwargs={'pk': build.id}))


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

    if 'ref' not in body or not body['head_commit']:
        return HttpResponse(status=204)

    try:
        repo = Repo.objects.get(full_name=body['repository']['full_name'])
    except Repo.DoesNotExist:
        return 'Repo not registered'

    # Update repo privacy, if changed
    if repo.is_private != body['repository']['private']:
        repo.is_private = body['repository']['private']
        repo.save()

    auth = repo.user.get_auth()
    if not auth:
        return 'User for repo not logged in'

    sha = body['head_commit']['id']
    try:
        build = Build.objects.get(sha=sha)
    except:
        branch = body['ref'].replace('refs/heads/', '')
        build = Build.objects.create(
            repo=repo,
            ref=branch,
            sha=sha
        )

    build.enqueue(auth)

    return HttpResponse(status=202)


def LogoutView(request):
    next = request.GET.get('next', '/')
    logout(request)
    return redirect(next)


def handler404(request):
    response = render(request, 'interface/404.html')
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, 'interface/500.html')
    response.status_code = 500
    return response
