from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from github import UnknownObjectException
from social.apps.django_app.default.models import UserSocialAuth

from documents.tasks.wiki_processor import process_wiki
from interface.utils import get_github
from interface.path_processor import PathProcessor


class UserProxy(User):

    class Meta:
        proxy = True

    def get_auth(self):
        try:
            data = UserSocialAuth.objects.filter(user=self).values_list('extra_data')[0][0]
        except:
            return None

        username = data['login']
        password = data['access_token']
        return (username, password)


class Repo(models.Model):
    user = models.ForeignKey(UserProxy, related_name='repos')
    full_name = models.TextField(unique=True)
    webhook_id = models.IntegerField(null=True, blank=True)
    is_private = models.BooleanField(default=True)

    wiki_branch = models.TextField(default='master')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'full_name': self.full_name})

    @property
    def clone_url(self):
        return 'https://github.com/{}.git'.format(self.full_name)

    def delete(self, *args, **kwargs):
        self.remove_webhook()
        return super(Repo, self).delete(*args, **kwargs)

    def remove_webhook(self):
        if not settings.DEBUG:
            g = get_github(self.user)
            grepo = g.get_repo(self.full_name)

            try:
                hook = grepo.get_hook(self.webhook_id)
                hook.delete()
            except UnknownObjectException:
                pass

        self.webhook_id = None
        self.save()

    def user_is_collaborator(self, user):
        if not user.is_authenticated():
            return False
        if self.user == user or user.is_staff:
            return True
        g = get_github(user)
        grepo = g.get_repo(self.full_name)
        guser = g.get_user(user.username)
        return grepo.has_in_collaborators(guser)

    def add_webhook(self, request):
        if settings.DEBUG:
            self.webhook_id = 123
        else:
            g = get_github(self.user)
            grepo = g.get_repo(self.full_name)

            hook = grepo.create_hook(
                'web',
                {
                    'content_type': 'json',
                    'url': request.build_absolute_uri(reverse('hooksgithub')),
                    'secret': settings.WEBHOOK_SECRET
                },
                events=['push'],
                active=True
            )
            self.webhook_id = hook.id

        self.save()

    @property
    def directory(self):
        path_processor = PathProcessor(self.full_name, is_directory=True)
        return path_processor.repo_disk_path

    def enqueue(self, file_change=None):
        file_change = file_change or {}
        process_wiki.delay(self.id, file_change)

    def get_folder_contents(self, path, documents):
        folders = []
        docs = []

        for document in documents:
            doc_path = document.path
            if path != '/':
                doc_path = doc_path.replace(path, '')
                if not doc_path.startswith('/'):
                    doc_path = '/{}'.format(doc_path)
            if doc_path == '/':
                docs.append(document.filename)
            else:
                first_seg = doc_path.split('/', maxsplit=2)[1]
                if first_seg:
                    folder_name = '{}/'.format(first_seg)
                    if folder_name not in folders:
                        folders.append(folder_name)

        folders = sorted(folders)
        docs = sorted(docs)
        folders.extend(docs)

        return folders
