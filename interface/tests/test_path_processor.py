from django.test import TestCase

from interface.path_processor import PathProcessor


class PathProcessTest(TestCase):

    def setUp(self):
        self.path_processor = PathProcessor('', 'ZeroCater/mp-users')

    def path_processor_test(self, path, directory, filename, is_directory=None):
        path_processor = PathProcessor(path, 'ZeroCater/mp-users', is_directory=is_directory)

        self.assertEqual(path_processor.directory, directory)
        self.assertEqual(path_processor.filename, filename)

    def test_file_path__w_tmp_w_leading_slash__root(self):
        path = '/tmp/ZeroCater/mp-users/README.md'

        self.path_processor_test(path, '/', 'README.md')

    def test_file_path__w_tmp_w_leading_slash__directory(self):
        path = '/tmp/ZeroCater/mp-users/tests/README.md'

        self.path_processor_test(path, '/tests', 'README.md')

    def test_file_path__w_tmp_wo_leading_slash__root(self):
        path = 'tmp/ZeroCater/mp-users/README.md'

        self.path_processor_test(path, '/', 'README.md')

    def test_file_path__w_tmp_wo_leading_slash__directory(self):
        path = 'tmp/ZeroCater/mp-users/tests/README.md'

        self.path_processor_test(path, '/tests', 'README.md')

    def test_file_path__wo_tmp_w_leading_slash__root(self):
        path = '/ZeroCater/mp-users/README.md'

        self.path_processor_test(path, '/', 'README.md')

    def test_file_path__wo_tmp_w_leading_slash__directory(self):
        path = '/ZeroCater/mp-users/tests/README.md'

        self.path_processor_test(path, '/tests', 'README.md')

    def test_file_path__wo_tmp_wo_leading_slash__root(self):
        path = 'ZeroCater/mp-users/README.md'

        self.path_processor_test(path, '/', 'README.md')

    def test_file_path__wo_tmp_wo_leading_slash__directory(self):
        path = 'ZeroCater/mp-users/tests/README.md'

        self.path_processor_test(path, '/tests', 'README.md')

    def test_directory_path__w_tmp_w_leading_slash__root(self):
        path = '/tmp/ZeroCater/mp-users/'

        self.path_processor_test(path, '/', None, is_directory=True)

    def test_directory_path__w_tmp_w_leading_slash__directory(self):
        path = '/tmp/ZeroCater/mp-users/tests'

        self.path_processor_test(path, '/tests', None, is_directory=True)

    def test_directory_path__w_tmp_wo_leading_slash__root(self):
        path = 'tmp/ZeroCater/mp-users'

        self.path_processor_test(path, '', None, is_directory=True)

    def test_directory_path__w_tmp_wo_leading_slash__directory(self):
        path = 'tmp/ZeroCater/mp-users/tests/'

        self.path_processor_test(path, '/tests/', None, is_directory=True)

    def test_directory_path__wo_tmp_w_leading_slash__root(self):
        path = '/ZeroCater/mp-users'

        self.path_processor_test(path, '', None, is_directory=True)

    def test_directory_path__wo_tmp_w_leading_slash__directory(self):
        path = '/ZeroCater/mp-users/tests/'

        self.path_processor_test(path, '/tests/', None, is_directory=True)

    def test_directory_path__wo_tmp_wo_leading_slash__root(self):
        path = 'ZeroCater/mp-users/'

        self.path_processor_test(path, '/', None, is_directory=True)

    def test_directory_path__wo_tmp_wo_leading_slash__directory(self):
        path = 'ZeroCater/mp-users/tests'

        self.path_processor_test(path, '/tests', None, is_directory=True)

    def test_repo_disk_path(self):
        path = '/tmp/ZeroCater/mp-users/tests/README.md'
        path_processor = PathProcessor(path, 'ZeroCater/mp-users')

        self.assertEqual(path_processor.repo_disk_path, 'tmp/ZeroCater/mp-users')

    def test_disk_path(self):
        path = '/tmp/ZeroCater/mp-users/tests/README.md'
        path_processor = PathProcessor(path, 'ZeroCater/mp-users')

        self.assertEqual(path_processor.disk_path, 'tmp/ZeroCater/mp-users/tests/README.md')

    def test_path_in_repo__file(self):
        path = '/tmp/ZeroCater/mp-users/tests/README.md'
        path_processor = PathProcessor(path, 'ZeroCater/mp-users')

        self.assertEqual(path_processor.path_in_repo, '/tests/README.md')

    def test_path_in_repo__directory(self):
        path = '/tmp/ZeroCater/mp-users/tests/'
        path_processor = PathProcessor(path, 'ZeroCater/mp-users', is_directory=True)

        self.assertEqual(path_processor.path_in_repo, '/tests/')

    def test_full_path(self):
        path = '/tmp/ZeroCater/mp-users/tests/README.md'
        path_processor = PathProcessor(path, 'ZeroCater/mp-users', is_directory=True)

        self.assertEqual(path_processor.full_path, 'ZeroCater/mp-users/tests/README.md')

    def test_git_style_path(self):
        path = '/tmp/ZeroCater/mp-users/tests/README.md'
        path_processor = PathProcessor(path, 'ZeroCater/mp-users', is_directory=True)

        self.assertEqual(path_processor.git_style_path, 'tests/README.md')
