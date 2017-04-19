from model_mommy.recipe import Recipe, foreign_key

from documents.models import Document
from interface.models import Repo

document = Recipe(Document)
repo = Recipe(Repo)
