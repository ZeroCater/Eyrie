from unittest import mock

from django.test import TestCase
from model_mommy import mommy

from documents.search import Search


class SearchTestCase(TestCase):

    def setUp(self):
        self.test_repo_name = 'test/test'
        self.user = mommy.make_recipe('eyrie.user', username='test')

        self.repo = mommy.make_recipe('eyrie.repo', full_name=self.test_repo_name, user=self.user)

        self.doc = mommy.make_recipe('eyrie.document', repo=self.repo, path='/test/dir')

        self.doc1 = mommy.make_recipe('eyrie.document', repo=self.repo, path='/test/dir',
                                      filename='test.md', body='This is a test')
        self.doc2 = mommy.make_recipe('eyrie.document', repo=self.repo, path='/test/dir',
                                      filename='fail.md', body='This is a fail')
        self.doc3 = mommy.make_recipe('eyrie.document', repo=self.repo, path='/test/dir',
                                      filename='different.md', body='This is also a test')

        self.user_2 = mommy.make_recipe('eyrie.user', username='test_2')
        self.repo_2 = mommy.make_recipe('eyrie.repo', full_name='test/test_2', user=self.user_2)
        self.doc_u2 = mommy.make_recipe('eyrie.document', repo=self.repo_2, path='/test/dir')

    @mock.patch('documents.search.Search.get_repo_names', return_value=['test/test'])
    def test_search__return_correct_results(self, mock_get_repo_names):
        search = Search(self.user, 'test')
        search_results = search.perform()

        self.assertEqual(len(search_results.keys()), 1)

        self.assertEqual(len(search_results[self.test_repo_name]), 2)

        search_results = search_results[self.test_repo_name]

        self.assertNotIn(self.doc, search_results, 'Search results included fail Document')
        self.assertNotIn(self.doc2, search_results, 'Search results included fail Document')
        self.assertNotIn(self.doc_u2, search_results, 'Search results included fail Document')
        # Check filename sorted first
        self.assertEqual(search_results[0], self.doc1, 'Filename matches should be sorted first')
        self.assertEqual(search_results[1], self.doc3, 'Filename matches should be sorted first')
