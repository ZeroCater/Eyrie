import re


class PathProcessor(object):

    def __init__(self, repo_name, raw_path=None, is_directory=None, directory=None, filename=None):
        self.repo_name = repo_name
        self.is_directory = is_directory
        self.raw_path = raw_path
        self.directory = directory or None
        self.filename = filename or None

        if raw_path:
            self.process()

    def process(self):
        if self.is_directory:
            regex = re.match(
                "/?(?P<tmp>(?:tmp))?/?(?P<repo>(?:{}))?(?P<directory>(?:/?.*))/?".format(
                    self.repo_name), self.raw_path, re.IGNORECASE)
            if regex:
                self.directory = regex.group('directory')
        else:
            regex = re.match(
                "/?(?P<tmp>(?:tmp))?/?(?P<repo>(?:{}))?(?P<directory>(?:/?.*))/(?P<filename>(?:.+))".format(
                    self.repo_name), self.raw_path, re.IGNORECASE)

            if regex:
                self.directory = regex.group('directory') if regex.group('directory') else '/'
                self.filename = regex.group('filename')

    @property
    def repo_disk_path(self):
        return "tmp/{}".format(self.repo_name)

    @property
    def disk_path(self):
        return "tmp/{}".format(self.full_path)

    @property
    def path_in_repo(self):
        if not self.filename:
            return "{}".format(self.directory)

        return "{}/{}".format(self.directory, self.filename)

    @property
    def full_path(self):
        if not self.filename:
            return "{}{}".format(self.repo_name, self.directory)

        return "{}{}/{}".format(self.repo_name, self.directory, self.filename)

    # Github style paths do not start with a slash
    @property
    def git_style_path(self):
        return re.match('/(?P<path>(?:.*))', self.path_in_repo).group('path')
