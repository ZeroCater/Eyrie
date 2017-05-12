from interface.utils import get_github
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db import models

from documents.models import Document


class Search(object):

    def __init__(self, user, query):
        self.user = user
        self.query = query

        if not self.user.is_authenticated():
            raise Exception('User should be authenticated')

    def perform(self):
        vector = SearchVector('body')
        query = SearchQuery(self.query + ':*')

        documents = self.get_documents()

        docs = documents.annotate(
            rank=SearchRank(vector, query),
            has_title=models.Case(
                models.When(filename__icontains=self.query, then=1),
                default=0,
                output_field=models.IntegerField()
            )
        ).exclude(rank=0).order_by('-has_title', '-rank')

        processed_docs = self.process_docs(docs)
        return processed_docs

    def get_user_github_repos(self):
        github = get_github(self.user)
        github_repos = github.get_user().get_repos()
        return [repo for repo in github_repos]

    def get_repo_names(self):
        github_repos = self.get_user_github_repos()
        repo_names = [repo.full_name for repo in github_repos]
        return repo_names

    def get_documents(self):
        repo_names = self.get_repo_names()
        documents = Document.objects.filter(repo__full_name__in=repo_names).prefetch_related('repo')
        return documents

    def process_docs(self, docs):
        res = {}
        for doc in docs:
            filename = doc.filename
            if self.query in filename:
                filename = filename.replace(self.query, '<strong>{}</strong>'.format(self.query))
            doc.search_path = '{}/{}'.format(doc.path, filename)

            repo_name = doc.repo.full_name
            if not res.get(repo_name):
                res[repo_name] = []

            res[repo_name].append(doc)

        return res
