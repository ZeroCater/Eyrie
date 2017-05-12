import hashlib
import hmac
import json
import re

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from github import UnknownObjectException, BadCredentialsException
from social.apps.django_app.default.models import UserSocialAuth

from documents.models import Document
from documents.search import Search
from interface.models import Repo
from interface.utils import get_github
from interface.path_processor import PathProcessor


class RepoDetailView(generic.DetailView, generic.UpdateView):
    model = Repo
    slug_field = 'full_name'
    slug_url_kwarg = 'full_name'
    template_name = 'interface/repo_detail.html'

    fields = ['wiki_branch']

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        is_collab = self.object.user_is_collaborator(request.user)
        context['is_owner'] = is_collab

        if self.object.is_private and not is_collab:
            raise Http404('You are not allowed to view this Repo')

        repo_name = self.object.full_name

        branches = []
        if is_collab:
            g = get_github(self.object.user)
            grepo = g.get_repo(repo_name)
            branches = [i.name for i in grepo.get_branches()]

        context['branches'] = branches

        path = kwargs.get('path')

        path = path or '/'

        path_processor = PathProcessor(repo_name, path)
        is_directory = False

        try:
            # Viewing a single file
            filename = path_processor.filename
            trunc_path = path_processor.directory
            document = Document.objects.get(repo=self.object, path=trunc_path, filename=filename)
            documents = []
        except Document.DoesNotExist:
            path_processor = PathProcessor(repo_name, path, is_directory=True)
            trunc_path = path_processor.directory
            is_directory = True
            try:
                # Viewing a folder with a README
                document = Document.objects.get(
                    repo=self.object, path=trunc_path, filename__istartswith='README')
            except Document.DoesNotExist:
                # Viewing a folder without a README
                document = None
            documents = Document.objects.filter(repo=self.object, path__startswith=trunc_path)

        context['document'] = document
        context['path'] = path_processor.path_in_repo
        context['files'] = self.object.get_folder_contents(trunc_path, documents)
        context['directory'] = is_directory

        if is_directory and re.match('.+[^/]$', request.path):
            return redirect(request.path + '/')

        if len(context['files']) == 0 and 'document' not in context:
            raise Http404

        context['base_url'] = request.build_absolute_uri(self.object.get_absolute_url())
        b_tuples = []
        if path != '/':
            path = path[1:]
            breadcrumbs = path.split('/')
            for b in breadcrumbs:
                if not b_tuples:
                    url = '{0}/{1}/'.format(context['base_url'], b)
                else:
                    url = '{0}{1}/'.format(b_tuples[-1][0], b)
                b_tuples.append((url, b))

        context['breadcrumbs'] = b_tuples

        return self.render_to_response(context)

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
            full_name__in=[i.full_name for i in repos]
        ).annotate(doc_count=Count('documents'))

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

    def check_and_delete(self, request):
        obj = self.get_object()

        if not obj.user_is_collaborator(request.user):
            raise Http404('You are not allowed to delete this repo')

        obj.delete()

    def get(self, request, *args, **kwargs):
        self.check_and_delete(request)
        return redirect(reverse('repo_list'))

    def delete(self, request, **kwargs):
        self.check_and_delete(request)
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
        repo.is_private = grepo.private
        repo.save()
    except Repo.DoesNotExist:
        repo = Repo.objects.create(
            full_name=grepo.full_name,
            user=user,
            wiki_branch=grepo.default_branch,
            is_private=grepo.private
        )

    if not repo.webhook_id:
        try:
            repo.add_webhook(request)
        except UnknownObjectException:
            raise Http404('Github failed to create a hook')

    repo.enqueue()

    url = reverse('repo_detail', kwargs={'full_name': repo.full_name})
    return redirect(url)


def search_view(request):
    query_text = request.GET.get('q', None)
    if not query_text:
        raise Http404

    search = Search(request.user, query_text)

    docs = search.perform()

    context = {
        'query': query_text,
        'results': docs
    }

    return render(request, 'interface/search.html', context)


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
