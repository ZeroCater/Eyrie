import re


class PathProcessor(object):

    def __init__(self, raw_path, repo_name, is_directory=None):
        self.repo_name = repo_name
        self.is_directory = is_directory

        if is_directory:
            regex = re.match(
                "/?(?P<tmp>(?:tmp))?/?(?P<repo>(?:{}))?(?P<directory>(?:/?.*))/?".format(
                    repo_name), raw_path, re.IGNORECASE)
            self.directory = regex.group('directory')
            self.filename = None
        else:
            regex = re.match(
                "/?(?P<tmp>(?:tmp))?/?(?P<repo>(?:{}))?(?P<directory>(?:/?.*))/(?P<filename>(?:.+))".format(
                    repo_name), raw_path, re.IGNORECASE)
            self.directory = regex.group('directory') or '/'
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

    @property
    def git_style_path(self):
        return re.match('/(?P<path>(?:.*))', self.path_in_repo).group('path')
