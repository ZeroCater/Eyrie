from django.test import TestCase

from model_mommy import mommy

from documents.models import Document
from documents.tasks.wiki_processor import delete_removed_files

from interface.path_processor import PathProcessor


class DeleteRemovedFileTest(TestCase):

    def setUp(self):
        self.repo = mommy.make_recipe('eyrie.repo')
        self.document = mommy.make_recipe('eyrie.document', repo=self.repo)

    def test_should_remove_document_passed_in_removed(self):
        document_id = self.document.id

        self.assertIsNotNone(Document.objects.filter(id=document_id).all())

        path_processor = PathProcessor(
            self.repo.full_name, filename=self.document.filename, directory=self.document.path)

        file_change_data = {
            'removed': [path_processor.git_style_path]
        }

        delete_removed_files(self.repo.id, file_change_data)

        self.assertIsNone(Document.objects.filter(id=document_id).first())

    def test_should_remove_document_passed_in_removed__not_in_file_change(self):
        document_id = self.document.id

        self.assertIsNotNone(Document.objects.filter(id=document_id).all())

        file_change_data = {
            'removed': ['/test/sample']
        }

        delete_removed_files(self.repo.id, file_change_data)

        self.assertIsNotNone(Document.objects.filter(id=document_id).first())

    def test_should_remove_document_passed_in_removed__different_repo(self):
        document_id = self.document.id

        self.assertIsNotNone(Document.objects.filter(id=document_id).all())

        path_processor = PathProcessor(
            self.repo.full_name, filename=self.document.filename, directory=self.document.path)

        file_change_data = {
            'removed': [path_processor.git_style_path]
        }

        delete_removed_files(123, file_change_data)

        self.assertIsNotNone(Document.objects.filter(id=document_id).first())
