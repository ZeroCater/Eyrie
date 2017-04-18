from django.db import models
from django.urls import reverse


class Document(models.Model):
    FILE_TYPES = ('md', 'txt')

    repo = models.ForeignKey('interface.Repo', related_name='documents')
    path = models.TextField()
    filename = models.TextField()
    body = models.TextField(blank=True)
    commit_date = models.DateTimeField()

    def __str__(self):
        return '{}/{}'.format(self.path, self.filename)

    @property
    def github_view_link(self):
        return 'https://github.com/{0}/blob/{1}{2}'.format(self.repo.full_name, self.repo.wiki_branch, str(self))

    @property
    def github_edit_link(self):
        return 'https://github.com/{0}/edit/{1}{2}'.format(self.repo.full_name, self.repo.wiki_branch, str(self))

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'full_name': self.repo.full_name, 'path': str(self)})

    class Meta:
        unique_together = ('repo', 'path', 'filename')
