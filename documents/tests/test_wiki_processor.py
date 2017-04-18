from django.test import TestCase

from model_mommy import mommy

from documents.models import Document
from documents.tasks.wiki_processor import delete_removed_files


class DeleteRemovedFileTest(TestCase):

    def setUp(self):
        self.repo = mommy.make_recipe('eyrie.repo')
        self.document = mommy.make_recipe('eyrie.document', repo=self.repo)

    def should_remove_document_passed_in_removed(self):
        document_id = self.document.id

        file_change_data = {
            'removed':}
