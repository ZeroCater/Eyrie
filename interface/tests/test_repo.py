from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from model_mommy import mommy

from interface.models import Repo


class RepoTestCase(TestCase):

    def setUp(self):
        self.user = mommy.make_recipe('eyrie.user', username='test')
        self.repo = mommy.make_recipe('eyrie.repo', full_name='test/test', user=self.user)
        self.document = mommy.make_recipe('eyrie.document', repo=self.repo, path='/test/dir')

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
