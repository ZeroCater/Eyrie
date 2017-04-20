from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from documents.models import Document
from interface.models import Repo, UserProxy


class RepoTestCase(TestCase):
    def setUp(self):
        self.user = UserProxy.objects.create(username='test')
        self.repo = Repo.objects.create(full_name='test/test', user=self.user)

    @patch('interface.models.Repo.remove_webhook')
    def test_delete(self, mock_delete):
        url = reverse('repo_delete', kwargs={'full_name': self.repo.full_name})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Repo.objects.count(), 1)
        self.client.force_login(self.user, backend='social.backends.github.GithubOAuth2')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Repo.objects.count(), 0)

    def test_search(self):
        now = timezone.now()
        doc1 = Document.objects.create(
            repo=self.repo, path='/test/dir', filename='test.md', commit_date=now, body='This is a test'
        )
        doc2 = Document.objects.create(
            repo=self.repo, path='/test/dir', filename='fail.md', commit_date=now, body='This is a fail'
        )
        doc3 = Document.objects.create(
            repo=self.repo, path='/test/dir', filename='different.md', commit_date=now, body='This is also a test'
        )

        search_results = self.repo.search_documents('test')
        self.assertEqual(search_results.count(), 2)
        self.assertNotIn(doc2, search_results, 'Search results included fail Document')
        # Check filename sorted first
        self.assertEqual(search_results.first(), doc1, 'Filename matches should be sorted first')
        self.assertEqual(search_results.last(), doc3, 'Filename matches should be sorted first')
