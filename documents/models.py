from django.db import models


class Document(models.Model):
    FILE_TYPES = ('md', 'txt')

    repo = models.ForeignKey('interface.Repo', related_name='documents')
    path = models.TextField()
    filename = models.TextField()
    body = models.TextField(blank=True)
    commit_date = models.DateTimeField()

    def __str__(self):
        return '{}{}'.format(self.path, self.filename)

    class Meta:
        unique_together = ('repo', 'path', 'filename')
